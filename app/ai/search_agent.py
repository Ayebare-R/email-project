from datetime import date

from app.ai.claude import ClaudeClient
from app.ai.prompts import SEARCH_SYSTEM
from app.imap.client import IMAPClient
from app.imap.search import SearchCriteria, build_imap_search


SEARCH_TOOL = {
    "name": "imap_search",
    "description": "Search the user's email inbox using IMAP criteria. Returns matching email summaries.",
    "input_schema": {
        "type": "object",
        "properties": {
            "from_addr": {
                "type": "string",
                "description": "Sender email address or name fragment",
            },
            "to_addr": {
                "type": "string",
                "description": "Recipient email or name",
            },
            "subject": {
                "type": "string",
                "description": "Subject line keyword(s)",
            },
            "body": {
                "type": "string",
                "description": "Body text keyword(s)",
            },
            "since": {
                "type": "string",
                "description": "Date in DD-Mon-YYYY format (e.g. 01-Jan-2025). Only return emails on or after this date.",
            },
            "before": {
                "type": "string",
                "description": "Date in DD-Mon-YYYY format. Only return emails before this date.",
            },
            "unseen": {
                "type": "boolean",
                "description": "If true, only return unread messages",
            },
        },
        "required": [],
    },
}


def run_search_agent(
    query: str,
    imap: IMAPClient,
    claude: ClaudeClient,
    folder: str = "INBOX",
) -> dict:
    today = date.today().strftime("%d-%b-%Y")
    system = SEARCH_SYSTEM.format(today=today)
    messages = [{"role": "user", "content": query}]
    tools = [SEARCH_TOOL]

    matched_emails = []
    imap_query = ""

    for _ in range(5):
        response = claude.complete_with_tools(
            system=system,
            messages=messages,
            tools=tools,
        )

        # Find tool_use blocks
        tool_use_block = None
        for block in response.content:
            if block.type == "tool_use":
                tool_use_block = block
                break

        if tool_use_block is None:
            # Claude returned a final text response
            text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text += block.text
            return {
                "summary": text,
                "emails": matched_emails,
                "imap_query": imap_query,
            }

        # Execute the IMAP search
        params = tool_use_block.input
        criteria = SearchCriteria(
            from_addr=params.get("from_addr"),
            to_addr=params.get("to_addr"),
            subject=params.get("subject"),
            body=params.get("body"),
            since=params.get("since"),
            before=params.get("before"),
            unseen=params.get("unseen"),
        )
        imap_query = build_imap_search(criteria)
        uids = imap.search(imap_query, folder=folder)
        headers = imap.fetch_headers(uids, limit=20)
        matched_emails = headers

        # Format results for Claude
        if headers:
            result_text = f"Found {len(headers)} emails:\n\n"
            for h in headers:
                read_status = "Read" if h["is_read"] else "Unread"
                result_text += (
                    f"- UID {h['uid']} | {h['sender']} | "
                    f"{h['subject']} | {h['date']} | {read_status}\n"
                )
        else:
            result_text = "No emails found matching those criteria."

        # Feed results back to Claude
        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_block.id,
                    "content": result_text,
                }
            ],
        })

    # Fell through max iterations
    return {
        "summary": "Search completed but did not produce a final summary.",
        "emails": matched_emails,
        "imap_query": imap_query,
    }
