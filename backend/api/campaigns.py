from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models import (
    Campaign, CampaignRecipient, Contact, EmailTemplate, User,
    CampaignStatus, ApprovalStatus, DeliveryStatus
)
from backend.schemas import (
    CampaignOut, CampaignCreate, CampaignUpdate, CampaignRecipientOut
)
from backend.api.deps import get_current_user, log_audit

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.get("", response_model=List[CampaignOut])
def list_campaigns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    campaigns = db.query(Campaign).filter(
        Campaign.organization_id == current_user.organization_id
    ).order_by(Campaign.created_at.desc()).all()

    result = []
    for c in campaigns:
        recipient_count = db.query(CampaignRecipient).filter(
            CampaignRecipient.campaign_id == c.id
        ).count()
        out = CampaignOut(
            id=c.id,
            organization_id=c.organization_id,
            template_id=c.template_id,
            name=c.name,
            description=c.description,
            status=c.status,
            scheduled_at=c.scheduled_at,
            daily_limit=c.daily_limit,
            sent_count=c.sent_count,
            approved_count=c.approved_count,
            recipient_count=recipient_count,
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        result.append(out)

    return result


@router.post("", response_model=CampaignOut)
def create_campaign(
    req: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if req.template_id:
        template = db.query(EmailTemplate).filter(
            EmailTemplate.id == req.template_id,
            EmailTemplate.organization_id == current_user.organization_id
        ).first()
        if not template:
            raise HTTPException(status_code=400, detail="Associated template not found")

    campaign = Campaign(
        id=uuid.uuid4(),
        organization_id=current_user.organization_id,
        template_id=req.template_id,
        name=req.name,
        description=req.description,
        status=CampaignStatus.DRAFT,
        daily_limit=req.daily_limit,
        sent_count=0,
        approved_count=0
    )
    db.add(campaign)
    db.flush()

    # Add recipients if contact_ids provided
    recipient_count = 0
    if req.contact_ids:
        contacts = db.query(Contact).filter(
            Contact.id.in_(req.contact_ids),
            Contact.organization_id == current_user.organization_id,
            Contact.is_suppressed == False
        ).all()

        for c in contacts:
            rec = CampaignRecipient(
                id=uuid.uuid4(),
                campaign_id=campaign.id,
                contact_id=c.id,
                approval_status=ApprovalStatus.PENDING,
                delivery_status=DeliveryStatus.PENDING
            )
            db.add(rec)
            recipient_count += 1

        if recipient_count > 0:
            campaign.status = CampaignStatus.RECIPIENT_REVIEW

    db.commit()
    db.refresh(campaign)

    log_audit(
        db,
        action="CAMPAIGN_CREATED",
        target_type="CAMPAIGN",
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        target_id=str(campaign.id),
        metadata_json={"name": campaign.name, "recipients": recipient_count}
    )

    return CampaignOut(
        id=campaign.id,
        organization_id=campaign.organization_id,
        template_id=campaign.template_id,
        name=campaign.name,
        description=campaign.description,
        status=campaign.status,
        scheduled_at=campaign.scheduled_at,
        daily_limit=campaign.daily_limit,
        sent_count=campaign.sent_count,
        approved_count=campaign.approved_count,
        recipient_count=recipient_count,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at
    )


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    c = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.organization_id == current_user.organization_id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")

    recipient_count = db.query(CampaignRecipient).filter(
        CampaignRecipient.campaign_id == c.id
    ).count()

    return CampaignOut(
        id=c.id,
        organization_id=c.organization_id,
        template_id=c.template_id,
        name=c.name,
        description=c.description,
        status=c.status,
        scheduled_at=c.scheduled_at,
        daily_limit=c.daily_limit,
        sent_count=c.sent_count,
        approved_count=c.approved_count,
        recipient_count=recipient_count,
        created_at=c.created_at,
        updated_at=c.updated_at
    )


@router.patch("/{campaign_id}", response_model=CampaignOut)
def update_campaign(
    campaign_id: uuid.UUID,
    req: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    c = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.organization_id == current_user.organization_id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if req.name is not None:
        c.name = req.name
    if req.description is not None:
        c.description = req.description
    if req.template_id is not None:
        c.template_id = req.template_id
    if req.daily_limit is not None:
        c.daily_limit = req.daily_limit
    if req.status is not None:
        c.status = req.status

    db.commit()
    db.refresh(c)

    recipient_count = db.query(CampaignRecipient).filter(
        CampaignRecipient.campaign_id == c.id
    ).count()

    log_audit(
        db,
        action="CAMPAIGN_UPDATED",
        target_type="CAMPAIGN",
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        target_id=str(c.id),
        metadata_json=req.model_dump(exclude_unset=True)
    )

    return CampaignOut(
        id=c.id,
        organization_id=c.organization_id,
        template_id=c.template_id,
        name=c.name,
        description=c.description,
        status=c.status,
        scheduled_at=c.scheduled_at,
        daily_limit=c.daily_limit,
        sent_count=c.sent_count,
        approved_count=c.approved_count,
        recipient_count=recipient_count,
        created_at=c.created_at,
        updated_at=c.updated_at
    )


@router.delete("/{campaign_id}")
def delete_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    c = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.organization_id == current_user.organization_id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")

    db.delete(c)
    db.commit()

    log_audit(
        db,
        action="CAMPAIGN_DELETED",
        target_type="CAMPAIGN",
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        target_id=str(campaign_id)
    )
    return {"status": "success", "message": f"Campaign {campaign_id} deleted."}
