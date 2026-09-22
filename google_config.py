# Google Meet / Calendar API Configuration
# ===========================================
# 1. Go to https://console.cloud.google.com
# 2. Create a project (or use existing)
# 3. Enable "Google Calendar API"
# 4. Create OAuth 2.0 Client ID (Desktop app)
# 5. Download JSON and place as 'credentials.json' in this directory
# 6. Run: python google_meet.py   (to complete one-time OAuth flow)

import os

# Path to OAuth2 credentials JSON (download from Google Cloud Console)
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")

# Path where the OAuth token is stored after first auth
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")

# Google Calendar API scopes
SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar"
]

# Meet link settings
DEFAULT_MEET_DURATION_MINUTES = 30  # Default consultation duration
