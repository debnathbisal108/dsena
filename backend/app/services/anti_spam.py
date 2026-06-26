"""
Anti-spam engine. Protects email reputation and prevents over-outreach.
Returns a spam risk score 0-100. >= 80 = stop outreach.
"""
from datetime import datetime, timezone
from app.models import Lead, Organization


def _days_since(dt: datetime | None) -> int:
    if not dt:
        return 0
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0, (now - dt).days)


UNSUBSCRIBE_SIGNALS = [
    "unsubscribe", "stop emailing", "remove me", "don't contact",
    "do not contact", "not interested", "leave me alone", "opt out",
    "stop sending", "take me off"
]


def _check_unsubscribe(lead: Lead) -> bool:
    """Check if any lead message contains unsubscribe signals."""
    if not lead.conversation:
        return False
    for msg in lead.conversation.messages:
        if msg.role == "lead":
            content_lower = msg.content.lower()
            if any(signal in content_lower for signal in UNSUBSCRIBE_SIGNALS):
                return True
    return False


def calculate_spam_risk(lead: Lead, org: Organization) -> int:
    """
    Returns 0-100 spam risk score.
    >= 80: stop outreach
    >= 60: reduce frequency
    < 60: safe to continue
    """
    risk = 0

    # 1. Exceeded max followup attempts (+50)
    if lead.followup_count >= org.max_followup_attempts:
        risk += 50

    # 2. Unsubscribe signal detected (+100 — immediate stop)
    if _check_unsubscribe(lead):
        return 100

    # 3. Negative sentiment consistently (+20)
    if lead.sentiment == "negative":
        risk += 20

    # 4. Very low intent after multiple attempts (+15)
    if lead.intent_score < 20 and lead.followup_count >= 2:
        risk += 15

    # 5. Too many days without engagement (+10)
    days = _days_since(lead.created_at)
    if days > 21 and lead.followup_count >= 3:
        risk += 10

    # 6. Already flagged high spam risk previously (+existing)
    risk = max(risk, lead.spam_risk_score // 2)

    return min(100, risk)


def should_send_during_hours(org: Organization) -> bool:
    """Check if current time is within org's allowed sending hours."""
    import pytz
    try:
        tz = pytz.timezone(org.allowed_timezone)
        now_local = datetime.now(tz)
        hour = now_local.hour
        return org.allowed_hours_start <= hour < org.allowed_hours_end
    except Exception:
        # Default: allow if timezone lookup fails
        return True
