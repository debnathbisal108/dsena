from datetime import datetime, timedelta, timezone
from typing import List
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from app.core.config import settings
from app.models import CalendarIntegration

SCOPES = ["https://www.googleapis.com/auth/calendar", "openid", "https://www.googleapis.com/auth/userinfo.email"]


def get_auth_url(state: str) -> str:
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_config(
        {"web": {"client_id": settings.GOOGLE_CLIENT_ID, "client_secret": settings.GOOGLE_CLIENT_SECRET,
                 "redirect_uris": [settings.google_calendar_redirect_uri],
                 "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                 "token_uri": "https://oauth2.googleapis.com/token"}},
        scopes=SCOPES, redirect_uri=settings.google_calendar_redirect_uri,
    )
    auth_url, _ = flow.authorization_url(access_type="offline", state=state, prompt="consent")
    return auth_url


def exchange_code(code: str) -> dict:
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_config(
        {"web": {"client_id": settings.GOOGLE_CLIENT_ID, "client_secret": settings.GOOGLE_CLIENT_SECRET,
                 "redirect_uris": [settings.google_calendar_redirect_uri],
                 "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                 "token_uri": "https://oauth2.googleapis.com/token"}},
        scopes=SCOPES, redirect_uri=settings.google_calendar_redirect_uri,
    )
    flow.fetch_token(code=code)
    creds = flow.credentials
    return {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_expires_at": creds.expiry or (datetime.now(timezone.utc) + timedelta(hours=1)),
    }


def _creds(integration: CalendarIntegration) -> Credentials:
    creds = Credentials(
        token=integration.google_access_token,
        refresh_token=integration.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def get_available_slots(integration: CalendarIntegration, date: datetime, duration_minutes: int = 30) -> List[dict]:
    service = build("calendar", "v3", credentials=_creds(integration), cache_discovery=False)
    day_start = date.replace(hour=9, minute=0, second=0, microsecond=0)
    day_end = date.replace(hour=17, minute=0, second=0, microsecond=0)
    freebusy = service.freebusy().query(body={
        "timeMin": day_start.isoformat(), "timeMax": day_end.isoformat(),
        "items": [{"id": integration.calendar_id}],
    }).execute()
    busy = [(datetime.fromisoformat(b["start"]), datetime.fromisoformat(b["end"]))
            for b in freebusy["calendars"].get(integration.calendar_id, {}).get("busy", [])]
    slots, cur = [], day_start
    while cur + timedelta(minutes=duration_minutes) <= day_end:
        end = cur + timedelta(minutes=duration_minutes)
        if not any(not (end <= bs or cur >= be) for bs, be in busy):
            slots.append({"starts_at": cur.isoformat(), "ends_at": end.isoformat()})
        cur = end
    return slots


def create_event(integration: CalendarIntegration, title: str, starts_at: datetime,
                 ends_at: datetime, attendee_email: str, attendee_name: str, description: str = "") -> dict:
    service = build("calendar", "v3", credentials=_creds(integration), cache_discovery=False)
    event = service.events().insert(
        calendarId=integration.calendar_id,
        body={"summary": title, "description": description,
              "start": {"dateTime": starts_at.isoformat(), "timeZone": "UTC"},
              "end": {"dateTime": ends_at.isoformat(), "timeZone": "UTC"},
              "attendees": [{"email": attendee_email, "displayName": attendee_name}],
              "conferenceData": {"createRequest": {"requestId": f"meet-{attendee_email}-{int(starts_at.timestamp())}"}}},
        conferenceDataVersion=1, sendUpdates="all",
    ).execute()
    meet_link = next((ep["uri"] for ep in event.get("conferenceData", {}).get("entryPoints", [])
                      if ep.get("entryPointType") == "video"), "")
    return {"event_id": event["id"], "meet_link": meet_link}
