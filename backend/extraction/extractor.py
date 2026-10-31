import re
from typing import List, Optional, Set
from pydantic import BaseModel
from backend.models import SourceCategory


class ExtractedContact(BaseModel):
    email: str
    full_name: Optional[str] = None
    role_title: Optional[str] = None
    evidence_text: str
    relevance_score: float
    source_url: str
    source_category: SourceCategory


# Strict RFC 5322 compatible regex tailored for plain text extraction
EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
)

# Pattern for Name <email> or Name (email)
NAMED_EMAIL_REGEX = re.compile(
    r"(?P<name>[A-Z][A-Za-z\s.'-]{2,40})\s*[<(\[]\s*(?P<email>[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7})\s*[>)\]]"
)

# Known bot, synthetic or placeholder domains to exclude
EXCLUDED_DOMAINS = {
    "example.com", "example.org", "example.net",
    "domain.com", "sample.org", "placeholder.com",
    "localhost", "test.com", "yoursite.com"
}

# Known non-human or system local parts
EXCLUDED_LOCAL_PARTS = {
    "noreply", "no-reply", "dependabot", "sentry",
    "mailer-daemon", "postmaster", "root", "git",
    "actions", "github-actions", "bot", "privacy", "abuse"
}

ROLE_KEYWORDS = {
    "lead": 0.95,
    "creator": 0.95,
    "author": 0.90,
    "maintainer": 0.90,
    "founder": 0.90,
    "principal": 0.85,
    "architect": 0.85,
    "core": 0.85,
    "developer": 0.80,
    "engineer": 0.80,
    "security": 0.80,
    "coordinator": 0.75,
    "contributor": 0.70,
}


class ContactExtractor:
    @staticmethod
    def extract_from_text(
        text: str,
        source_url: str,
        source_category: SourceCategory = SourceCategory.GITHUB_README
    ) -> List[ExtractedContact]:
        results: List[ExtractedContact] = []
        if not text:
            return results

        seen_emails: Set[str] = set()

        # 1. First pass: Check for Name <email> structures
        for match in NAMED_EMAIL_REGEX.finditer(text):
            email = match.group("email").lower().strip()
            name = match.group("name").strip()

            if not ContactExtractor._is_valid_candidate(email):
                continue

            if email in seen_emails:
                continue
            seen_emails.add(email)

            start = max(0, match.start() - 80)
            end = min(len(text), match.end() + 80)
            evidence = text[start:end].replace("\n", " ").strip()

            score, detected_role = ContactExtractor._calculate_relevance(evidence)

            results.append(
                ExtractedContact(
                    email=email,
                    full_name=name,
                    role_title=detected_role,
                    evidence_text=evidence,
                    relevance_score=score,
                    source_url=source_url,
                    source_category=source_category
                )
            )

        # 2. Second pass: All standard email occurrences
        for match in EMAIL_REGEX.finditer(text):
            email = match.group(0).lower().strip()

            if not ContactExtractor._is_valid_candidate(email):
                continue

            if email in seen_emails:
                continue
            seen_emails.add(email)

            start = max(0, match.start() - 90)
            end = min(len(text), match.end() + 90)
            evidence = text[start:end].replace("\n", " ").strip()

            score, detected_role = ContactExtractor._calculate_relevance(evidence)
            name_guess = ContactExtractor._guess_name_from_evidence(evidence, email)

            results.append(
                ExtractedContact(
                    email=email,
                    full_name=name_guess,
                    role_title=detected_role,
                    evidence_text=evidence,
                    relevance_score=score,
                    source_url=source_url,
                    source_category=source_category
                )
            )

        return results

    @staticmethod
    def _is_valid_candidate(email: str) -> bool:
        if "@" not in email:
            return False

        # Filter out image/media extensions captured as part of pseudo addresses
        if any(email.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp")):
            return False

        local_part, domain = email.split("@", 1)
        domain = domain.lower()
        local_part = local_part.lower()

        if domain in EXCLUDED_DOMAINS:
            return False

        for excl in EXCLUDED_LOCAL_PARTS:
            if excl == local_part or local_part.startswith(f"{excl}+") or local_part.startswith(f"{excl}-"):
                return False

        return True

    @staticmethod
    def _calculate_relevance(context_snippet: str) -> (float, Optional[str]):
        snippet_lower = context_snippet.lower()
        score = 0.50
        detected_role = None

        for keyword, weight in sorted(ROLE_KEYWORDS.items(), key=lambda x: x[1], reverse=True):
            if keyword in snippet_lower:
                score = max(score, weight)
                if not detected_role:
                    detected_role = keyword.capitalize()

        return score, detected_role

    @staticmethod
    def _guess_name_from_evidence(evidence: str, email: str) -> Optional[str]:
        # If evidence contains Maintainer: John Smith
        patterns = [
            r"(?:maintainer|author|lead|developer|contact):\s*([A-Z][A-Za-z\s.'-]{2,30})",
            r"([A-Z][A-Za-z\s.'-]{2,30})\s*(?:is the|serves as|acts as)"
        ]
        for p in patterns:
            m = re.search(p, evidence, re.IGNORECASE)
            if m:
                candidate = m.group(1).strip()
                if len(candidate.split()) >= 2:
                    return candidate

        # Format local part if like john.doe
        local_part = email.split("@")[0]
        if "." in local_part:
            parts = local_part.split(".")
            if len(parts) == 2 and all(p.isalpha() for p in parts):
                return f"{parts[0].capitalize()} {parts[1].capitalize()}"

        return None
