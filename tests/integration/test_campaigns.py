import uuid
import pytest
from fastapi.testclient import TestClient
from backend.models import Contact, ContactSource, SourceCategory, VerificationStatus, CampaignStatus, ApprovalStatus, DeliveryStatus, SuppressionReason
from backend.suppression.checker import SuppressionChecker
from backend.providers.sandbox import SandboxProvider


def test_campaign_full_lifecycle_and_approval_gate(client: TestClient, auth_headers, db_session, test_organization):
    SandboxProvider.clear()

    # 1. Create a Contact in DB
    contact = Contact(
        id=uuid.uuid4(),
        organization_id=test_organization.id,
        email="alex.lead@meshproject.org",
        full_name="Alex Lead",
        role_title="Lead Maintainer",
        relevance_score=0.90,
        verification_status=VerificationStatus.VALID,
        is_suppressed=False
    )
    db_session.add(contact)
    db_session.flush()

    source = ContactSource(
        id=uuid.uuid4(),
        contact_id=contact.id,
        source_url="https://github.com/mesh/mesh/blob/main/README.md",
        source_category=SourceCategory.GITHUB_README,
        evidence_text="Lead Maintainer: Alex Lead <alex.lead@meshproject.org>"
    )
    db_session.add(source)
    db_session.commit()

    # 2. Create Template
    tmpl_resp = client.post("/api/v1/templates", json={
        "name": "Integration Outreach",
        "subject": "Regarding {{project_name}}",
        "body_markdown": "Hi {{first_name}},\n\nExcited by {{project_name}}."
    }, headers=auth_headers)
    assert tmpl_resp.status_code == 200
    tmpl_id = tmpl_resp.json()["id"]

    # 3. Create Campaign
    camp_resp = client.post("/api/v1/campaigns", json={
        "name": "Q4 Collaboration Push",
        "description": "Connecting with core distributed systems leads.",
        "template_id": tmpl_id,
        "daily_limit": 50,
        "contact_ids": [str(contact.id)]
    }, headers=auth_headers)
    assert camp_resp.status_code == 200
    camp_data = camp_resp.json()
    camp_id = camp_data["id"]
    assert camp_data["status"] == "RECIPIENT_REVIEW"

    # 4. Mandatory Approval Check: Attempt to send BEFORE approval -> MUST FAIL
    pre_send_resp = client.post("/api/v1/messages/send", json={
        "campaign_id": camp_id,
        "test_mode": True
    }, headers=auth_headers)
    assert pre_send_resp.status_code == 400
    assert "Must be APPROVED" in pre_send_resp.json()["detail"]

    # 5. Review and Approve Recipient
    pending_resp = client.get(f"/api/v1/approvals?campaign_id={camp_id}", headers=auth_headers)
    assert pending_resp.status_code == 200
    pending_list = pending_resp.json()
    assert len(pending_list) == 1
    recipient_id = pending_list[0]["id"]

    approve_resp = client.post("/api/v1/approvals/review", json={
        "recipient_id": recipient_id,
        "approved": True
    }, headers=auth_headers)
    assert approve_resp.status_code == 200
    assert approve_resp.json()["approval_status"] == "APPROVED"

    # 6. Verify Campaign transitioned to APPROVED
    camp_check = client.get(f"/api/v1/campaigns/{camp_id}", headers=auth_headers)
    assert camp_check.json()["status"] == "APPROVED"

    # 7. Dispatch Campaign in Sandbox Mode
    send_resp = client.post("/api/v1/messages/send", json={
        "campaign_id": camp_id,
        "test_mode": True
    }, headers=auth_headers)
    assert send_resp.status_code == 200
    dispatch_data = send_resp.json()
    assert dispatch_data["delivered"] == 1
    assert dispatch_data["status"] == "COMPLETED"

    # 8. Verify SandboxProvider captured message
    sent_box = SandboxProvider.get_sent_messages()
    assert len(sent_box) == 1
    assert sent_box[0]["to_email"] == "alex.lead@meshproject.org"
    assert "Regarding" in sent_box[0]["subject"]
    assert "List-Unsubscribe" in sent_box[0]["headers"]

    # 9. Idempotency Check: Running send again must not duplicate message
    second_send = client.post("/api/v1/messages/send", json={
        "campaign_id": camp_id,
        "test_mode": True
    }, headers=auth_headers)
    # Campaign is already COMPLETED or has 0 pending
    assert second_send.status_code in (200, 400)
    assert len(SandboxProvider.get_sent_messages()) == 1  # Still exactly 1!


def test_suppression_enforcement_prevents_dispatch(client: TestClient, auth_headers, db_session, test_organization):
    SandboxProvider.clear()

    # Create suppressed contact
    supp_email = "suppressed.maintainer@mesh.org"
    contact = Contact(
        id=uuid.uuid4(),
        organization_id=test_organization.id,
        email=supp_email,
        full_name="Suppressed User",
        verification_status=VerificationStatus.VALID,
        is_suppressed=False
    )
    db_session.add(contact)
    db_session.commit()

    # Suppress email
    SuppressionChecker.suppress_email(
        db=db_session,
        email=supp_email,
        reason=SuppressionReason.OPT_OUT,
        organization_id=test_organization.id
    )

    # Create template & campaign
    tmpl = client.post("/api/v1/templates", json={
        "name": "Test Tmpl",
        "subject": "Hello",
        "body_markdown": "Test body"
    }, headers=auth_headers).json()

    camp = client.post("/api/v1/campaigns", json={
        "name": "Suppression Test Campaign",
        "template_id": tmpl["id"],
        "contact_ids": [str(contact.id)]
    }, headers=auth_headers).json()

    # Get recipient & approve
    pending = client.get(f"/api/v1/approvals?campaign_id={camp['id']}", headers=auth_headers).json()
    if pending:
        client.post("/api/v1/approvals/review", json={
            "recipient_id": pending[0]["id"],
            "approved": True
        }, headers=auth_headers)

        # Dispatch
        res = client.post("/api/v1/messages/send", json={
            "campaign_id": camp["id"],
            "test_mode": True
        }, headers=auth_headers).json()

        assert res["delivered"] == 0
        assert res["suppressed"] == 1
        assert len(SandboxProvider.get_sent_messages()) == 0
