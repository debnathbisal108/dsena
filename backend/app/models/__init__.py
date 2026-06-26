import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Boolean, Text, Integer, Float, ForeignKey,
    DateTime, UniqueConstraint, CheckConstraint, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def utcnow(): return datetime.now(timezone.utc)
def new_uuid(): return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(Text)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    verification_token: Mapped[str | None] = mapped_column(String(255))
    reset_token: Mapped[str | None] = mapped_column(String(255))
    reset_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    organizations: Mapped[list["Organization"]] = relationship(back_populates="owner")


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    owner_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Business context
    description: Mapped[str | None] = mapped_column(Text)
    services: Mapped[str | None] = mapped_column(Text)
    target_customer: Mapped[str | None] = mapped_column(Text)
    pricing_guidance: Mapped[str | None] = mapped_column(Text)
    faqs: Mapped[str | None] = mapped_column(Text)
    business_rules: Mapped[str | None] = mapped_column(Text)
    website_url: Mapped[str | None] = mapped_column(Text)

    # AI policy
    ai_tone: Mapped[str] = mapped_column(String(50), default="professional")
    max_followup_attempts: Mapped[int] = mapped_column(Integer, default=5)
    allowed_hours_start: Mapped[int] = mapped_column(Integer, default=8)
    allowed_hours_end: Mapped[int] = mapped_column(Integer, default=18)
    allowed_timezone: Mapped[str] = mapped_column(String(100), default="UTC")

    # Email integration
    email_provider: Mapped[str | None] = mapped_column(String(50))
    email_access_token: Mapped[str | None] = mapped_column(Text)
    email_refresh_token: Mapped[str | None] = mapped_column(Text)
    email_token_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sending_email: Mapped[str | None] = mapped_column(String(255))

    # Onboarding state
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    onboarding_step: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    owner: Mapped["User"] = relationship(back_populates="organizations")
    leads: Mapped[list["Lead"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    knowledge_chunks: Mapped[list["KnowledgeChunk"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    knowledge_documents: Mapped[list["KnowledgeDocument"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    crawl_jobs: Mapped[list["CrawlJob"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    ai_actions: Mapped[list["AIAction"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    calendar_integration: Mapped["CalendarIntegration | None"] = relationship(back_populates="organization", uselist=False, cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # website|pdf|faq|manual
    source_url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list | None] = mapped_column(JSON)  # float array
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    organization: Mapped["Organization"] = relationship(back_populates="knowledge_chunks")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="processing")
    chunks_created: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    organization: Mapped["Organization"] = relationship(back_populates="knowledge_documents")


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending|running|done|failed
    pages_found: Mapped[int] = mapped_column(Integer, default=0)
    chunks_created: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    organization: Mapped["Organization"] = relationship(back_populates="crawl_jobs")


class Lead(Base):
    __tablename__ = "leads"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    # Identity
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    company: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(Text)

    # Submission
    message: Mapped[str | None] = mapped_column(Text)
    custom_fields: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    utm_source: Mapped[str | None] = mapped_column(String(100))
    utm_medium: Mapped[str | None] = mapped_column(String(100))
    utm_campaign: Mapped[str | None] = mapped_column(String(100))
    ip_address: Mapped[str | None] = mapped_column(String(45))

    # AI Intelligence — updated continuously
    intent_score: Mapped[int] = mapped_column(Integer, default=0)
    urgency_score: Mapped[int] = mapped_column(Integer, default=0)
    buying_probability: Mapped[int] = mapped_column(Integer, default=0)
    estimated_deal_value: Mapped[float | None] = mapped_column(Float)
    sentiment: Mapped[str | None] = mapped_column(String(50))
    detected_objections: Mapped[list | None] = mapped_column(JSONB, default=list)
    qualification_summary: Mapped[str | None] = mapped_column(Text)
    recommended_action: Mapped[str | None] = mapped_column(Text)
    risk_factors: Mapped[list | None] = mapped_column(JSONB, default=list)
    spam_risk_score: Mapped[int] = mapped_column(Integer, default=0)

    # State
    status: Mapped[str] = mapped_column(String(50), default="new")
    followup_count: Mapped[int] = mapped_column(Integer, default=0)
    last_ai_action: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stop_reason: Mapped[str | None] = mapped_column(Text)
    human_takeover: Mapped[bool] = mapped_column(Boolean, default=False)

    # Email threading
    email_thread_id: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    organization: Mapped["Organization"] = relationship(back_populates="leads")
    conversation: Mapped["Conversation | None"] = relationship(back_populates="lead", uselist=False, cascade="all, delete-orphan")
    meetings: Mapped[list["Meeting"]] = relationship(back_populates="lead", cascade="all, delete-orphan")
    ai_actions: Mapped[list["AIAction"]] = relationship(back_populates="lead", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_leads_org_status", "org_id", "status"),
        Index("idx_leads_next_action", "next_action_at"),
    )


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    lead_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, unique=True)
    thread_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    lead: Mapped["Lead"] = relationship(back_populates="conversation")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    conversation_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # lead|ai|human_agent
    content: Mapped[str] = mapped_column(Text, nullable=False)
    email_message_id: Mapped[str | None] = mapped_column(String(255))
    sent_via: Mapped[str | None] = mapped_column(String(50), default="email")
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class AIAction(Base):
    __tablename__ = "ai_actions"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    lead_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    reasoning: Mapped[str | None] = mapped_column(Text)
    response_content: Mapped[str | None] = mapped_column(Text)
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    model_used: Mapped[str | None] = mapped_column(String(100))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    lead: Mapped["Lead"] = relationship(back_populates="ai_actions")
    organization: Mapped["Organization"] = relationship(back_populates="ai_actions")

    __table_args__ = (Index("idx_ai_actions_org_created", "org_id", "created_at"),)


class Meeting(Base):
    __tablename__ = "meetings"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    lead_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    google_event_id: Mapped[str | None] = mapped_column(String(255))
    meet_link: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="confirmed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    lead: Mapped["Lead"] = relationship(back_populates="meetings")


class CalendarIntegration(Base):
    __tablename__ = "calendar_integrations"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True)
    google_access_token: Mapped[str] = mapped_column(Text, nullable=False)
    google_refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    calendar_id: Mapped[str] = mapped_column(String(255), default="primary")
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    organization: Mapped["Organization"] = relationship(back_populates="calendar_integration")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id", ondelete="SET NULL"))
    user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    metadata: Mapped[dict | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
