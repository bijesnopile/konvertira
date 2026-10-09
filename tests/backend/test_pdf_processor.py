import io
import zipfile

import pytest
from PIL import Image
from pypdf import PdfReader, PdfWriter

from backend.models.files import FileProcessingError
from backend.processors.pdf import (
    delete_pdf_pages,
    extract_pdf_pages,
    images_to_pdf,
    inspect_pdf_metadata,
    merge_pdfs,
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
