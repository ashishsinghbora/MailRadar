from backend.verification.dns_verifier import DNSVerifier
from backend.models import VerificationStatus


def test_verifier_invalid_syntax():
    res1 = DNSVerifier.verify_email("not-an-email")
    assert res1.status == VerificationStatus.INVALID_SYNTAX

    res2 = DNSVerifier.verify_email("@missinguser.com")
    assert res2.status == VerificationStatus.INVALID_SYNTAX

    res3 = DNSVerifier.verify_email("")
    assert res3.status == VerificationStatus.INVALID_SYNTAX


def test_verifier_disposable_domain():
    res = DNSVerifier.verify_email("throwaway@mailinator.com")
    assert res.status == VerificationStatus.DISPOSABLE
    assert "disposable" in res.details.lower()


def test_verifier_valid_email_fallback():
    res = DNSVerifier.verify_email("contact@python.org", allow_mock=True)
    assert res.status == VerificationStatus.VALID
    assert len(res.mx_records) > 0
