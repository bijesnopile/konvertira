import pytest

from backend.services.downloads import DownloadError, is_allowed_download_host, validate_download_url


@pytest.mark.parametrize(
    "host",
    ["openai.com", "files.openai.com", "oaiusercontent.com", "files.oaiusercontent.com"],
)
def test_openai_download_hosts_are_allowed(host: str) -> None:
    assert is_allowed_download_host(host)


@pytest.mark.parametrize(
    "url",
    [
        "http://files.oaiusercontent.com/file",
        "https://oaiusercontent.com.evil.example/file",
        "https://127.0.0.1/file",
        "https://user:secret@files.oaiusercontent.com/file",
        "https://files.oaiusercontent.com:8443/file",
    ],
)
def test_disallowed_download_urls(url: str) -> None:
    with pytest.raises(DownloadError):
        validate_download_url(url)
