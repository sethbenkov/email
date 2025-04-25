import base64
from googleapiclient.errors import HttpError

import config
import utils

def get_email_snippets():
    """Fetches snippets of recent emails from Gmail."""
    print("\n--- Fetching Gmail Snippets ---")
    emails_data = []
    raw_email_texts = [] # For potential AI summarization
    try:
        service = utils.get_google_service(
            'gmail', 'v1',
            config.GOOGLE_SCOPES,
            config.GOOGLE_CREDENTIALS_FILE,
            config.GOOGLE_TOKEN_FILE
        )

        # List messages matching the query
        results = service.users().messages().list(
            userId='me',
            q=config.GMAIL_QUERY,
            maxResults=config.MAX_EMAILS_TO_PROCESS
        ).execute()
        messages = results.get('messages', [])

        if not messages:
            print("No recent emails found matching the criteria.")
            return ["No relevant emails from the past day."], ""
        else:
            print(f"Found {len(messages)} emails. Fetching details...")
            count = 0
            for message_info in messages:
                if count >= config.MAX_EMAILS_TO_PROCESS:
                    print(f"Reached processing limit ({config.MAX_EMAILS_TO_PROCESS}).")
                    break
                msg = service.users().messages().get(
                    userId='me',
                    id=message_info['id'],
                    format='metadata', # Fetch specific headers and snippet
                    metadataHeaders=['From', 'Subject']
                ).execute()

                headers = msg.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                snippet = msg.get('snippet', '')

                # Clean up sender format (often includes email in < >)
                if '<' in sender:
                    sender_name = sender.split('<')[0].strip()
                    if sender_name and sender_name != '""': # Use name if available
                        sender = sender_name.replace('"', '')
                    else: # Fallback to full address if name is empty
                        sender = sender.split('<')[1].split('>')[0]
                else:
                    sender = sender.strip()

                formatted_email = f"From: {sender} | Subject: {subject} | Snippet: {snippet[:100]}..."
                print(f"  - Processed email: {subject[:50]}...")
                emails_data.append(formatted_email)

                # Collect raw data for AI summary (Sender, Subject, Snippet)
                raw_email_texts.append(f"From: {sender}\nSubject: {subject}\n{snippet}")
                count += 1

            return emails_data, "\n\n".join(raw_email_texts) # Join raw texts for single AI input

    except HttpError as error:
        print(f'An HTTP error occurred fetching emails: {error}')
        if error.resp.status == 403:
            print("Suggestion: Ensure the Gmail API is enabled in your GCP project.")
        elif error.resp.status == 401:
            print("Suggestion: Authentication error. Try deleting token.json and re-running.")
        return [f"Error fetching emails: {error}"], ""
    except FileNotFoundError as fnf_error:
        print(f"Configuration error: {fnf_error}")
        return ["Error: Credentials file missing."], ""
    except Exception as e:
        print(f'An unexpected error occurred fetching emails: {e}')
        return ["Error fetching emails."], ""

if __name__ == '__main__':
    # For local testing
    email_list, raw_text = get_email_snippets()
    print("\nFormatted Email Snippets:")
    for item in email_list:
        print(item)
    # print("\nRaw Text for AI:")
    # print(raw_text) # Uncomment to see raw text for AI 