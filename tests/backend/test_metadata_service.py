import io
import zipfile

import pytest
from docx import Document

from backend.models.files import FileProcessingError
from backend.services.metadata import inspect_file_metadata, remove_file_metadata


def docx_with_metadata() -> bytes:
    document = Document()
    document.add_paragraph("Visible content")
    document.core_properties.author = "Person <script>alert(1)</script>"
    document.core_properties.title = "Private title"
    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


def test_ooxml_metadata_inspection_categories_and_untrusted_text() -> None:
    result = inspect_file_metadata(docx_with_metadata(), "docx")
    author = next(field for field in result.fields if field.label.lower() == "creator")
    assert author.sensitive is True
    assert author.category == "Author/identity"
    assert "<script>" in author.value


def test_ooxml_metadata_removal_and_post_verification() -> None:
    result = remove_file_metadata(docx_with_metadata(), "docx")
    assert result.removed_fields >= 2
    after = inspect_file_metadata(result.content, "docx")
    assert not any(field.value in {"Private title", "Person <script>alert(1)</script>"} for field in after.fields)


def test_archive_traversal_entry_is_rejected_without_extraction() -> None:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("../escape.xml", "bad")
        archive.writestr("docProps/core.xml", "<root />")
    with pytest.raises(FileProcessingError, match="unsafe entry"):
        inspect_file_metadata(output.getvalue(), "docx")


def test_large_metadata_value_is_bounded() -> None:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        archive.writestr("word/document.xml", "<document />")
        archive.writestr("docProps/core.xml", f"<root><title>{'x' * 20000}</title></root>")
    result = inspect_file_metadata(output.getvalue(), "docx")
    assert len(result.fields[0].value) == 10000


def test_renamed_zip_is_not_accepted_as_ooxml() -> None:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("docProps/core.xml", "<root><author>Person</author></root>")
    with pytest.raises(FileProcessingError, match="valid DOCX"):
        inspect_file_metadata(output.getvalue(), "docx")
