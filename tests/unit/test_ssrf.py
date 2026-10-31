import pytest
from backend.core.ssrf import validate_url_ssrf_safe, is_ip_forbidden, SSRFSecurityError


def test_ip_forbidden_ranges():
    # Loopback
    assert is_ip_forbidden("127.0.0.1") is True
    assert is_ip_forbidden("127.0.0.2") is True
    # Private RFC 1918
    assert is_ip_forbidden("10.0.0.1") is True
    assert is_ip_forbidden("192.168.1.100") is True
    assert is_ip_forbidden("172.16.5.4") is True
    assert is_ip_forbidden("172.31.255.255") is True
    # Cloud Metadata
    assert is_ip_forbidden("169.254.169.254") is True
    # Broadcast / Unspecified
    assert is_ip_forbidden("0.0.0.0") is True
    assert is_ip_forbidden("255.255.255.255") is True
    # Public IPs should not be forbidden
    assert is_ip_forbidden("8.8.8.8") is False
    assert is_ip_forbidden("1.1.1.1") is False


def test_ssrf_forbidden_schemes():
    with pytest.raises(SSRFSecurityError, match="Prohibited URL scheme"):
        validate_url_ssrf_safe("file:///etc/passwd")

    with pytest.raises(SSRFSecurityError, match="Prohibited URL scheme"):
        validate_url_ssrf_safe("gopher://127.0.0.1:6379/_")

    with pytest.raises(SSRFSecurityError, match="Prohibited URL scheme"):
        validate_url_ssrf_safe("ftp://ftp.example.com")


def test_ssrf_credentials_rejected():
    with pytest.raises(SSRFSecurityError, match="Embedded credentials"):
        validate_url_ssrf_safe("https://admin:secret@github.com")


def test_ssrf_localhost_shortcuts():
    with pytest.raises(SSRFSecurityError):
        validate_url_ssrf_safe("http://localhost:8080/metrics")

    with pytest.raises(SSRFSecurityError):
        validate_url_ssrf_safe("http://127.0.0.1:5432")

    with pytest.raises(SSRFSecurityError):
        validate_url_ssrf_safe("http://metadata.google.internal")


def test_ssrf_valid_public_url():
    # Resolves to real public IPs
    safe_url = validate_url_ssrf_safe("https://github.com")
    assert safe_url == "https://github.com"
