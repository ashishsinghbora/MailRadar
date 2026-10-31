from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models import User, UserRole
from backend.schemas import UserOut, UserUpdate
from backend.api.deps import get_current_user, get_current_admin, log_audit

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[UserOut])
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    users = db.query(User).filter(User.organization_id == current_user.organization_id).all()
    return users


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: uuid.UUID,
    req: UserUpdate,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    target_user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == admin_user.organization_id
    ).first()

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if req.full_name is not None:
        target_user.full_name = req.full_name
    if req.role is not None:
        target_user.role = req.role
    if req.is_active is not None:
        target_user.is_active = req.is_active

    db.commit()
    db.refresh(target_user)

    log_audit(
        db,
        action="USER_UPDATED",
        target_type="USER",
        user_id=admin_user.id,
        organization_id=admin_user.organization_id,
        target_id=str(target_user.id),
        metadata_json=req.model_dump(exclude_unset=True)
    )
    return target_user


@router.delete("/{user_id}")
def delete_user(
    user_id: uuid.UUID,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    if user_id == admin_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account through user management.")

    target_user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == admin_user.organization_id
    ).first()

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(target_user)
    db.commit()

    log_audit(
        db,
        action="USER_DELETED",
        target_type="USER",
        user_id=admin_user.id,
        organization_id=admin_user.organization_id,
        target_id=str(user_id)
    )
    return {"status": "success", "message": f"User {user_id} deleted."}
