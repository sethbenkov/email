import base64
from googleapiclient.errors import HttpError

import config
import utils

def get_email_snippets():
    """Fetches recent emails from Gmail, returning a list of {'sender', 'subject'} dicts
       and a combined string of raw email text for AI processing.
    """
    print("\n--- Fetching Gmail Snippets ---")
    email_list_data = [] # List of dictionaries for the email section
    raw_email_texts = [] # For AI summarization
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
            return [], "" # Return empty list and string
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

                # Append dict to email_list_data
                email_list_data.append({'sender': sender, 'subject': subject})
                print(f"  - Processed email: {subject[:50]}...")

                # Collect raw data for AI summary (Sender, Subject, Snippet)
                raw_email_texts.append(f"From: {sender}\nSubject: {subject}\n{snippet}")
                count += 1

            return email_list_data, "\n\n".join(raw_email_texts) # Return list of dicts and joined raw texts

    except HttpError as error:
        print(f'An HTTP error occurred fetching emails: {error}')
        if error.resp.status == 403:
            print("Suggestion: Ensure the Gmail API is enabled in your GCP project.")
        elif error.resp.status == 401:
            print("Suggestion: Authentication error. Try deleting token.json and re-running.")
        return [], "" # Return empty list and string on error
    except FileNotFoundError as fnf_error:
        print(f"Configuration error: {fnf_error}")
        return [], "" # Return empty list and string on error
    except Exception as e:
        print(f'An unexpected error occurred fetching emails: {e}')
        return [], "" # Return empty list and string on error

if __name__ == '__main__':
    # For local testing
    email_list, raw_text = get_email_snippets()
    print("\nEmail List Data (Sender/Subject):")
    if email_list:
        for item in email_list:
            print(f"  Sender: {item['sender']}, Subject: {item['subject']}")
    else:
        print("No emails fetched.")
    # print("\nRaw Text for AI:")
    # print(raw_text) # Uncomment to see raw text for AI 