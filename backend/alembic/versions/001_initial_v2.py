"""Initial schema v2

Revision ID: 001_initial_v2
Revises:
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "001_initial_v2"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table("users",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.Text),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("is_verified", sa.Boolean, nullable=False, default=False),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("google_id", sa.String(255), unique=True),
        sa.Column("avatar_url", sa.Text),
        sa.Column("verification_token", sa.String(255)),
        sa.Column("reset_token", sa.String(255)),
        sa.Column("reset_token_expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table("organizations",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("owner_id", UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("services", sa.Text),
        sa.Column("target_customer", sa.Text),
        sa.Column("pricing_guidance", sa.Text),
        sa.Column("faqs", sa.Text),
        sa.Column("business_rules", sa.Text),
        sa.Column("website_url", sa.Text),
        sa.Column("ai_tone", sa.String(50), default="professional"),
        sa.Column("max_followup_attempts", sa.Integer, default=5),
        sa.Column("allowed_hours_start", sa.Integer, default=8),
        sa.Column("allowed_hours_end", sa.Integer, default=18),
        sa.Column("allowed_timezone", sa.String(100), default="UTC"),
        sa.Column("email_provider", sa.String(50)),
        sa.Column("email_access_token", sa.Text),
        sa.Column("email_refresh_token", sa.Text),
        sa.Column("email_token_expires", sa.DateTime(timezone=True)),
        sa.Column("sending_email", sa.String(255)),
        sa.Column("onboarding_complete", sa.Boolean, default=False),
        sa.Column("onboarding_step", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table("knowledge_chunks",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("org_id", UUID(as_uuid=False), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_url", sa.Text),
        sa.Column("title", sa.Text),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", sa.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_chunks_org", "knowledge_chunks", ["org_id"])

    op.create_table("knowledge_documents",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("org_id", UUID(as_uuid=False), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(50)),
        sa.Column("status", sa.String(50), default="processing"),
        sa.Column("chunks_created", sa.Integer, default=0),
        sa.Column("error", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table("crawl_jobs",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("org_id", UUID(as_uuid=False), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("status", sa.String(50), default="pending"),
        sa.Column("pages_found", sa.Integer, default=0),
        sa.Column("chunks_created", sa.Integer, default=0),
        sa.Column("error", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    op.create_table("leads",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("org_id", UUID(as_uuid=False), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("phone", sa.String(50)),
        sa.Column("company", sa.String(255)),
        sa.Column("role", sa.String(255)),
        sa.Column("website", sa.Text),
        sa.Column("message", sa.Text),
        sa.Column("custom_fields", JSONB, default=dict),
        sa.Column("utm_source", sa.String(100)),
        sa.Column("utm_medium", sa.String(100)),
        sa.Column("utm_campaign", sa.String(100)),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("intent_score", sa.Integer, default=0),
        sa.Column("urgency_score", sa.Integer, default=0),
        sa.Column("buying_probability", sa.Integer, default=0),
        sa.Column("estimated_deal_value", sa.Float),
        sa.Column("sentiment", sa.String(50)),
        sa.Column("detected_objections", JSONB, default=list),
        sa.Column("qualification_summary", sa.Text),
        sa.Column("recommended_action", sa.Text),
        sa.Column("risk_factors", JSONB, default=list),
        sa.Column("spam_risk_score", sa.Integer, default=0),
        sa.Column("status", sa.String(50), default="new"),
        sa.Column("followup_count", sa.Integer, default=0),
        sa.Column("last_ai_action", sa.DateTime(timezone=True)),
        sa.Column("next_action_at", sa.DateTime(timezone=True)),
        sa.Column("stop_reason", sa.Text),
        sa.Column("human_takeover", sa.Boolean, default=False),
        sa.Column("email_thread_id", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_leads_org_status", "leads", ["org_id", "status"])
    op.create_index("idx_leads_next_action", "leads", ["next_action_at"])

    op.create_table("conversations",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("lead_id", UUID(as_uuid=False), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("thread_id", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table("messages",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("conversation_id", UUID(as_uuid=False), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("email_message_id", sa.String(255)),
        sa.Column("sent_via", sa.String(50), default="email"),
        sa.Column("opened_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_messages_conv", "messages", ["conversation_id", "created_at"])

    op.create_table("ai_actions",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("lead_id", UUID(as_uuid=False), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("org_id", UUID(as_uuid=False), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("reasoning", sa.Text),
        sa.Column("response_content", sa.Text),
        sa.Column("tokens_used", sa.Integer),
        sa.Column("model_used", sa.String(100)),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_ai_actions_org_created", "ai_actions", ["org_id", "created_at"])

    op.create_table("meetings",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("lead_id", UUID(as_uuid=False), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("org_id", UUID(as_uuid=False), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("google_event_id", sa.String(255)),
        sa.Column("meet_link", sa.Text),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), default="confirmed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table("calendar_integrations",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("org_id", UUID(as_uuid=False), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("google_access_token", sa.Text, nullable=False),
        sa.Column("google_refresh_token", sa.Text, nullable=False),
        sa.Column("calendar_id", sa.String(255), default="primary"),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table("audit_logs",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("org_id", UUID(as_uuid=False), sa.ForeignKey("organizations.id", ondelete="SET NULL")),
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50)),
        sa.Column("entity_id", UUID(as_uuid=False)),
        sa.Column("metadata", JSONB),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    for t in ["audit_logs", "calendar_integrations", "meetings", "ai_actions",
              "messages", "conversations", "leads", "crawl_jobs",
              "knowledge_documents", "knowledge_chunks", "organizations", "users"]:
        op.drop_table(t)
