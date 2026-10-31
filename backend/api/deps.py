import uuid
from typing import Generator, Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.security import decode_access_token
from backend.database.session import get_db
from backend.models import User, UserRole, AuditLog

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except Exception:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise credentials_exception
    return user


def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have administrative privileges."
        )
    return current_user


def log_audit(
    db: Session,
    action: str,
    target_type: str,
    user_id: Optional[uuid.UUID] = None,
    organization_id: Optional[uuid.UUID] = None,
    target_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    metadata_json: Optional[Dict[str, Any]] = None
) -> AuditLog:
    entry = AuditLog(
        id=uuid.uuid4(),
        user_id=user_id,
        organization_id=organization_id,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id else None,
        ip_address=ip_address,
        metadata_json=metadata_json or {}
    )
    db.add(entry)
    db.commit()
    return entry
