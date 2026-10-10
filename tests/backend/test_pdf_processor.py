import io
import zipfile
from dataclasses import replace

import pytest
from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject, NumberObject
import backend.processors.pdf as processor

from backend.models.files import FileProcessingError
from backend.processors.pdf import (
    delete_pdf_pages,
    extract_pdf_pages,
    images_to_pdf,
    inspect_pdf_metadata,
    merge_pdfs,
    optimize_pdf,
    parse_page_selection,
    pdf_to_images,
    remove_pdf_metadata,
    reorder_pdf_pages,
    select_pdf_pages,
    split_pdf_pages,
)


def make_pdf(widths: tuple[int, ...] = (100,), metadata: dict[str, str] | None = None) -> bytes:
    writer = PdfWriter()
    for width in widths:
        writer.add_blank_page(width=width, height=100)
    if metadata:
        writer.add_metadata(metadata)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def test_merge_preserves_file_and_page_order() -> None:
    result = merge_pdfs([make_pdf((100, 200)), make_pdf((300,))])
    reader = PdfReader(io.BytesIO(result.content))
    assert [int(page.mediabox.width) for page in reader.pages] == [100, 200, 300]


def test_merge_limits_and_corrupt_input() -> None:
    with pytest.raises(FileProcessingError, match="requires"):
        merge_pdfs([make_pdf()])
    with pytest.raises(FileProcessingError, match="valid supported PDF"):
        merge_pdfs([make_pdf(), b"not a pdf"])


def test_encrypted_pdf_is_rejected() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("secret")
    output = io.BytesIO()
    writer.write(output)
    with pytest.raises(FileProcessingError, match="Encrypted PDFs"):
        inspect_pdf_metadata(output.getvalue())


def test_page_selection_extract_reorder_and_delete() -> None:
    source = make_pdf((100, 200, 300))
    assert parse_page_selection("1-2,3", 3) == [0, 1, 2]
    extracted = extract_pdf_pages(source, "3,1")
    assert [int(page.mediabox.width) for page in PdfReader(io.BytesIO(extracted.content)).pages] == [300, 100]
    reordered = select_pdf_pages(source, [2, 0, 1])
    assert [int(page.mediabox.width) for page in PdfReader(io.BytesIO(reordered.content)).pages] == [300, 100, 200]
    deleted = delete_pdf_pages(source, "2")
    assert [int(page.mediabox.width) for page in PdfReader(io.BytesIO(deleted.content)).pages] == [100, 300]
    with pytest.raises(FileProcessingError):
        parse_page_selection("0,99", 3)
    assert reorder_pdf_pages(source, "3,1,2").page_count == 3
    with pytest.raises(FileProcessingError, match="every page exactly once"):
        reorder_pdf_pages(source, "1,1,2")


def test_split_zip_uses_generated_safe_names() -> None:
    result = split_pdf_pages(make_pdf((100, 200)))
    with zipfile.ZipFile(io.BytesIO(result.content)) as archive:
        assert archive.namelist() == ["page-0001.pdf", "page-0002.pdf"]
        assert all("/" not in name and "\\" not in name for name in archive.namelist())


def test_images_to_pdf_and_pdf_to_bounded_images() -> None:
    image = Image.new("RGB", (8, 6), "red")
    png = io.BytesIO()
    image.save(png, format="PNG")
    pdf = images_to_pdf([png.getvalue(), png.getvalue()])
    assert len(PdfReader(io.BytesIO(pdf.content)).pages) == 2
    rendered = pdf_to_images(pdf.content, output_format="png", dpi=72, selection="1")
    with zipfile.ZipFile(io.BytesIO(rendered.content)) as archive:
        assert archive.namelist() == ["page-0001.png"]
    with pytest.raises(FileProcessingError, match="DPI"):
        pdf_to_images(pdf.content, dpi=9999)


def test_metadata_inspection_and_removal() -> None:
    source = make_pdf(metadata={"/Title": "Private title", "/Author": "Person"})
    metadata = inspect_pdf_metadata(source)
    assert metadata["title"] == "Private title"
    assert metadata["author"] == "Person"
    cleaned = remove_pdf_metadata(source)
    cleaned_metadata = PdfReader(io.BytesIO(cleaned.content)).metadata or {}
    assert not cleaned_metadata.get("/Title")
    assert not cleaned_metadata.get("/Author")


def colored_pdf() -> bytes:
    """Real vector content, empty transparent half, three distinguishable pages."""
    writer = PdfWriter()
    for width, color in zip((100, 200, 300), ("1 0 0", "0 1 0", "0 0 1")):
        page = writer.add_blank_page(width=width, height=60)
        font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
        page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
        stream = DecodedStreamObject()
        stream.set_data(f"q {color} rg 0 0 {width / 2} 60 re f Q BT /F1 8 Tf 0 0 0 rg 5 10 Td (PDF page {width // 100}) Tj ET".encode())
        page[NameObject("/Contents")] = writer._add_object(stream)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


