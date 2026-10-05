from backend.utils.filenames import clean_filename, converted_output_filename


def test_filename_cleaning_removes_paths_and_unsafe_characters() -> None:
    assert clean_filename(r"..\private/folder/photo?.jpg") == "photo_.jpg"


def test_filename_cleaning_uses_fallback() -> None:
    assert clean_filename("  ...  ") == "image"
    assert converted_output_filename(None, "png") == "image.png"
