from backend.utils.filenames import clean_filename, cleaned_output_filename, converted_output_filename


def test_filename_cleaning_removes_paths_and_unsafe_characters() -> None:
    assert clean_filename(r"..\private/folder/photo?.jpg") == "photo_.jpg"


def test_filename_cleaning_uses_fallback() -> None:
    assert clean_filename("  ...  ") == "image"
    assert converted_output_filename(None, "png") == "image.png"


def test_cleaned_filename_uses_verified_output_format() -> None:
    assert cleaned_output_filename("photo.jpeg", "JPEG") == "clean_photo.jpg"
    assert cleaned_output_filename("misleading.exe", "PNG") == "clean_misleading.png"
