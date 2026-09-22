"""
Google Meet Integration via Google Calendar API
================================================
Creates Google Calendar events with Meet conference links for video consultations.

Setup (one-time):
1. Place your OAuth2 credentials.json in the project root
2. Run:  python google_meet.py
3. Complete the browser OAuth flow
4. token.json is saved — the app uses it from then on
"""

import os
import sys
import json
import datetime
from typing import Optional, Dict, Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import google_config


def get_credentials():  # Returns Optional[Credentials]
    """
    Load or refresh Google OAuth2 credentials.
    Returns None if credentials are not available.
    """
    creds = None

    # Load saved token
    if os.path.exists(google_config.TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(
                google_config.TOKEN_FILE,
                google_config.SCOPES
            )
        except Exception:
            creds = None

    # Refresh or re-auth
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Save refreshed token
            with open(google_config.TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
        except Exception:
            creds = None

    # First-time auth (interactive)
    if not creds or not creds.valid:
        if not os.path.exists(google_config.CREDENTIALS_FILE):
            print(f"[Google Meet] No credentials.json found at {google_config.CREDENTIALS_FILE}")
            print("[Google Meet] Follow setup instructions in google_config.py")
            return None

        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                google_config.CREDENTIALS_FILE,
                google_config.SCOPES
            )
            creds = flow.run_local_server(port=0)
            # Save token
            with open(google_config.TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
            print("[Google Meet] Authentication successful. Token saved.")
        except Exception as e:
            print(f"[Google Meet] Auth failed: {e}")
            return None

    return creds


def create_meet_event(
    summary: str,
    description: str,
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    attendee_emails: list[str],
    timezone: str = "Asia/Kolkata"
) -> Optional[Dict[str, Any]]:
    """
    Create a Google Calendar event with a Google Meet conference link.

    Args:
        summary: Event title (e.g. "Video Consultation - Dr. Smith & John Doe")
        description: Event description with appointment details
        start_time: Event start (datetime, will be converted to RFC3339)
        end_time: Event end
        attendee_emails: List of email addresses to invite
        timezone: IANA timezone string

    Returns:
        dict with {meet_link, event_id, html_link} or None on failure
    """
    creds = get_credentials()
    if not creds:
        return None

    try:
        service = build("calendar", "v3", credentials=creds)

        # Format datetimes to RFC3339
        def to_rfc3339(dt: datetime.datetime) -> str:
            if dt.tzinfo is None:
                # Assume IST if naive
                import pytz
                ist = pytz.timezone(timezone)
                dt = ist.localize(dt)
            return dt.isoformat()

        # Build attendees list
        attendees = [{"email": email} for email in attendee_emails]

        # Create event with Google Meet conference
        event_body = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": to_rfc3339(start_time),
                "timeZone": timezone,
            },
            "end": {
                "dateTime": to_rfc3339(end_time),
                "timeZone": timezone,
            },
            "attendees": attendees,
            "conferenceData": {
                "createRequest": {
                    "requestId": f"medipure-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}",
                    "conferenceSolutionKey": {
                        "type": "hangoutsMeet"
                    }
                }
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 10},
                    {"method": "email", "minutes": 30}
                ]
            },
            "guestsCanModify": False,
            "guestsCanSeeOtherGuests": True
        }

        event = service.events().insert(
            calendarId="primary",
            body=event_body,
            conferenceDataVersion=1,
            sendUpdates="all"  # Send email invites to attendees
        ).execute()

        # Extract Meet link
        meet_link = None
        conference_data = event.get("conferenceData", {})
        if conference_data:
            entry_points = conference_data.get("entryPoints", [])
            for ep in entry_points:
                if ep.get("entryPointType") == "video":
                    meet_link = ep.get("uri")
                    break
            # Fallback: use hangoutLink
            if not meet_link:
                meet_link = event.get("hangoutLink")

        result = {
            "meet_link": meet_link,
            "event_id": event.get("id"),
            "html_link": event.get("htmlLink"),
            "start_time": event.get("start", {}).get("dateTime"),
            "end_time": event.get("end", {}).get("dateTime"),
        }

        print(f"[Google Meet] Event created: {meet_link}")
        return result

    except HttpError as e:
        print(f"[Google Meet] API error: {e}")
        return None
    except Exception as e:
        print(f"[Google Meet] Error creating event: {e}")
        return None


def delete_meet_event(event_id: str) -> bool:
    """Delete a Google Calendar event (e.g., when appointment is cancelled)."""
    creds = get_credentials()
    if not creds:
        return False

    try:
        service = build("calendar", "v3", credentials=creds)
        service.events().delete(
            calendarId="primary",
            eventId=event_id,
            sendUpdates="all"
        ).execute()
        print(f"[Google Meet] Event {event_id} deleted")
        return True
    except Exception as e:
        print(f"[Google Meet] Error deleting event: {e}")
        return False


# --- CLI: Run one-time OAuth flow ---
if __name__ == "__main__":
    print("=" * 50)
    print("Google Meet Integration - Setup")
    print("=" * 50)
    creds = get_credentials()
    if creds:
        print("\n✅ Authentication successful!")
        print(f"Token saved to: {google_config.TOKEN_FILE}")

        # Quick test: list next 3 calendar events
        try:
            service = build("calendar", "v3", credentials=creds)
            now = datetime.datetime.utcnow().isoformat() + "Z"
            events_result = service.events().list(
                calendarId="primary",
                timeMin=now,
                maxResults=3,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            events = events_result.get("items", [])
            if events:
                print(f"\n📅 Upcoming events ({len(events)}):")
                for ev in events:
                    start = ev["start"].get("dateTime", ev["start"].get("date"))
                    print(f"  - {start}: {ev.get('summary', '(no title)')}")
            else:
                print("\n📅 No upcoming events found.")
        except Exception as e:
            print(f"\n⚠️  Could not list events: {e}")
    else:
        print("\n❌ Authentication failed.")
        print(f"Make sure credentials.json exists at: {google_config.CREDENTIALS_FILE}")
        sys.exit(1)
