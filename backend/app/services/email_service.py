import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)
RESEND_API_URL = "https://api.resend.com/emails"


async def _send(to: str, subject: str, html: str) -> None:
    if not settings.RESEND_API_KEY:
        logger.warning(f"RESEND_API_KEY not set — skipping email to {to}")
        logger.info(f"[EMAIL PREVIEW] To: {to} | Subject: {subject}")
        return
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                RESEND_API_URL,
                headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}", "Content-Type": "application/json"},
                json={"from": settings.RESEND_FROM_EMAIL, "to": [to], "subject": subject, "html": html},
            )
            r.raise_for_status()
    except Exception as e:
        logger.error(f"Email send failed to {to}: {e}")
        raise


async def send_verification_email(to_email: str, full_name: str, token: str) -> None:
    url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    await _send(to_email, "Verify your email", f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
    <h2>Welcome, {full_name}!</h2>
    <p>Click below to verify your email and activate your account.</p>
    <p><a href="{url}" style="background:#6366f1;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none;display:inline-block;">Verify Email</a></p>
    <p style="color:#9ca3af;font-size:12px">Link expires in 24 hours.</p>
    </div>""")


async def send_password_reset_email(to_email: str, full_name: str, token: str) -> None:
    url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    await _send(to_email, "Reset your password", f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
    <h2>Password Reset</h2>
    <p>Hi {full_name},</p>
    <p><a href="{url}" style="background:#6366f1;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none;display:inline-block;">Reset Password</a></p>
    <p style="color:#9ca3af;font-size:12px">Expires in 1 hour.</p>
    </div>""")


async def send_lead_email(to_email: str, lead_name: str, subject: str, body: str, from_business: str) -> None:
    await _send(to_email, subject, f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px;line-height:1.6">
    <p>{body.replace(chr(10), "<br>")}</p>
    <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0">
    <p style="color:#9ca3af;font-size:12px">Sent on behalf of {from_business}.</p>
    </div>""")


async def send_meeting_confirmation(to_email: str, lead_name: str, business_name: str, starts_at: str, meet_link: str) -> None:
    meet_btn = f'<p><a href="{meet_link}" style="background:#6366f1;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;display:inline-block;">Join Google Meet</a></p>' if meet_link else ""
    await _send(to_email, f"Meeting confirmed with {business_name}", f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
    <h2>Meeting confirmed!</h2>
    <p>Hi {lead_name}, your discovery call with <strong>{business_name}</strong> is set for:</p>
    <p style="font-size:20px;font-weight:bold;color:#6366f1">{starts_at}</p>
    {meet_btn}
    </div>""")


async def send_owner_meeting_notification(to_email: str, lead_name: str, lead_email: str, company: str, starts_at: str, meet_link: str) -> None:
    meet_html = f'<p><a href="{meet_link}">{meet_link}</a></p>' if meet_link else ""
    await _send(to_email, f"🎉 Meeting booked: {lead_name}", f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
    <h2>New meeting booked by AI!</h2>
    <p><strong>Lead:</strong> {lead_name} ({lead_email})</p>
    <p><strong>Company:</strong> {company or "N/A"}</p>
    <p><strong>Time:</strong> {starts_at}</p>
    {meet_html}
    </div>""")


async def send_human_escalation_alert(to_email: str, lead_name: str, lead_email: str, reasoning: str) -> None:
    await _send(to_email, f"⚠️ Lead needs your attention: {lead_name}", f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
    <h2>A lead needs human attention</h2>
    <p><strong>Lead:</strong> {lead_name} ({lead_email})</p>
    <p><strong>AI reasoning:</strong> {reasoning}</p>
    <p>Log in to your dashboard to handle this lead manually.</p>
    </div>""")
