from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models import AuditLog, User
from backend.schemas import AuditLogOut
from backend.api.deps import get_current_user

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("", response_model=List[AuditLogOut])
def list_audit_logs(
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(AuditLog).filter(
        AuditLog.organization_id == current_user.organization_id
    )
    if action:
        q = q.filter(AuditLog.action.ilike(f"%{action}%"))
    if target_type:
        q = q.filter(AuditLog.target_type == target_type)

    return q.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
