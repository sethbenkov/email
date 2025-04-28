import time
import os
import base64
from email.mime.text import MIMEText
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

# Import fetcher and composer functions
import google_calendar_fetcher
import gmail_fetcher
import onenote_parser
import email_composer
import config
import utils # Import utils for google service


def get_ai_summary(text_to_summarize):
    """Summarizes the provided text using the OpenAI ChatCompletion API."""
    print("\n--- Calling OpenAI for Summarization ---")
    if not text_to_summarize or text_to_summarize.strip() == "":
        print("No text provided for AI summary.")
        return "No email or meeting content available to summarize."

    # Load API key and initialize client
    api_key = os.getenv(config.OPENAI_API_KEY_ENV_VAR)
    if not api_key:
        print(f"Error: {config.OPENAI_API_KEY_ENV_VAR} not found in environment variables.")
        return "Error: OpenAI API key not configured."
    client = OpenAI(api_key=api_key)

    # Prepare chat messages
    system_message = ("You are a highly efficient executive assistant. Your task is to analyze the provided text, which includes emails, meeting notes (from Zoom), and personal task notes (from OneNote). "
                      "Consolidate this information and extract ONLY the following:\n\n"
                      "1. Key Decisions: List any significant decisions explicitly mentioned.\n\n"
                      "2. Action Items (Seth Benkov): List all action items assigned specifically to Seth Benkov. Include any mentioned due dates.\n\n"
                      "3. Action Items (Others): List action items assigned to Kevin or Trent that have upcoming due dates (e.g., today, tomorrow, this week). Be specific about who is responsible.\n\n"
                      "4. Due Dates: List any other major deadlines or due dates mentioned.\n\n"
                      "Format the output clearly with headings for each section. If no information is found for a section, state 'None identified'. Be concise and focus only on these points.")

    user_message = f"Analyze the following content from yesterday and today:\n\n{text_to_summarize}"

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1000, # Increased token limit
            temperature=0.5
        )
        summary = response.choices[0].message.content.strip()
        print("OpenAI Summary generated successfully.")
        return summary
    except OpenAIError as e:
        print(f"OpenAI API Error: {e}")
        return f"Error: OpenAI API error: {e}"
    except Exception as e:
        print(f"Unexpected error in OpenAI summarization: {e}")
        return f"Error generating AI summary: {e}"

def send_gmail(subject, html_body, recipient):
    """Sends an email using the Gmail API."""
    print("\n--- Sending Email via Gmail API ---")
    if not recipient:
        print("Error: Recipient email address not configured.")
        return False
        
    try:
        # Get Gmail service (ensure correct scopes including send)
        service = utils.get_google_service(
            'gmail', 'v1',
            config.GOOGLE_SCOPES,
            config.GOOGLE_CREDENTIALS_FILE,
            config.GOOGLE_TOKEN_FILE
        )

        # Create the email message
        message = MIMEText(html_body, 'html')
        message['to'] = recipient
        message['subject'] = subject
        # You can set 'from' if needed, otherwise it defaults to the authenticated user
        # message['from'] = 'Your Name <your_email@example.com>' 

        # Encode the message in base64url format
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': raw_message}

        # Send the email
        send_message = (service.users().messages().send(userId="me", body=create_message)
                       .execute())
        print(f"Email sent successfully to {recipient}. Message ID: {send_message['id']}")
        return True

    except HttpError as error:
        print(f'An HTTP error occurred sending email: {error}')
        if error.resp.status == 401:
            print("Suggestion: Authentication error. Ensure 'gmail.send' scope was granted. Try deleting token.json and re-running.")
        elif error.resp.status == 403:
             print("Suggestion: Ensure Gmail API is enabled and you have permission to send.")
        return False
    except Exception as e:
        print(f'An unexpected error occurred sending email: {e}')
        return False


def main():
    """Runs the full data fetching, AI summarization, composition, and sending process locally."""
    start_time = time.time()
    print("Starting Daily Brief generation process...")
    
    # Load environment variables from .env file
    load_dotenv() 

    # --- Fetch Data ---
    print("\n--- Fetching Data ---")
    # Note: The first time running may trigger browser-based auth flows
    todays_events = google_calendar_fetcher.get_calendar_events()
    email_list, raw_email_text = gmail_fetcher.get_email_snippets()
    # Zoom parser was removed; ensure you handle meeting summaries separately if needed
    onenote_tasks = onenote_parser.get_onenote_tasks_from_export()

    # Combine raw text for AI, including OneNote tasks
    # Filter out error messages from OneNote tasks before adding to AI input
    onenote_text_for_ai = "\n".join([task for task in onenote_tasks if not task.startswith("Error:") and task != "No open tasks found in latest OneNote export."])
    combined_raw_text = f"""--- Emails ---
{raw_email_text}

--- OneNote Tasks ---
{onenote_text_for_ai}"""

    # --- AI Summarization ---
    ai_summary_result = get_ai_summary(combined_raw_text)
    print(f"AI Summary Result: {ai_summary_result[:100]}...")

    # --- Compose Email ---
    email_subject = f"Daily Brief - {time.strftime('%A, %B %d, %Y')}" 
    final_html = email_composer.compose_email(
        calendar_events=todays_events, # Now a list of dicts
        email_list=email_list,       # Now a list of dicts
        onenote_tasks=onenote_tasks, # Keep as list of strings for its own section
        ai_summary=ai_summary_result
        # zoom_summaries are now implicitly included in ai_summary input
    )

    # --- Save Local Output ---
    output_file = config.LOCAL_OUTPUT_HTML_FILE
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_html)
        print(f"\nHTML output saved locally to: {output_file}")
    except Exception as e:
        print(f"Error saving local HTML file {output_file}: {e}")
        
    # --- Send Email ---
    recipient_email = os.getenv(config.RECIPIENT_EMAIL_ENV_VAR)
    if final_html and not final_html.startswith("<html><body><h1>Error</h1>"):
        send_success = send_gmail(email_subject, final_html, recipient_email)
        if not send_success:
             print("\n*** Email sending failed. Check logs above. ***")
    else:
        print("\nSkipping email sending due to composition error.")

    # --- Finish ---
    end_time = time.time()
    print(f"\nDaily Brief generation process finished in {end_time - start_time:.2f} seconds.")

if __name__ == '__main__':
    main() 