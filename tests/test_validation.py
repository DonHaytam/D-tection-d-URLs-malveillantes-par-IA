"""Tests for URL validation (passive, no network access)."""
import sys
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")

from src.data.validation import is_valid_url, normalize_url, extract_components


def test_valid_https():
    assert is_valid_url("https://example.com/path?q=1") is True


def test_valid_no_scheme():
    assert is_valid_url("example.com") is True


def test_invalid_empty():
    assert is_valid_url("") is False
    assert is_valid_url(None) is False


def test_invalid_with_newline():
    assert is_valid_url("https://example.com\n.evil") is False


def test_normalize_adds_scheme():
    assert normalize_url("example.com") == "https://example.com"


def test_normalize_lowercases_host():
    assert normalize_url("https://Example.COM/Path") == "https://example.com/Path"


def test_extract_components():
    c = extract_components("https://example.com:8080/a/b?q=1#frag")
    assert c["scheme"] == "https"
    assert c["host"] == "example.com"
    assert c["port"] == 8080
    assert c["path"] == "/a/b"
    assert c["query"] == "q=1"
    assert c["fragment"] == "frag"


if __name__ == "__main__":
    test_valid_https(); test_valid_no_scheme(); test_invalid_empty()
    test_invalid_with_newline(); test_normalize_adds_scheme()
    test_normalize_lowercases_host(); test_extract_components()
    print("All validation tests passed.")
