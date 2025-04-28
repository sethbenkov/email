import os
from datetime import datetime
import pytz
from jinja2 import Environment, FileSystemLoader, select_autoescape

import config

def compose_email(calendar_events, email_list, onenote_tasks, ai_summary):
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
            'email_list': email_list,
            'onenote_tasks': onenote_tasks,
            'ai_summary': ai_summary
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
    # For local testing with sample data matching new structures
    sample_events = [{"time": "09:00 AM", "name": "Team Sync"}, {"time": "02:30 PM", "name": "Project Review"}]
    sample_emails = [{"sender": "Boss", "subject": "Urgent Request"}, {"sender": "Newsletter", "subject": "Weekly Update"}]
    sample_tasks = ["[Project X] Finalize budget", "[Admin] Book travel"]
    sample_ai = "**Key Decisions:**\n- Approved budget V2.\n\n**Action Items (Seth Benkov):**\n- Send final report by EOD Friday.\n\n**Action Items (Others):**\n- Kevin to update roadmap (Due Tomorrow).\n\n**Due Dates:**\n- Project X Launch: Next Monday."

    html_result = compose_email(sample_events, sample_emails, sample_tasks, sample_ai)

    # Save to local file for preview
    output_file = config.LOCAL_OUTPUT_HTML_FILE
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_result)
        print(f"\nEmail preview saved to: {output_file}")
    except Exception as e:
        print(f"Error saving email preview to {output_file}: {e}") 