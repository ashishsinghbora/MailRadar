from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
from pydantic import BaseModel, EmailStr, Field
from backend.models import (
    UserRole, VerificationStatus, SourceCategory, JobStatus,
    SuppressionReason, CampaignStatus, ApprovalStatus, DeliveryStatus,
    MessageEventType
)


# Token & Auth
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    email: str
    role: UserRole
    organization_id: uuid.UUID


class TokenData(BaseModel):
    sub: Optional[str] = None
    role: Optional[UserRole] = None
    organization_id: Optional[str] = None


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    organization_name: str = Field(..., min_length=2)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


# Organization
class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    website: Optional[str] = None
    settings_json: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    settings_json: Optional[Dict[str, Any]] = None


# Project
class ProjectCreate(BaseModel):
    name: str
    full_name: str
    description: Optional[str] = None
    owner: str
    stars_count: int = 0
    forks_count: int = 0
    language: Optional[str] = None
    topics: List[str] = []
    repository_url: str
    homepage_url: Optional[str] = None
    contributing_url: Optional[str] = None


class ProjectOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    full_name: str
    description: Optional[str] = None
    owner: str
    stars_count: int
    forks_count: int
    language: Optional[str] = None
    topics: List[str]
    repository_url: str
    homepage_url: Optional[str] = None
    contributing_url: Optional[str] = None
    last_activity_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Contact Source
class ContactSourceOut(BaseModel):
    id: uuid.UUID
    contact_id: uuid.UUID
    source_url: str
    source_category: SourceCategory
    evidence_text: str
    extracted_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


# Contact
class ContactCreate(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role_title: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    source_url: str
    source_category: SourceCategory
    evidence_text: str


class ContactOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    email: str
    full_name: Optional[str] = None
    role_title: Optional[str] = None
    relevance_score: float
    verification_status: VerificationStatus
    is_suppressed: bool
    created_at: datetime
    updated_at: datetime
    sources: List[ContactSourceOut] = []

    model_config = {"from_attributes": True}


# Discovery
class DiscoveryQuery(BaseModel):
    query: str
    language: Optional[str] = None
    min_stars: int = 0
    max_results: int = 20
    scan_sources: bool = True


class DiscoveryJobOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    target_query: str
    job_type: str
    status: JobStatus
    projects_found: int
    contacts_found: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Verification
class VerificationRequest(BaseModel):
    contact_id: uuid.UUID


class VerificationRecordOut(BaseModel):
    id: uuid.UUID
    contact_id: uuid.UUID
    status: VerificationStatus
    mx_records: List[str]
    details: Optional[str] = None
    verified_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


# Suppression
class SuppressionCreate(BaseModel):
    email: EmailStr
    reason: SuppressionReason = SuppressionReason.MANUAL
    notes: Optional[str] = None


class SuppressionOut(BaseModel):
    id: uuid.UUID
    organization_id: Optional[uuid.UUID] = None
    email: str
    reason: SuppressionReason
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Templates
class EmailTemplateCreate(BaseModel):
    name: str
    subject: str
    body_markdown: str


class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body_markdown: Optional[str] = None


class EmailTemplateOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    subject: str
    body_markdown: str
    body_html: Optional[str] = None
    variables: List[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TemplatePreviewRequest(BaseModel):
    template_id: uuid.UUID
    contact_id: Optional[uuid.UUID] = None
    sample_context: Optional[Dict[str, str]] = None


class TemplatePreviewOut(BaseModel):
    subject: str
    body_markdown: str
    body_html: str
    resolved_variables: Dict[str, str]


# Campaigns
class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    template_id: Optional[uuid.UUID] = None
    daily_limit: int = 50
    contact_ids: List[uuid.UUID] = []


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    template_id: Optional[uuid.UUID] = None
    daily_limit: Optional[int] = None
    status: Optional[CampaignStatus] = None


class CampaignRecipientOut(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    contact_id: uuid.UUID
    approval_status: ApprovalStatus
    delivery_status: DeliveryStatus
    personalized_subject: Optional[str] = None
    personalized_body: Optional[str] = None
    sent_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    contact: Optional[ContactOut] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CampaignOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    template_id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None
    status: CampaignStatus
    scheduled_at: Optional[datetime] = None
    daily_limit: int
    sent_count: int
    approved_count: int
    recipient_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Approval Queue
class RecipientApprovalAction(BaseModel):
    recipient_id: uuid.UUID
    approved: bool
    rejection_reason: Optional[str] = None


class BulkApprovalAction(BaseModel):
    campaign_id: uuid.UUID
    recipient_ids: List[uuid.UUID]
    approved: bool


# Message & Delivery
class MessageEventOut(BaseModel):
    id: uuid.UUID
    campaign_recipient_id: uuid.UUID
    event_type: MessageEventType
    provider_message_id: Optional[str] = None
    payload: Dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class SendCampaignRequest(BaseModel):
    campaign_id: uuid.UUID
    test_mode: bool = True  # Defaults to sandbox safety


# Connected Accounts & Integrations
class ConnectedAccountCreate(BaseModel):
    provider: str
    credentials: Dict[str, Any]


class ConnectedAccountOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    provider: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Audit Log
class AuditLogOut(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    organization_id: Optional[uuid.UUID] = None
    action: str
    target_type: str
    target_id: Optional[str] = None
    ip_address: Optional[str] = None
    metadata_json: Dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


# Analytics
class DashboardMetrics(BaseModel):
    projects_count: int
    sources_analyzed: int
    contacts_found: int
    eligible_contacts: int
    pending_reviews: int
    active_campaigns: int
    delivery_count: int
    bounced_count: int
    recent_jobs: List[DiscoveryJobOut]
    recent_campaigns: List[CampaignOut]
