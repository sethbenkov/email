import os
from datetime import datetime
import pytz
from jinja2 import Environment, FileSystemLoader, select_autoescape

import config

def compose_email(calendar_events, email_snippets, zoom_summaries, onenote_tasks, ai_summary="(AI Summary Placeholder)"):
    """Renders the HTML email using the Jinja2 template and collected data."""
    print("\n--- Composing Email ---")
    try:
        # Set up Jinja2 environment
        env = Environment(
            loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__))),
            autoescape=select_autoescape(['html', 'xml'])
        )
        template = env.get_template("email_template.html")

        # Get current time in target timezone for the footer
        try:
            target_tz = pytz.timezone(config.TARGET_TIMEZONE)
        except pytz.UnknownTimeZoneError:
            print(f"Warning: Unknown timezone '{config.TARGET_TIMEZONE}'. Using UTC for footer.")
            target_tz = pytz.utc

        now_local = datetime.now(target_tz)
        today_date_str = now_local.strftime("%A, %B %d, %Y")
        generation_time_str = now_local.strftime("%I:%M %p")
        generation_timezone_str = now_local.strftime("%Z")

        # Prepare context data for the template
        context = {
            'today_date': today_date_str,
            'generation_time': generation_time_str,
            'generation_timezone': generation_timezone_str,
            'calendar_events': calendar_events,
            'email_snippets': email_snippets,
            'zoom_summaries': zoom_summaries,
            'onenote_tasks': onenote_tasks,
            'ai_summary': ai_summary # Placeholder for now
        }

        # Render the template
        html_output = template.render(context)
        print("Email composition successful.")
        return html_output

    except Exception as e:
        print(f"Error composing email: {e}")
        # Return a basic error message as HTML
        return f"<html><body><h1>Error</h1><p>Failed to compose email: {e}</p></body></html>"

if __name__ == '__main__':
    # For local testing with sample data
    sample_events = ["09:00 AM - Team Sync", "02:30 PM - Project Review"]
    sample_emails = ["From: Boss | Subject: Urgent Request | Snippet: Please review the attached...", "From: Newsletter | Subject: Weekly Update | Snippet: Here is your weekly news..."]
    sample_zooms = [{'title': 'Weekly Team Meeting', 'recap': 'Discussed project progress.', 'next_steps': '- Alice to update JIRA\n- Bob to send report'}]
    sample_tasks = ["[Project X] Finalize budget", "[Admin] Book travel"]

    html_result = compose_email(sample_events, sample_emails, sample_zooms, sample_tasks)

    # Save to local file for preview
    output_file = config.LOCAL_OUTPUT_HTML_FILE
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_result)
        print(f"\nEmail preview saved to: {output_file}")
    except Exception as e:
        print(f"Error saving email preview to {output_file}: {e}") 