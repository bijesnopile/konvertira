"""Offline CPU U²-NetP segmentation with a reusable, bounded session."""

import hashlib
import io
import threading
from enum import StrEnum

import numpy as np
from PIL import Image, ImageChops

from backend.formats import format_from_processor_name
from backend.models.files import FileProcessingError, ProcessedFile
from backend.processors.image import _open_image, _oriented_copy
from config import settings


class BackgroundOutputFormat(StrEnum):
    PNG = "png"
    WEBP = "webp"


# Published rembg U²-NetP artifact, fixed model, never selected by an API caller.
MODEL_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx"
MODEL_SHA256 = "309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8"
WARNING = "Automatic segmentation may need refinement around hair, fur, shadows, glass, semi-transparent objects, or similar foreground/background colors. It does not guarantee anonymity or remove visible sensitive information."
_session = None
_session_lock = threading.Lock()
_inference_lock = threading.Lock()


def verify_model(path):
    if not path.is_file() or path.stat().st_size > 10 * 1024 * 1024:
        raise FileProcessingError("Background removal model is unavailable. Ask the operator to prepare the model.", 503)
    with path.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    if digest != MODEL_SHA256:
        raise FileProcessingError("Background removal model failed integrity verification.", 503)


def _get_session():
    global _session
    with _session_lock:
        if _session is None:
            path = settings.background_model_dir / "u2netp.onnx"
            verify_model(path)
            import onnxruntime as ort
            options = ort.SessionOptions()
            options.intra_op_num_threads = settings.background_threads
            options.inter_op_num_threads = 1
            options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            try:
                _session = ort.InferenceSession(str(path), sess_options=options, providers=["CPUExecutionProvider"])
            except Exception as exc:
                raise FileProcessingError("Background removal model could not be initialized.", 503) from exc
        return _session


def _segment(image: Image.Image) -> Image.Image:
    # Reject rather than queue another inference and its decoded image buffers.
    if not _inference_lock.acquire(blocking=False):
        raise FileProcessingError("Background removal is busy. Please try again shortly.", 429)
    try:
        session = _get_session()
        with image.convert("RGB") as rgb, rgb.resize((320, 320), Image.Resampling.LANCZOS) as small:
            tensor = np.asarray(small, dtype=np.float32) / 255.0
        tensor /= max(float(tensor.max()), 1e-6)
        tensor = (tensor - np.array([0.485, 0.456, 0.406], dtype=np.float32)) / np.array([0.229, 0.224, 0.225], dtype=np.float32)
        tensor = np.ascontiguousarray(tensor.transpose(2, 0, 1)[None])
        prediction = session.run(None, {session.get_inputs()[0].name: tensor})[0][0, 0]
        if prediction.shape != (320, 320) or not np.isfinite(prediction).all():
            raise FileProcessingError("Background segmentation failed.", 500)
        low, high = float(prediction.min()), float(prediction.max())
        mask = np.clip((prediction - low) / (high - low), 0, 1) if high > low else np.clip(prediction, 0, 1)
        with Image.fromarray((mask * 255).astype(np.uint8)) as small_mask:
            return small_mask.resize(image.size, Image.Resampling.LANCZOS)
    except FileProcessingError:
        raise
    except Exception as exc:
        raise FileProcessingError("Background segmentation failed.", 500) from exc
    finally:
        _inference_lock.release()


def remove_image_background(content: bytes, *, output_format: BackgroundOutputFormat = BackgroundOutputFormat.PNG, expected_format: str | None = None) -> ProcessedFile:
    try:
        output_format = BackgroundOutputFormat(output_format)
    except ValueError as exc:
        raise FileProcessingError("Background removal output must be PNG or WebP.", 422) from exc
    with _open_image(content, settings.max_image_size, min(settings.max_pixels, settings.background_max_pixels)) as source:
        definition = format_from_processor_name(source.format)
        if definition is None or "server" not in definition.modes_for("removeBackground"):
            raise FileProcessingError("Background removal is not supported for this format.", 415)
        if expected_format is not None and definition.id != expected_format:
            raise FileProcessingError("The image content does not match its declared format.", 415)
        with _oriented_copy(source) as oriented, oriented.convert("RGBA") as rgba:
            # Fresh pixels without metadata or a megapixel-sized Python tuple list.
            clean = Image.frombytes("RGBA", rgba.size, rgba.tobytes())
    with clean:
        with _segment(clean) as mask, clean.getchannel("A") as original_alpha, ImageChops.multiply(mask, original_alpha) as alpha:
            clean.putalpha(alpha)
        output = io.BytesIO()
        try:
            if output_format == BackgroundOutputFormat.PNG:
                clean.save(output, format="PNG", optimize=True)
            else:
                clean.save(output, format="WEBP", lossless=True, method=4)
        except OSError as exc:
            raise FileProcessingError("The transparent image could not be generated.", 500) from exc
        result = output.getvalue()
        if len(result) > settings.max_image_output_size:
            raise FileProcessingError("The generated image exceeds the output size limit.", 413)
        return ProcessedFile(result, output_format.value.upper(), clean.width, clean.height)
