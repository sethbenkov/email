import os
import pickle
from datetime import datetime, time, timedelta, timezone

import pytz # Use pytz for robust timezone handling
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

import config

def get_google_service(api_name, api_version, scopes, credentials_file, token_file):
    """Authenticates and builds a Google API service object."""
    creds = None
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing Google API token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {e}. Deleting token and re-authenticating.")
                # Attempt to remove token file only if it exists
                if os.path.exists(token_file):
                    try:
                        os.remove(token_file)
                    except OSError as ose:
                         print(f"Error removing token file {token_file} during refresh error: {ose}")
                creds = None # Force re-authentication
        else:
            print("Google credentials not found or invalid. Starting auth flow...")
            if not os.path.exists(credentials_file):
                raise FileNotFoundError(f"Credentials file not found: {credentials_file}. Please download it from Google Cloud Console.")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
            # Specify host='localhost' and port=0 to let the library find an available port
            creds = flow.run_local_server(host='localhost', port=0)

        # Save the credentials for the next run only if valid creds were obtained
        if creds:
             with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
                print(f"Google credentials saved to {token_file}")
        else:
             print("Could not obtain valid Google credentials.")
             # Avoid building service if creds are None
             raise ConnectionError("Failed to obtain Google credentials.")


    try:
        service = build(api_name, api_version, credentials=creds)
        print(f"Successfully connected to Google {api_name.capitalize()} API.")
        return service
    except Exception as e:
        print(f"Error building Google {api_name.capitalize()} service: {e}")
        # Attempt to delete potentially corrupted token file
        if os.path.exists(token_file):
            try:
                os.remove(token_file)
                print(f"Removed potentially corrupted token file: {token_file}")
            except OSError as ose:
                print(f"Error removing token file {token_file}: {ose}")
        raise

def get_localized_time_range(target_tz_name):
    """Returns the start and end of today in the target timezone (ISO format)."""
    try:
        target_tz = pytz.timezone(target_tz_name)
    except pytz.UnknownTimeZoneError:
        print(f"Error: Unknown timezone '{target_tz_name}'. Using UTC.")
        target_tz = pytz.utc

    now_local = datetime.now(target_tz)
    start_of_day_local = target_tz.localize(datetime.combine(now_local.date(), time.min))
    end_of_day_local = target_tz.localize(datetime.combine(now_local.date(), time.max))

    # Convert to UTC ISO format for Google API
    start_of_day_utc = start_of_day_local.astimezone(pytz.utc).isoformat()
    end_of_day_utc = end_of_day_local.astimezone(pytz.utc).isoformat()

    return start_of_day_utc, end_of_day_utc

def get_yesterday_date():
    """Returns the date for yesterday."""
    return datetime.now().date() - timedelta(days=1) 