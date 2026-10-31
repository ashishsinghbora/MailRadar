from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models import (
    Project, Contact, ContactSource, DiscoveryJob,
    Campaign, CampaignRecipient, MessageEvent, MessageEventType,
    User, ApprovalStatus, CampaignStatus, DeliveryStatus
)
from backend.schemas import DashboardMetrics, DiscoveryJobOut, CampaignOut
from backend.api.deps import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=DashboardMetrics)
def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    org_id = current_user.organization_id

    projects_count = db.query(Project).filter(Project.organization_id == org_id).count()

    sources_analyzed = db.query(ContactSource).join(Contact).filter(
        Contact.organization_id == org_id
    ).count()

    contacts_found = db.query(Contact).filter(Contact.organization_id == org_id).count()

    eligible_contacts = db.query(Contact).filter(
        Contact.organization_id == org_id,
        Contact.is_suppressed == False
    ).count()

    pending_reviews = db.query(CampaignRecipient).join(Campaign).filter(
        Campaign.organization_id == org_id,
        CampaignRecipient.approval_status == ApprovalStatus.PENDING
    ).count()

    active_campaigns = db.query(Campaign).filter(
        Campaign.organization_id == org_id,
        Campaign.status.in_([CampaignStatus.APPROVED, CampaignStatus.SENDING, CampaignStatus.SCHEDULED])
    ).count()

    delivery_count = db.query(MessageEvent).join(CampaignRecipient).join(Campaign).filter(
        Campaign.organization_id == org_id,
        MessageEvent.event_type == MessageEventType.SENT
    ).count()

    bounced_count = db.query(MessageEvent).join(CampaignRecipient).join(Campaign).filter(
        Campaign.organization_id == org_id,
        MessageEvent.event_type == MessageEventType.BOUNCED
    ).count()

    recent_jobs = db.query(DiscoveryJob).filter(
        DiscoveryJob.organization_id == org_id
    ).order_by(DiscoveryJob.created_at.desc()).limit(5).all()

    recent_campaigns_db = db.query(Campaign).filter(
        Campaign.organization_id == org_id
    ).order_by(Campaign.created_at.desc()).limit(5).all()

    recent_campaigns = []
    for c in recent_campaigns_db:
        recipient_count = db.query(CampaignRecipient).filter(
            CampaignRecipient.campaign_id == c.id
        ).count()
        recent_campaigns.append(
            CampaignOut(
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
        )

    return DashboardMetrics(
        projects_count=projects_count,
        sources_analyzed=sources_analyzed,
        contacts_found=contacts_found,
        eligible_contacts=eligible_contacts,
        pending_reviews=pending_reviews,
        active_campaigns=active_campaigns,
        delivery_count=delivery_count,
        bounced_count=bounced_count,
        recent_jobs=recent_jobs,
        recent_campaigns=recent_campaigns
    )
