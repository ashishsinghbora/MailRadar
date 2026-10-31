from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models import MessageEvent, CampaignRecipient, Campaign, User
from backend.schemas import MessageEventOut, SendCampaignRequest
from backend.campaigns.engine import CampaignEngine
from backend.providers.sandbox import SandboxProvider
from backend.api.deps import get_current_user, log_audit

router = APIRouter(prefix="/messages", tags=["Messages & Delivery"])


@router.post("/send")
async def send_campaign(
    req: SendCampaignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    campaign = db.query(Campaign).filter(
        Campaign.id == req.campaign_id,
        Campaign.organization_id == current_user.organization_id
    ).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    try:
        dispatch_result = await CampaignEngine.process_campaign_dispatch(
            db=db,
            campaign_id=req.campaign_id,
            test_mode=req.test_mode
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    log_audit(
        db,
        action="CAMPAIGN_DISPATCHED",
        target_type="CAMPAIGN",
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        target_id=str(campaign.id),
        metadata_json=dispatch_result
    )
    return dispatch_result


@router.get("/events", response_model=List[MessageEventOut])
def list_message_events(
    campaign_id: Optional[uuid.UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(MessageEvent).join(CampaignRecipient).join(Campaign).filter(
        Campaign.organization_id == current_user.organization_id
    )
    if campaign_id:
        q = q.filter(CampaignRecipient.campaign_id == campaign_id)

    return q.order_by(MessageEvent.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/sandbox")
def get_sandbox_inbox(
    current_user: User = Depends(get_current_user)
):
    """Retrieve simulated outgoing messages stored by SandboxProvider."""
    return {
        "mode": "SANDBOX",
        "total_captured": len(SandboxProvider.get_sent_messages()),
        "messages": SandboxProvider.get_sent_messages()[-50:]
    }
