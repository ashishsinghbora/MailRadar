from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from backend.database.session import get_db
from backend.models import (
    Campaign, CampaignRecipient, Contact, User,
    ApprovalStatus, CampaignStatus
)
from backend.schemas import (
    CampaignRecipientOut, RecipientApprovalAction, BulkApprovalAction
)
from backend.api.deps import get_current_user, log_audit

router = APIRouter(prefix="/approvals", tags=["Approval Queue"])


@router.get("", response_model=List[CampaignRecipientOut])
def list_pending_approvals(
    campaign_id: Optional[uuid.UUID] = None,
    approval_status: Optional[ApprovalStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(CampaignRecipient).join(Campaign).options(
        joinedload(CampaignRecipient.contact).joinedload(Contact.sources)
    ).filter(
        Campaign.organization_id == current_user.organization_id
    )

    if campaign_id:
        q = q.filter(CampaignRecipient.campaign_id == campaign_id)
    if approval_status:
        q = q.filter(CampaignRecipient.approval_status == approval_status)
    else:
        # Defaults to showing pending reviews first
        q = q.filter(CampaignRecipient.approval_status == ApprovalStatus.PENDING)

    recipients = q.order_by(CampaignRecipient.created_at.desc()).offset(skip).limit(limit).all()
    return recipients


@router.post("/review", response_model=CampaignRecipientOut)
def review_recipient(
    action: RecipientApprovalAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rec = db.query(CampaignRecipient).join(Campaign).filter(
        CampaignRecipient.id == action.recipient_id,
        Campaign.organization_id == current_user.organization_id
    ).first()

    if not rec:
        raise HTTPException(status_code=404, detail="Campaign recipient not found")

    rec.approval_status = ApprovalStatus.APPROVED if action.approved else ApprovalStatus.REJECTED
    rec.rejection_reason = action.rejection_reason if not action.approved else None
    db.flush()

    # Update approved count on campaign
    campaign = db.query(Campaign).filter(Campaign.id == rec.campaign_id).first()
    if campaign:
        approved_count = db.query(CampaignRecipient).filter(
            CampaignRecipient.campaign_id == campaign.id,
            CampaignRecipient.approval_status == ApprovalStatus.APPROVED
        ).count()
        campaign.approved_count = approved_count

        if approved_count > 0 and campaign.status in (CampaignStatus.RECIPIENT_REVIEW, CampaignStatus.DRAFT):
            campaign.status = CampaignStatus.APPROVED

    db.commit()
    db.refresh(rec)

    log_audit(
        db,
        action="RECIPIENT_REVIEWED",
        target_type="CAMPAIGN_RECIPIENT",
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        target_id=str(rec.id),
        metadata_json={"approved": action.approved, "campaign_id": str(campaign.id)}
    )
    return rec


@router.post("/bulk-review")
def bulk_review_recipients(
    action: BulkApprovalAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    campaign = db.query(Campaign).filter(
        Campaign.id == action.campaign_id,
        Campaign.organization_id == current_user.organization_id
    ).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    status_to_set = ApprovalStatus.APPROVED if action.approved else ApprovalStatus.REJECTED

    updated = db.query(CampaignRecipient).filter(
        CampaignRecipient.campaign_id == action.campaign_id,
        CampaignRecipient.id.in_(action.recipient_ids)
    ).update({"approval_status": status_to_set}, synchronize_session=False)

    approved_count = db.query(CampaignRecipient).filter(
        CampaignRecipient.campaign_id == campaign.id,
        CampaignRecipient.approval_status == ApprovalStatus.APPROVED
    ).count()
    campaign.approved_count = approved_count

    if approved_count > 0 and campaign.status == CampaignStatus.RECIPIENT_REVIEW:
        campaign.status = CampaignStatus.APPROVED

    db.commit()

    log_audit(
        db,
        action="BULK_RECIPIENTS_REVIEWED",
        target_type="CAMPAIGN",
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        target_id=str(campaign.id),
        metadata_json={"count": updated, "approved": action.approved}
    )
    return {"status": "success", "updated_count": updated, "new_approved_total": approved_count}
