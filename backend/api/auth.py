import uuid
import re
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.core.security import hash_password, verify_password, create_access_token
from backend.database.session import get_db
from backend.models import User, Organization, UserRole
from backend.schemas import UserRegister, UserLogin, UserOut, Token, PasswordChange
from backend.api.deps import get_current_user, log_audit

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(req: UserRegister, request: Request, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == req.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # Create slug for org
    slug = re.sub(r"[^a-z0-9]+", "-", req.organization_name.lower()).strip("-")
    if not slug:
        slug = f"org-{uuid.uuid4().hex[:8]}"

    existing_org = db.query(Organization).filter(Organization.slug == slug).first()
    if existing_org:
        slug = f"{slug}-{uuid.uuid4().hex[:4]}"

    org = Organization(
        id=uuid.uuid4(),
        name=req.organization_name,
        slug=slug,
        settings_json={"created_via": "self_register"}
    )
    db.add(org)
    db.flush()

    user = User(
        id=uuid.uuid4(),
        email=req.email.lower(),
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role=UserRole.ADMIN,
        is_active=True,
        organization_id=org.id
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    client_ip = request.client.host if request.client else None
    log_audit(
        db,
        action="USER_REGISTER",
        target_type="USER",
        user_id=user.id,
        organization_id=org.id,
        target_id=str(user.id),
        ip_address=client_ip,
        metadata_json={"email": user.email, "org_name": org.name}
    )

    access_token = create_access_token(
        subject=user.id,
        claims={"role": user.role.value, "organization_id": str(org.id), "email": user.email}
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role,
        organization_id=org.id
    )


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username.lower()).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated. Please contact an administrator."
        )

    client_ip = request.client.host if request and request.client else None
    log_audit(
        db,
        action="USER_LOGIN",
        target_type="USER",
        user_id=user.id,
        organization_id=user.organization_id,
        target_id=str(user.id),
        ip_address=client_ip
    )

    access_token = create_access_token(
        subject=user.id,
        claims={"role": user.role.value, "organization_id": str(user.organization_id), "email": user.email}
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role,
        organization_id=user.organization_id
    )


@router.post("/login/json", response_model=Token)
def login_json(req: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated."
        )

    client_ip = request.client.host if request.client else None
    log_audit(
        db,
        action="USER_LOGIN_JSON",
        target_type="USER",
        user_id=user.id,
        organization_id=user.organization_id,
        target_id=str(user.id),
        ip_address=client_ip
    )

    access_token = create_access_token(
        subject=user.id,
        claims={"role": user.role.value, "organization_id": str(user.organization_id), "email": user.email}
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role,
        organization_id=user.organization_id
    )


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password")
def change_password(
    req: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect."
        )

    current_user.hashed_password = hash_password(req.new_password)
    db.commit()
    log_audit(
        db,
        action="PASSWORD_CHANGED",
        target_type="USER",
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        target_id=str(current_user.id)
    )
    return {"status": "success", "message": "Password updated successfully."}


@router.delete("/account")
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.id
    org_id = current_user.organization_id
    db.delete(current_user)
    db.commit()
    log_audit(
        db,
        action="USER_ACCOUNT_DELETED",
        target_type="USER",
        user_id=user_id,
        organization_id=org_id,
        target_id=str(user_id)
    )
    return {"status": "success", "message": "Account deleted."}
