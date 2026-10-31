from datetime import datetime, timezone
import enum
import uuid
from typing import Optional, List
from sqlalchemy import (
    String, Text, Boolean, Integer, Float, ForeignKey, Enum, Index, JSON, DateTime
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database.base import Base, GUID, TimestampMixin


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    settings_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    users: Mapped[List["User"]] = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    projects: Mapped[List["Project"]] = relationship("Project", back_populates="organization", cascade="all, delete-orphan")
    contacts: Mapped[List["Contact"]] = relationship("Contact", back_populates="organization", cascade="all, delete-orphan")
    campaigns: Mapped[List["Campaign"]] = relationship("Campaign", back_populates="organization", cascade="all, delete-orphan")
    templates: Mapped[List["EmailTemplate"]] = relationship("EmailTemplate", back_populates="organization", cascade="all, delete-orphan")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False),
        default=UserRole.OPERATOR,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)  # owner/repo
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    stars_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    forks_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    language: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    topics: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    repository_url: Mapped[str] = mapped_column(String(512), nullable=False)
    homepage_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    contributing_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    last_activity_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="projects")
    contacts: Mapped[List["Contact"]] = relationship("Contact", back_populates="project", cascade="all, delete-orphan")


class VerificationStatus(str, enum.Enum):
    UNCHECKED = "UNCHECKED"
    VALID = "VALID"
    NO_MX = "NO_MX"
    INVALID_SYNTAX = "INVALID_SYNTAX"
    DISPOSABLE = "DISPOSABLE"


class Contact(Base, TimestampMixin):
    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID, ForeignKey("projects.id", ondelete="SET NULL"), index=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status", native_enum=False),
        default=VerificationStatus.UNCHECKED,
        nullable=False
    )
    is_suppressed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="contacts")
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="contacts")
    sources: Mapped[List["ContactSource"]] = relationship("ContactSource", back_populates="contact", cascade="all, delete-orphan")
    verification_records: Mapped[List["VerificationRecord"]] = relationship("VerificationRecord", back_populates="contact", cascade="all, delete-orphan")
    campaign_recipients: Mapped[List["CampaignRecipient"]] = relationship("CampaignRecipient", back_populates="contact", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_contacts_org_email", "organization_id", "email", unique=True),
    )


class SourceCategory(str, enum.Enum):
    GITHUB_README = "GITHUB_README"
    CONTRIBUTING_GUIDE = "CONTRIBUTING_GUIDE"
    SECURITY_POLICY = "SECURITY_POLICY"
    OFFICIAL_WEBSITE = "OFFICIAL_WEBSITE"
    DOCUMENTATION = "DOCUMENTATION"
    ORGANIZATION_PAGE = "ORGANIZATION_PAGE"


class ContactSource(Base, TimestampMixin):
    __tablename__ = "contact_sources"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    contact_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("contacts.id", ondelete="CASCADE"), index=True, nullable=False)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    source_category: Mapped[SourceCategory] = mapped_column(
        Enum(SourceCategory, name="source_category", native_enum=False),
        nullable=False
    )
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    contact: Mapped["Contact"] = relationship("Contact", back_populates="sources")


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DiscoveryJob(Base, TimestampMixin):
    __tablename__ = "discovery_jobs"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    target_query: Mapped[str] = mapped_column(String(512), nullable=False)
    job_type: Mapped[str] = mapped_column(String(64), default="GITHUB_SEARCH", nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status", native_enum=False),
        default=JobStatus.PENDING,
        nullable=False
    )
    projects_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contacts_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class VerificationRecord(Base, TimestampMixin):
    __tablename__ = "verification_records"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    contact_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("contacts.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status", native_enum=False),
        nullable=False
    )
    mx_records: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

    contact: Mapped["Contact"] = relationship("Contact", back_populates="verification_records")


class SuppressionReason(str, enum.Enum):
    OPT_OUT = "OPT_OUT"
    BOUNCE = "BOUNCE"
    COMPLAINT = "COMPLAINT"
    MANUAL = "MANUAL"


class SuppressionEntry(Base, TimestampMixin):
    __tablename__ = "suppression_entries"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    reason: Mapped[SuppressionReason] = mapped_column(
        Enum(SuppressionReason, name="suppression_reason", native_enum=False),
        default=SuppressionReason.MANUAL,
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_suppression_org_email", "organization_id", "email", unique=True),
    )


class EmailTemplate(Base, TimestampMixin):
    __tablename__ = "email_templates"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(512), nullable=False)
    body_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    body_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    variables: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="templates")
    campaigns: Mapped[List["Campaign"]] = relationship("Campaign", back_populates="template")


class CampaignStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    RECIPIENT_REVIEW = "RECIPIENT_REVIEW"
    APPROVED = "APPROVED"
    SCHEDULED = "SCHEDULED"
    SENDING = "SENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID, ForeignKey("email_templates.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, name="campaign_status", native_enum=False),
        default=CampaignStatus.DRAFT,
        nullable=False
    )
    scheduled_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    daily_limit: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    sent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    approved_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="campaigns")
    template: Mapped[Optional["EmailTemplate"]] = relationship("EmailTemplate", back_populates="campaigns")
    recipients: Mapped[List["CampaignRecipient"]] = relationship("CampaignRecipient", back_populates="campaign", cascade="all, delete-orphan")


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DeliveryStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    BOUNCED = "BOUNCED"
    FAILED = "FAILED"
    SUPPRESSED = "SUPPRESSED"


class CampaignRecipient(Base, TimestampMixin):
    __tablename__ = "campaign_recipients"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("campaigns.id", ondelete="CASCADE"), index=True, nullable=False)
    contact_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("contacts.id", ondelete="CASCADE"), index=True, nullable=False)
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, name="approval_status", native_enum=False),
        default=ApprovalStatus.PENDING,
        nullable=False
    )
    delivery_status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus, name="delivery_status", native_enum=False),
        default=DeliveryStatus.PENDING,
        nullable=False
    )
    personalized_subject: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    personalized_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="recipients")
    contact: Mapped["Contact"] = relationship("Contact", back_populates="campaign_recipients")
    events: Mapped[List["MessageEvent"]] = relationship("MessageEvent", back_populates="recipient", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_campaign_contact_unique", "campaign_id", "contact_id", unique=True),
    )


class MessageEventType(str, enum.Enum):
    SENT = "SENT"
    BOUNCED = "BOUNCED"
    REPLIED = "REPLIED"
    OPT_OUT = "OPT_OUT"


class MessageEvent(Base, TimestampMixin):
    __tablename__ = "message_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    campaign_recipient_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("campaign_recipients.id", ondelete="CASCADE"), index=True, nullable=False)
    event_type: Mapped[MessageEventType] = mapped_column(
        Enum(MessageEventType, name="message_event_type", native_enum=False),
        nullable=False
    )
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    recipient: Mapped["CampaignRecipient"] = relationship("CampaignRecipient", back_populates="events")


class ConnectedAccount(Base, TimestampMixin):
    __tablename__ = "connected_accounts"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)  # GITHUB, SMTP, SANDBOX
    encrypted_credentials: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID, nullable=True)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID, nullable=True)
    action: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
