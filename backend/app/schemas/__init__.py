from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Any
from datetime import datetime
import re


# ── Auth ───────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    is_verified: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    class Config: from_attributes = True


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ── Onboarding ─────────────────────────────────────────
class BusinessInfoRequest(BaseModel):
    name: str
    slug: str
    description: str
    services: str
    target_customer: str
    pricing_guidance: Optional[str] = None
    faqs: Optional[str] = None
    business_rules: Optional[str] = None
    website_url: Optional[str] = None

    @field_validator("slug")
    @classmethod
    def slug_valid(cls, v):
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Slug must be lowercase alphanumeric with hyphens")
        return v


class AIPolicyRequest(BaseModel):
    ai_tone: str = "professional"
    max_followup_attempts: int = 5
    allowed_hours_start: int = 8
    allowed_hours_end: int = 18
    allowed_timezone: str = "UTC"


class CrawlRequest(BaseModel):
    url: str


# ── Organization ───────────────────────────────────────
class OrgOut(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    services: Optional[str] = None
    target_customer: Optional[str] = None
    pricing_guidance: Optional[str] = None
    faqs: Optional[str] = None
    business_rules: Optional[str] = None
    website_url: Optional[str] = None
    ai_tone: str
    max_followup_attempts: int
    allowed_hours_start: int
    allowed_hours_end: int
    allowed_timezone: str
    onboarding_complete: bool
    onboarding_step: int
    created_at: datetime
    class Config: from_attributes = True


# ── Knowledge ──────────────────────────────────────────
class KnowledgeChunkOut(BaseModel):
    id: str
    source_type: str
    source_url: Optional[str] = None
    title: Optional[str] = None
    content: str
    created_at: datetime
    class Config: from_attributes = True


class KnowledgeDocumentOut(BaseModel):
    id: str
    filename: str
    file_type: Optional[str] = None
    status: str
    chunks_created: int
    created_at: datetime
    class Config: from_attributes = True


class CrawlJobOut(BaseModel):
    id: str
    url: str
    status: str
    pages_found: int
    chunks_created: int
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    class Config: from_attributes = True


class AddManualKnowledgeRequest(BaseModel):
    title: str
    content: str


# ── Leads ──────────────────────────────────────────────
class LeadSubmitRequest(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    message: Optional[str] = None
    custom_fields: Optional[dict] = {}
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    sent_via: Optional[str] = None
    opened_at: Optional[datetime] = None
    created_at: datetime
    class Config: from_attributes = True


class ConversationOut(BaseModel):
    id: str
    messages: List[MessageOut] = []
    created_at: datetime
    class Config: from_attributes = True


class AIActionOut(BaseModel):
    id: str
    action_type: str
    reasoning: Optional[str] = None
    response_content: Optional[str] = None
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    created_at: datetime
    class Config: from_attributes = True


class MeetingOut(BaseModel):
    id: str
    meet_link: Optional[str] = None
    starts_at: datetime
    ends_at: datetime
    status: str
    created_at: datetime
    class Config: from_attributes = True


class LeadListItem(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    company: Optional[str] = None
    status: str
    intent_score: int
    urgency_score: int
    buying_probability: int
    sentiment: Optional[str] = None
    followup_count: int
    human_takeover: bool
    next_action_at: Optional[datetime] = None
    created_at: datetime
    class Config: from_attributes = True


class LeadDetail(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    message: Optional[str] = None
    status: str
    intent_score: int
    urgency_score: int
    buying_probability: int
    estimated_deal_value: Optional[float] = None
    sentiment: Optional[str] = None
    detected_objections: Optional[list] = []
    qualification_summary: Optional[str] = None
    recommended_action: Optional[str] = None
    risk_factors: Optional[list] = []
    spam_risk_score: int
    followup_count: int
    human_takeover: bool
    stop_reason: Optional[str] = None
    last_ai_action: Optional[datetime] = None
    next_action_at: Optional[datetime] = None
    utm_source: Optional[str] = None
    conversation: Optional[ConversationOut] = None
    ai_actions: List[AIActionOut] = []
    meetings: List[MeetingOut] = []
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True


class PaginatedLeads(BaseModel):
    items: List[LeadListItem]
    total: int
    page: int
    pages: int


# ── Dashboard ──────────────────────────────────────────
class AIFeedItem(BaseModel):
    id: str
    lead_name: str
    action_type: str
    reasoning: Optional[str] = None
    created_at: datetime


class DashboardMetrics(BaseModel):
    leads_received: int
    leads_contacted: int
    meetings_booked: int
    pipeline_value: float
    conversion_rate: float
    ai_actions_taken: int
    followups_sent: int
    hot_leads: int
    leads_needing_human: int
    avg_response_time_minutes: float
    leads_by_day: List[dict]
    score_distribution: dict


# ── Booking ────────────────────────────────────────────
class SlotOut(BaseModel):
    starts_at: datetime
    ends_at: datetime


class BookSlotRequest(BaseModel):
    lead_id: str
    starts_at: datetime
    ends_at: datetime
