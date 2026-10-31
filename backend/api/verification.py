from datetime import datetime, timezone
from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models import Contact, VerificationRecord, User, VerificationStatus
from backend.schemas import VerificationRecordOut, VerificationRequest
from backend.verification.dns_verifier import DNSVerifier
from backend.api.deps import get_current_user, log_audit

router = APIRouter(prefix="/verification", tags=["Verification"])


@router.post("/verify", response_model=VerificationRecordOut)
def verify_contact(
    req: VerificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    contact = db.query(Contact).filter(
        Contact.id == req.contact_id,
        Contact.organization_id == current_user.organization_id
    ).first()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    result = DNSVerifier.verify_email(contact.email, allow_mock=True)

    contact.verification_status = result.status
    record = VerificationRecord(
        id=uuid.uuid4(),
        contact_id=contact.id,
        status=result.status,
        mx_records=result.mx_records,
        details=result.details,
        verified_at=datetime.now(timezone.utc)
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    log_audit(
        db,
        action="CONTACT_VERIFIED",
        target_type="CONTACT",
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        target_id=str(contact.id),
        metadata_json={"email": contact.email, "status": result.status.value}
    )
    return record


@router.post("/verify-all")
def verify_all_unverified(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    unverified = db.query(Contact).filter(
        Contact.organization_id == current_user.organization_id,
        Contact.verification_status == VerificationStatus.UNCHECKED
    ).limit(100).all()

    count = 0
    for contact in unverified:
        res = DNSVerifier.verify_email(contact.email, allow_mock=True)
        contact.verification_status = res.status
        rec = VerificationRecord(
            id=uuid.uuid4(),
            contact_id=contact.id,
            status=res.status,
            mx_records=res.mx_records,
            details=res.details,
            verified_at=datetime.now(timezone.utc)
        )
        db.add(rec)
        count += 1

    db.commit()
    return {"status": "success", "verified_count": count}


@router.get("/records/{contact_id}", response_model=List[VerificationRecordOut])
def get_verification_history(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.organization_id == current_user.organization_id
    ).first()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    records = db.query(VerificationRecord).filter(
        VerificationRecord.contact_id == contact_id
    ).order_by(VerificationRecord.verified_at.desc()).all()

    return records
