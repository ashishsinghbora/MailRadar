import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.models import (
    Campaign, CampaignRecipient, ApprovalStatus, DeliveryStatus,
    CampaignStatus, MessageEvent, MessageEventType, Contact
)
from backend.suppression.checker import SuppressionChecker
from backend.campaigns.renderer import TemplateRenderer
from backend.providers.registry import ProviderRegistry

logger = logging.getLogger(__name__)


class CampaignEngine:
    @staticmethod
    async def process_campaign_dispatch(
        db: Session,
        campaign_id: uuid.UUID,
        test_mode: bool = True
    ) -> Dict[str, Any]:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        if campaign.status not in (CampaignStatus.APPROVED, CampaignStatus.SENDING, CampaignStatus.SCHEDULED):
            raise ValueError(
                f"Campaign cannot be sent from state '{campaign.status.value}'. Must be APPROVED."
            )

        campaign.status = CampaignStatus.SENDING
        db.commit()

        # Query all approved and pending delivery recipients
        recipients = db.query(CampaignRecipient).filter(
            CampaignRecipient.campaign_id == campaign_id,
            CampaignRecipient.approval_status == ApprovalStatus.APPROVED,
            CampaignRecipient.delivery_status == DeliveryStatus.PENDING
        ).limit(campaign.daily_limit).all()

        provider = ProviderRegistry.get_provider("sandbox" if test_mode else None)
        processed = 0
        delivered = 0
        suppressed_count = 0
        bounced_count = 0

        for recipient in recipients:
            contact: Contact = recipient.contact
            if not contact:
                continue

            processed += 1

            # 1. HARD SUPPRESSION CHECK (Global and Org)
            if contact.is_suppressed or SuppressionChecker.is_suppressed(
                db, contact.email, campaign.organization_id
            ):
                recipient.delivery_status = DeliveryStatus.SUPPRESSED
                recipient.rejection_reason = "Recipient is present on suppression / opt-out list."
                suppressed_count += 1
                db.commit()
                continue

            # 2. DUPLICATE DELIVERY PREVENTION (Idempotency check)
            existing_event = db.query(MessageEvent).filter(
                MessageEvent.campaign_recipient_id == recipient.id,
                MessageEvent.event_type == MessageEventType.SENT
            ).first()
            if existing_event:
                recipient.delivery_status = DeliveryStatus.SENT
                db.commit()
                continue

            # 3. CONTEXT RESOLUTION & PERSONALIZATION
            org_name = campaign.organization.name if campaign.organization else "MailRadar"
            project_name = contact.project.name if contact.project else "your open-source project"
            first_name = (contact.full_name or "").split()[0] if contact.full_name else "there"

            unsub_token = SuppressionChecker.generate_unsubscribe_token(
                contact.email, campaign.organization_id
            )
            unsub_url = f"http://localhost:8000/api/v1/suppression/unsubscribe?token={unsub_token}"

            context = {
                "first_name": first_name,
                "full_name": contact.full_name or "Maintainer",
                "project_name": project_name,
                "organization_name": org_name,
                "unsubscribe_url": unsub_url
            }

            template = campaign.template
            if not template:
                recipient.delivery_status = DeliveryStatus.FAILED
                recipient.rejection_reason = "No template associated with campaign."
                db.commit()
                continue

            subject = TemplateRenderer.render(template.subject, context)
            body_markdown = TemplateRenderer.render(template.body_markdown, context)
            body_html = TemplateRenderer.markdown_to_html(body_markdown)

            recipient.personalized_subject = subject
            recipient.personalized_body = body_markdown

            # 4. DISPATCH
            headers = {
                "List-Unsubscribe": f"<{unsub_url}>",
                "X-Campaign-ID": str(campaign.id),
                "X-MailRadar-Provenance": "Official-Project-Maintainer-Outreach"
            }

            result = await provider.send_email(
                to_email=contact.email,
                subject=subject,
                body_markdown=body_markdown,
                body_html=body_html,
                headers=headers,
                metadata={"campaign_id": str(campaign.id), "contact_id": str(contact.id)}
            )

            if result.success:
                recipient.delivery_status = DeliveryStatus.SENT
                recipient.sent_at = datetime.now(timezone.utc)
                delivered += 1
                campaign.sent_count += 1

                # Record Sent Event
                event = MessageEvent(
                    id=uuid.uuid4(),
                    campaign_recipient_id=recipient.id,
                    event_type=MessageEventType.SENT,
                    provider_message_id=result.provider_message_id,
                    payload=result.raw_payload
                )
                db.add(event)
            else:
                if result.status == "BOUNCED":
                    recipient.delivery_status = DeliveryStatus.BOUNCED
                    recipient.rejection_reason = result.error_message
                    bounced_count += 1
                    event = MessageEvent(
                        id=uuid.uuid4(),
                        campaign_recipient_id=recipient.id,
                        event_type=MessageEventType.BOUNCED,
                        provider_message_id=result.provider_message_id,
                        payload=result.raw_payload
                    )
                    db.add(event)
                else:
                    recipient.delivery_status = DeliveryStatus.FAILED
                    recipient.rejection_reason = result.error_message

            db.commit()

        # Update campaign status
        remaining = db.query(CampaignRecipient).filter(
            CampaignRecipient.campaign_id == campaign_id,
            CampaignRecipient.approval_status == ApprovalStatus.APPROVED,
            CampaignRecipient.delivery_status == DeliveryStatus.PENDING
        ).count()

        if remaining == 0:
            campaign.status = CampaignStatus.COMPLETED
        db.commit()

        return {
            "campaign_id": str(campaign_id),
            "processed": processed,
            "delivered": delivered,
            "suppressed": suppressed_count,
            "bounced": bounced_count,
            "remaining_pending": remaining,
            "status": campaign.status.value
        }
