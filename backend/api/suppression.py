from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models import SuppressionEntry, User, SuppressionReason
from backend.schemas import SuppressionOut, SuppressionCreate
from backend.suppression.checker import SuppressionChecker
from backend.api.deps import get_current_user, log_audit

router = APIRouter(prefix="/suppression", tags=["Suppression"])


@router.get("", response_model=List[SuppressionOut])
def list_suppression(
    query: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(SuppressionEntry).filter(
        (SuppressionEntry.organization_id == current_user.organization_id) |
        (SuppressionEntry.organization_id.is_(None))
    )
    if query:
        q = q.filter(SuppressionEntry.email.ilike(f"%{query}%"))

    return q.order_by(SuppressionEntry.created_at.desc()).all()


@router.post("", response_model=SuppressionOut)
def add_suppression(
    req: SuppressionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entry = SuppressionChecker.suppress_email(
        db=db,
        email=req.email,
        reason=req.reason,
        organization_id=current_user.organization_id,
        notes=req.notes
    )

    log_audit(
        db,
        action="SUPPRESSION_ADDED",
        target_type="SUPPRESSION",
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        target_id=str(entry.id),
        metadata_json={"email": req.email, "reason": req.reason.value}
    )
    return entry


@router.delete("/{entry_id}")
def delete_suppression(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entry = db.query(SuppressionEntry).filter(
        SuppressionEntry.id == entry_id,
        SuppressionEntry.organization_id == current_user.organization_id
    ).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Suppression entry not found or belongs to global blocklist")

    db.delete(entry)
    db.commit()

    log_audit(
        db,
        action="SUPPRESSION_REMOVED",
        target_type="SUPPRESSION",
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        target_id=str(entry_id)
    )
    return {"status": "success", "message": f"Suppression entry {entry_id} removed."}


@router.get("/unsubscribe", response_class=HTMLResponse)
def unsubscribe_recipient(
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    payload = SuppressionChecker.decode_unsubscribe_token(token)
    if not payload:
        return HTMLResponse(
            content="""<html><body style="font-family:sans-serif; text-align:center; padding: 50px;">
            <h2>Invalid or Expired Unsubscribe Link</h2>
            <p>We could not process this request. If you believe this is an error, please reply directly to the email.</p>
            </body></html>""",
            status_code=400
        )

    email = payload.get("email")
    org_id_str = payload.get("org_id")
    org_id = uuid.UUID(org_id_str) if org_id_str else None

    SuppressionChecker.suppress_email(
        db=db,
        email=email,
        reason=SuppressionReason.OPT_OUT,
        organization_id=org_id,
        notes="Unsubscribed via one-click link."
    )

    return HTMLResponse(
        content=f"""<html><body style="font-family:sans-serif; text-align:center; padding: 50px; background-color: #0f172a; color: #f8fafc;">
        <div style="max-width: 500px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 8px; border: 1px solid #334155;">
            <h2 style="color: #38bdf8;">Unsubscribed Successfully</h2>
            <p>The address <strong>{email}</strong> has been permanently removed and suppressed from future outreach campaigns.</p>
            <p style="color: #94a3b8; font-size: 0.9em;">MailRadar respects your preferences and will never contact this address again.</p>
        </div>
        </body></html>"""
    )
