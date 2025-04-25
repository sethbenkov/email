import os
from datetime import datetime, time, timedelta, timezone

# --- Configuration Constants ---

# Target timezone for the email (e.g., 'America/New_York' for ET)
TARGET_TIMEZONE = 'America/New_York' # PRD specifies ET

# Google API Scopes
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send' # Added scope for sending email
]
GOOGLE_CREDENTIALS_FILE = 'credentials.json'
GOOGLE_TOKEN_FILE = 'token.json'

# Email Fetching
GMAIL_QUERY = 'newer_than:1d in:inbox -label:trash' # Last 24 hours, inbox, not trash
MAX_EMAILS_TO_PROCESS = 50 # Limit number of emails processed

# OneNote Local Parsing
ONENOTE_EXPORT_FOLDER_ENV_VAR = 'ONENOTE_EXPORT_FOLDER' # Environment variable name
ONENOTE_DONE_MARKER = "DONE"

# Zoom Parsing
ZOOM_SUMMARY_FOLDER_ENV_VAR = 'ZOOM_SUMMARY_FOLDER' # Environment variable name
ZOOM_RECAP_ID = 'quick-recap'
ZOOM_NEXT_STEPS_ID = 'next-steps'
ZOOM_SUMMARY_ID = 'summary'

# OpenAI API Key
OPENAI_API_KEY_ENV_VAR = 'OPENAI_API_KEY' # Environment variable name

# Email Sending
RECIPIENT_EMAIL_ENV_VAR = 'RECIPIENT_EMAIL' # Environment variable name for recipient

# Output Files
LOCAL_OUTPUT_HTML_FILE = 'daily_brief_local_output.html'

# --- Environment Variable Loading (Handled in specific modules) ---
# ONENOTE_EXPORT_FOLDER and ZOOM_SUMMARY_FOLDER
# are loaded from .env using python-dotenv where needed. 