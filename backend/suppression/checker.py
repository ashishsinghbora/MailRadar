import uuid
from typing import Optional
from sqlalchemy.orm import Session
from backend.models import SuppressionEntry, SuppressionReason, Contact
import jwt
from backend.core.config import settings


class SuppressionChecker:
    @staticmethod
    def is_suppressed(db: Session, email: str, organization_id: Optional[uuid.UUID] = None) -> bool:
        norm_email = email.strip().lower()

        # 1. Global suppression check
        global_entry = db.query(SuppressionEntry).filter(
            SuppressionEntry.email == norm_email,
            SuppressionEntry.organization_id.is_(None)
        ).first()
        if global_entry:
            return True

        # 2. Org-specific suppression check
        if organization_id:
            org_entry = db.query(SuppressionEntry).filter(
                SuppressionEntry.email == norm_email,
                SuppressionEntry.organization_id == organization_id
            ).first()
            if org_entry:
                return True

        return False

    @staticmethod
    def suppress_email(
        db: Session,
        email: str,
        reason: SuppressionReason,
        organization_id: Optional[uuid.UUID] = None,
        notes: Optional[str] = None
    ) -> SuppressionEntry:
        norm_email = email.strip().lower()

        # Update any matching Contact records in database to is_suppressed = True
        query = db.query(Contact).filter(Contact.email == norm_email)
        if organization_id:
            query = query.filter(Contact.organization_id == organization_id)
        for contact in query.all():
            contact.is_suppressed = True

        # Check existing suppression entry
        existing = db.query(SuppressionEntry).filter(
            SuppressionEntry.email == norm_email,
            SuppressionEntry.organization_id == organization_id
        ).first()

        if existing:
            existing.reason = reason
            if notes:
                existing.notes = notes
            db.commit()
            return existing

        new_entry = SuppressionEntry(
            id=uuid.uuid4(),
            organization_id=organization_id,
            email=norm_email,
            reason=reason,
            notes=notes
        )
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)
        return new_entry

    @staticmethod
    def generate_unsubscribe_token(email: str, organization_id: uuid.UUID) -> str:
        payload = {
            "email": email.strip().lower(),
            "org_id": str(organization_id),
            "purpose": "unsubscribe"
        }
        return jwt.encode(payload, settings.secret_key, algorithm="HS256")

    @staticmethod
    def decode_unsubscribe_token(token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
            if payload.get("purpose") == "unsubscribe":
                return payload
        except Exception:
            pass
        return None
