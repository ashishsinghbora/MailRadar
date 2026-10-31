from datetime import datetime, timezone
import csv
import io
import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session, joinedload

from backend.database.session import get_db
from backend.models import Contact, ContactSource, User, VerificationStatus
from backend.schemas import ContactOut, ContactCreate
from backend.api.deps import get_current_user, log_audit
from backend.verification.dns_verifier import DNSVerifier

router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.get("", response_model=List[ContactOut])
def list_contacts(
    query: Optional[str] = None,
    project_id: Optional[uuid.UUID] = None,
    verification_status: Optional[VerificationStatus] = None,
    min_relevance: Optional[float] = None,
    is_suppressed: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(Contact).options(joinedload(Contact.sources)).filter(
        Contact.organization_id == current_user.organization_id
    )

    if query:
        q = q.filter(
            (Contact.email.ilike(f"%{query}%")) |
            (Contact.full_name.ilike(f"%{query}%")) |
            (Contact.role_title.ilike(f"%{query}%"))
        )
    if project_id:
        q = q.filter(Contact.project_id == project_id)
    if verification_status:
        q = q.filter(Contact.verification_status == verification_status)
    if min_relevance is not None:
        q = q.filter(Contact.relevance_score >= min_relevance)
    if is_suppressed is not None:
        q = q.filter(Contact.is_suppressed == is_suppressed)

    contacts = q.order_by(Contact.relevance_score.desc(), Contact.created_at.desc()).offset(skip).limit(limit).all()
    return contacts


@router.post("", response_model=ContactOut)
def create_contact(
    req: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    norm_email = req.email.strip().lower()
    existing = db.query(Contact).filter(
        Contact.organization_id == current_user.organization_id,
        Contact.email == norm_email
    ).first()

    if existing:
        return existing

    verif = DNSVerifier.verify_email(norm_email, allow_mock=True)

    contact = Contact(
        id=uuid.uuid4(),
        organization_id=current_user.organization_id,
        project_id=req.project_id,
        email=norm_email,
        full_name=req.full_name,
        role_title=req.role_title,
        relevance_score=0.75 if req.role_title else 0.5,
        verification_status=verif.status,
        is_suppressed=False
    )
    db.add(contact)
    db.flush()

    source = ContactSource(
        id=uuid.uuid4(),
        contact_id=contact.id,
        source_url=req.source_url,
        source_category=req.source_category,
        evidence_text=req.evidence_text[:1000],
        extracted_at=datetime.now(timezone.utc)
    )
    db.add(source)
    db.commit()
    db.refresh(contact)

    log_audit(
        db,
        action="CONTACT_CREATED",
        target_type="CONTACT",
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        target_id=str(contact.id)
    )
    return contact


@router.get("/export")
def export_contacts(
    format: str = Query("csv", pattern="^(csv|json)$"),
    project_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(Contact).options(joinedload(Contact.sources)).filter(
        Contact.organization_id == current_user.organization_id
    )
    if project_id:
        q = q.filter(Contact.project_id == project_id)

    contacts = q.all()

    if format == "json":
        data = [
            {
                "id": str(c.id),
                "email": c.email,
                "full_name": c.full_name,
                "role_title": c.role_title,
                "relevance_score": c.relevance_score,
                "verification_status": c.verification_status.value,
                "is_suppressed": c.is_suppressed,
                "sources": [
                    {
                        "source_url": s.source_url,
                        "source_category": s.source_category.value,
                        "evidence_text": s.evidence_text
                    }
                    for s in c.sources
                ]
            }
            for c in contacts
        ]
        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=contacts.json"}
        )

    # CSV Format
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Email", "Full Name", "Role Title", "Relevance Score",
        "Verification Status", "Suppressed", "Primary Source URL", "Evidence Snippet"
    ])

    for c in contacts:
        primary_source = c.sources[0].source_url if c.sources else ""
        primary_evidence = c.sources[0].evidence_text if c.sources else ""
        writer.writerow([
            c.email,
            c.full_name or "",
            c.role_title or "",
            c.relevance_score,
            c.verification_status.value,
            c.is_suppressed,
            primary_source,
            primary_evidence
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contacts.csv"}
    )


@router.get("/{contact_id}", response_model=ContactOut)
def get_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    c = db.query(Contact).options(joinedload(Contact.sources)).filter(
        Contact.id == contact_id,
        Contact.organization_id == current_user.organization_id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Contact not found")
    return c


@router.delete("/{contact_id}")
def delete_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    c = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.organization_id == current_user.organization_id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(c)
    db.commit()

    log_audit(
        db,
        action="CONTACT_DELETED",
        target_type="CONTACT",
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        target_id=str(contact_id)
    )
    return {"status": "success", "message": f"Contact {contact_id} deleted."}
