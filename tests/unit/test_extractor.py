from backend.extraction.extractor import ContactExtractor
from backend.models import SourceCategory


def test_contact_extractor_basic():
    sample_text = """
    # Mesh Network Orchestrator
    Welcome to the repository.
    Lead Maintainer: Sarah Jenkins <sarah.jenkins@mesh-project.org>
    For security advisories: <security@mesh-project.org>
    For general questions check the docs.
    """
    contacts = ContactExtractor.extract_from_text(
        text=sample_text,
        source_url="https://github.com/mesh-org/mesh/blob/main/README.md",
        source_category=SourceCategory.GITHUB_README
    )

    assert len(contacts) >= 2
    emails = [c.email for c in contacts]
    assert "sarah.jenkins@mesh-project.org" in emails
    assert "security@mesh-project.org" in emails

    sarah = next(c for c in contacts if c.email == "sarah.jenkins@mesh-project.org")
    assert sarah.full_name == "Sarah Jenkins"
    assert sarah.relevance_score >= 0.85
    assert "Lead Maintainer" in sarah.evidence_text
    assert sarah.source_category == SourceCategory.GITHUB_README


def test_contact_extractor_excludes_noise_and_placeholders():
    noisy_text = """
    Do not email user@example.com or fake@domain.com or test@placeholder.com.
    Also ignore bot notifications from noreply@github.com or dependabot@github.com.
    Bad image pseudo email: image.png@2x.jpg
    Real author: Dave Miller <dave.miller@realproject.io>
    """
    contacts = ContactExtractor.extract_from_text(
        text=noisy_text,
        source_url="https://github.com/real/repo/README.md"
    )

    emails = [c.email for c in contacts]
    assert "user@example.com" not in emails
    assert "fake@domain.com" not in emails
    assert "noreply@github.com" not in emails
    assert "dependabot@github.com" not in emails
    assert "dave.miller@realproject.io" in emails


def test_relevance_scoring():
    text_lead = "Project Architect & Lead Maintainer: Jordan <jordan@distributed.org>"
    text_generic = "Send questions to team@distributed.org"

    c_lead = ContactExtractor.extract_from_text(text_lead, "https://example.org")[0]
    c_generic = ContactExtractor.extract_from_text(text_generic, "https://example.org")[0]

    assert c_lead.relevance_score > c_generic.relevance_score
    assert c_lead.relevance_score >= 0.85