@pytest.mark.parametrize("output_format,extension,mode", [("png", "png", "RGBA"), ("jpeg", "jpg", "RGB"), ("jpg", "jpg", "RGB"), ("webp", "webp", "RGBA")])
@pytest.mark.parametrize("dpi", [36, 72, 144])
def test_real_render_formats_dpi_order_and_alpha(output_format, extension, mode, dpi) -> None:
    source = colored_pdf()
    result = pdf_to_images(source, output_format=output_format, dpi=dpi, selection="3,1-2,3")
    assert result.page_count == 3
    with zipfile.ZipFile(io.BytesIO(result.content)) as archive:
        assert archive.namelist() == [f"page-{i:04d}.{extension}" for i in range(1, 4)]
        for name, width, channel in zip(archive.namelist(), (300, 100, 200), (2, 0, 1)):
            with Image.open(io.BytesIO(archive.read(name))) as image:
                assert image.size == (int(width * dpi / 72), int(60 * dpi / 72))
                assert image.mode == mode
                pixel = image.getpixel((image.width // 4, image.height // 2))
                assert pixel[channel] > 230
                assert all(pixel[c] < 25 for c in range(3) if c != channel)
                empty = image.getpixel((image.width * 3 // 4, image.height // 2))
                if mode == "RGBA":
                    assert pixel[3] == 255 and empty[3] == 0
                else:
                    assert all(c > 245 for c in empty)
    assert source == colored_pdf()  # Input was not changed.


def test_crop_rotation_and_user_unit_dimensions() -> None:
    writer = PdfWriter()
    page = writer.add_blank_page(width=100, height=60)
    page.cropbox.upper_right = (80, 40)
    page.rotate(90)
    page[NameObject("/UserUnit")] = NumberObject(2)
    output = io.BytesIO()
    writer.write(output)
    result = pdf_to_images(output.getvalue(), dpi=72)
    with zipfile.ZipFile(io.BytesIO(result.content)) as archive:
        with Image.open(io.BytesIO(archive.read("page-0001.png"))) as image:
            assert image.size == (80, 160)


@pytest.mark.parametrize("selection", ["0", "4", "2-1", "one", "1,,2"])
def test_render_invalid_selection(selection) -> None:
    with pytest.raises(FileProcessingError) as error:
        pdf_to_images(colored_pdf(), selection=selection)
    assert error.value.status_code == 422


def test_render_encrypted_corrupt_and_resource_limits(monkeypatch) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("password")
    encrypted = io.BytesIO()
    writer.write(encrypted)
    for source in (encrypted.getvalue(), b"%PDF-1.7\ncorrupt", b""):
        with pytest.raises(FileProcessingError):
            pdf_to_images(source)
    source = colored_pdf()
    for field, value, message in [("max_pdf_size", 10, "size limit"), ("max_pdf_pages", 2, "page-count limit"), ("max_pdf_generated_pixels", 100, "pixel limit"), ("max_pdf_output_size", 64, "output size limit")]:
        with monkeypatch.context() as patch:
            patch.setattr(processor, "settings", replace(processor.settings, **{field: value}))
            with pytest.raises(FileProcessingError, match=message) as error:
                pdf_to_images(source)
            assert error.value.status_code == 413
    assert pdf_to_images(source).page_count == 3


def test_pixel_preflight_happens_before_native_render(monkeypatch) -> None:
    def forbidden_render(*args, **kwargs):
        pytest.fail("Pixel-rejected PDFs must never allocate a bitmap")
    monkeypatch.setattr(processor.pdfium.PdfPage, "render", forbidden_render)
    monkeypatch.setattr(processor, "settings", replace(processor.settings, max_pdf_generated_pixels=100))
    with pytest.raises(FileProcessingError, match="pixel limit"):
        pdf_to_images(colored_pdf())


def test_native_resources_close_after_encoder_failure(monkeypatch) -> None:
    objects = []
    original_document = processor.pdfium.PdfDocument
    original_render = processor.pdfium.PdfPage.render

    def tracked_document(*args, **kwargs):
        document = original_document(*args, **kwargs)
        objects.append(document)
        return document

    def tracked_render(page, *args, **kwargs):
        objects.append(page)
        bitmap = original_render(page, *args, **kwargs)
        objects.append(bitmap)
        return bitmap

    def failed_save(*args, **kwargs):
        raise OSError("encoder failed")

    with monkeypatch.context() as patch:
        patch.setattr(processor.pdfium, "PdfDocument", tracked_document)
        patch.setattr(processor.pdfium.PdfPage, "render", tracked_render)
        patch.setattr(Image.Image, "save", failed_save)
        with pytest.raises(FileProcessingError, match="could not be rendered"):
            pdf_to_images(colored_pdf())
    assert objects and all(not obj.raw for obj in objects)
    assert pdf_to_images(colored_pdf()).page_count == 3  # Gate released too.


def test_pdfium_gate_rejects_concurrent_rendering() -> None:
    assert processor._pdfium_lock.acquire(blocking=False)
    try:
        with pytest.raises(FileProcessingError, match="busy") as error:
            pdf_to_images(colored_pdf())
        assert error.value.status_code == 429
    finally:
        processor._pdfium_lock.release()


def test_optimization_preserves_structure_metadata_and_vector_content() -> None:
    source = colored_pdf()
    result = optimize_pdf(source)
    before, after = PdfReader(io.BytesIO(source)), PdfReader(io.BytesIO(result.content))
    assert result.page_count == 3
    assert [page.get_contents().get_data() for page in after.pages] == [page.get_contents().get_data() for page in before.pages]
    assert [page.mediabox for page in after.pages] == [page.mediabox for page in before.pages]
