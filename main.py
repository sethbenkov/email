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
import zoom_parser
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
    messages = [
        {"role": "system", "content": "You are a helpful assistant that summarizes text."},
        {"role": "user", "content": f"Please summarize the following email snippets and meeting notes from yesterday.\n\n{text_to_summarize}"}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=300,
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
    zoom_summaries, raw_zoom_text = zoom_parser.get_zoom_summaries()
    onenote_tasks = onenote_parser.get_onenote_tasks_from_export()

    # Combine raw text for AI
    combined_raw_text = f"""--- Emails ---
{raw_email_text}

--- Zoom Meetings ---
{raw_zoom_text}"""

    # --- AI Summarization ---
    ai_summary_result = get_ai_summary(combined_raw_text)
    print(f"AI Summary Result: {ai_summary_result[:100]}...") # Print start of summary

    # --- Compose Email ---
    email_subject = f"Daily Brief - {time.strftime('%A, %B %d, %Y')}" 
    final_html = email_composer.compose_email(
        calendar_events=todays_events,
        email_snippets=email_list,
        zoom_summaries=zoom_summaries,
        onenote_tasks=onenote_tasks,
        ai_summary=ai_summary_result
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