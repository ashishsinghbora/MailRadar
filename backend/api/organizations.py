from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models import Organization, User
from backend.schemas import OrganizationOut, OrganizationUpdate
from backend.api.deps import get_current_user, get_current_admin, log_audit

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("/current", response_model=OrganizationOut)
def get_current_organization(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.patch("/current", response_model=OrganizationOut)
def update_current_organization(
    req: OrganizationUpdate,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.id == admin_user.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if req.name is not None:
        org.name = req.name
    if req.description is not None:
        org.description = req.description
    if req.website is not None:
        org.website = req.website
    if req.settings_json is not None:
        current_settings = dict(org.settings_json)
        current_settings.update(req.settings_json)
        org.settings_json = current_settings

    db.commit()
    db.refresh(org)

    log_audit(
        db,
        action="ORGANIZATION_UPDATED",
        target_type="ORGANIZATION",
        user_id=admin_user.id,
        organization_id=admin_user.organization_id,
        target_id=str(org.id),
        metadata_json=req.model_dump(exclude_unset=True)
    )
    return org
