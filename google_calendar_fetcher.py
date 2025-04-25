from datetime import datetime
import pytz

from googleapiclient.errors import HttpError

import config
import utils

def format_event_time(event_time_data):
    """Formats Google Calendar event time data into a readable string."""
    # Check for date field (all-day events) first
    if event_time_data.get('date'):
        # No specific time for all-day events
        return "All-day"
    elif event_time_data.get('dateTime'):
        dt_str = event_time_data['dateTime']
        dt_utc = datetime.fromisoformat(dt_str)
        try:
            target_tz = pytz.timezone(config.TARGET_TIMEZONE)
            dt_local = dt_utc.astimezone(target_tz)
            # Format as HH:MM AM/PM (e.g., 09:30 AM)
            return dt_local.strftime('%I:%M %p')
        except Exception as e:
            print(f"Error formatting event time ({dt_str}): {e}. Falling back to UTC.")
            return dt_utc.strftime('%H:%M UTC') # Fallback format
    else:
        return "Time N/A" # Should not happen often

def get_calendar_events():
    """Fetches today's events from Google Calendar."""
    print("\n--- Fetching Google Calendar Events ---")
    try:
        service = utils.get_google_service(
            'calendar', 'v3',
            config.GOOGLE_SCOPES,
            config.GOOGLE_CREDENTIALS_FILE,
            config.GOOGLE_TOKEN_FILE
        )

        time_min_iso, time_max_iso = utils.get_localized_time_range(config.TARGET_TIMEZONE)

        print(f"Fetching events from {time_min_iso} to {time_max_iso}")

        events_result = service.events().list(
            calendarId='primary', # Use the primary calendar
            timeMin=time_min_iso,
            timeMax=time_max_iso,
            singleEvents=True, # Expand recurring events
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        formatted_events = []

        if not events:
            print("No upcoming events found for today.")
            return ["No meetings scheduled for today."]
        else:
            print(f"Found {len(events)} events:")
            for event in events:
                start_time_str = format_event_time(event['start'])
                summary = event.get('summary', 'No Title')
                formatted_event = f"{start_time_str} - {summary}"
                print(f"  - {formatted_event}")
                formatted_events.append(formatted_event)
            return formatted_events

    except HttpError as error:
        print(f'An HTTP error occurred fetching calendar events: {error}')
        if error.resp.status == 403:
             print("Suggestion: Ensure the Google Calendar API is enabled in your GCP project.")
        elif error.resp.status == 401:
            print("Suggestion: Authentication error. Try deleting token.json and re-running.")
        return ["Error fetching calendar events."]
    except FileNotFoundError as fnf_error:
        print(f"Configuration error: {fnf_error}")
        return ["Error: Credentials file missing."]
    except Exception as e:
        print(f'An unexpected error occurred fetching calendar events: {e}')
        return ["Error fetching calendar events."]

if __name__ == '__main__':
    # For local testing
    todays_events = get_calendar_events()
    print("\nFormatted Events:")
    for item in todays_events:
        print(item) 