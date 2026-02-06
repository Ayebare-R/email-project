import json

from app.ai.claude import ClaudeClient
from app.ai.prompts import (
    SUMMARIZE_SYSTEM,
    DRAFT_REPLY_SYSTEM,
    CATEGORIZE_SYSTEM,
    ACTION_ITEMS_SYSTEM,
)
from app.imap.parser import ParsedEmail


def summarize_email(email: ParsedEmail, claude: ClaudeClient) -> str:
    body = email.body_plain or email.body_html or "(empty)"
    user_msg = (
        f"From: {email.sender}\n"
        f"Subject: {email.subject}\n"
        f"Date: {email.date}\n\n"
        f"{body[:3000]}"
    )
    return claude.complete(SUMMARIZE_SYSTEM, user_msg, max_tokens=512)


def draft_reply(
    email: ParsedEmail, instruction: str, claude: ClaudeClient
) -> dict:
    body = email.body_plain or email.body_html or "(empty)"
    user_msg = (
        f"Original email:\n"
        f"From: {email.sender}\n"
        f"Subject: {email.subject}\n"
        f"Date: {email.date}\n\n"
        f"{body[:3000]}\n\n"
        f"---\n"
        f"User's instruction for the reply: {instruction}"
    )
    draft_text = claude.complete(DRAFT_REPLY_SYSTEM, user_msg, max_tokens=1024)

    subject = email.subject
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    return {"draft": draft_text, "subject": subject}


def categorize_emails(
    emails: list[dict], claude: ClaudeClient
) -> list[dict]:
    email_list = "\n".join(
        f'- UID {e["uid"]}: From {e["sender"]} | Subject: {e["subject"]}'
        for e in emails
    )
    user_msg = f"Categorize these emails:\n\n{email_list}"
    response = claude.complete(CATEGORIZE_SYSTEM, user_msg, max_tokens=1024)

    try:
        # Try to parse JSON from the response
        # Claude might wrap it in markdown code blocks
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        results = json.loads(text)
        return results
    except (json.JSONDecodeError, IndexError):
        return [{"uid": "?", "category": "Error parsing AI response"}]


def extract_action_items(email: ParsedEmail, claude: ClaudeClient) -> list[str]:
    body = email.body_plain or email.body_html or "(empty)"
    user_msg = (
        f"From: {email.sender}\n"
        f"Subject: {email.subject}\n"
        f"Date: {email.date}\n\n"
        f"{body[:3000]}"
    )
    response = claude.complete(ACTION_ITEMS_SYSTEM, user_msg, max_tokens=512)
    # Split into list items
    items = []
    for line in response.split("\n"):
        line = line.strip().lstrip("-•* ")
        if line:
            items.append(line)
    return items
