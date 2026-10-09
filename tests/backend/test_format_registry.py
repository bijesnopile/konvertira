import pytest

from backend.errors import normalize_processing_error
from backend.formats import (
    FormatCategory,
    conversion_capability,
    declared_format,
    format_from_extension,
    format_from_mime,
    implemented_formats,
    normalize_format,
    require_conversion,
)
from backend.models.files import FileProcessingError, ProcessingErrorCode
from backend.utils.filenames import converted_output_filename


def test_format_normalization_and_aliases() -> None:
    assert normalize_format("JPG").id == "jpeg"
    assert normalize_format(".jpeg").id == "jpeg"
    assert normalize_format("image/pjpeg").id == "jpeg"
    assert format_from_extension("PNG").preferred_mime_type == "image/png"
    assert format_from_mime("image/x-png; charset=binary").id == "png"
    assert normalize_format("mp4") is None


def test_implemented_formats_are_advertised_by_mode() -> None:
    assert normalize_format("docx").implemented is True
    server_images = implemented_formats(category=FormatCategory.IMAGE, mode="server")
    assert {definition.id for definition in server_images} == {
        "jpeg", "png", "webp", "heic", "avif", "gif"
    }


def test_declared_format_is_distinct_from_verified_content() -> None:
    declared = declared_format("photo.jpg", "image/png")
    assert declared.filename_format.id == "jpeg"
    assert declared.mime_format.id == "png"
    assert declared.is_consistent is False
    assert declared.candidate is None


def test_conversion_capabilities_are_explicit_by_execution_mode() -> None:
    edge = conversion_capability("jpeg", "png", "local")
    assert edge is not None
    assert edge.source == "jpeg"
    assert edge.target == "png"
    assert conversion_capability("docx", "pdf", "server") is not None
    assert conversion_capability("docx", "pdf", "local") is None


def test_operation_execution_metadata_does_not_imply_a_server_fallback() -> None:
    jpeg = normalize_format("jpeg")
    assert jpeg.modes_for("removeMetadata") == {"local", "server"}
    assert jpeg.modes_for("inspectMetadata") == {"server"}
    assert jpeg.modes_for("merge") == set()


def test_unsupported_conversion_has_stable_error_code() -> None:
    with pytest.raises(FileProcessingError) as error:
        require_conversion("txt", "html", "server")
    assert error.value.code == ProcessingErrorCode.UNSUPPORTED_CONVERSION
    assert error.value.status_code == 422


def test_safe_output_filename_uses_canonical_extension() -> None:
    assert converted_output_filename(r"..\private/photo?.jpeg", "jpeg") == "photo_.jpg"
    with pytest.raises(ValueError, match="Unsupported output extension"):
        converted_output_filename("video.mp4", "mp4")


def test_error_normalization_hides_unexpected_details() -> None:
    normalized = normalize_processing_error(RuntimeError(r"secret C:\temp\input.bin"))
    assert normalized.code == ProcessingErrorCode.CONVERSION_FAILED
    assert normalized.status_code == 500
    assert "secret" not in normalized.message

    expected = normalize_processing_error(
        FileProcessingError(
            "That conversion is unavailable.",
            422,
            ProcessingErrorCode.UNSUPPORTED_CONVERSION,
        )
    )
    assert expected.code == ProcessingErrorCode.UNSUPPORTED_CONVERSION
    assert expected.message == "That conversion is unavailable."
