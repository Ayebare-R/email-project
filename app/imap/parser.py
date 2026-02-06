import email
import email.header
import email.utils
from email.message import EmailMessage
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ParsedEmail:
    uid: str
    subject: str
    sender: str
    to: list[str]
    cc: list[str]
    date: str
    body_plain: str
    body_html: str
    attachments: list[dict] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)


def parse_email(uid: str, msg: EmailMessage, flags: list[str] = None) -> ParsedEmail:
    subject = _decode_header(msg.get("Subject", "(No Subject)"))
    sender = _decode_header(msg.get("From", ""))
    to = _decode_address_list(msg.get("To", ""))
    cc = _decode_address_list(msg.get("Cc", ""))
    date = _parse_date(msg.get("Date", ""))

    body_plain = ""
    body_html = ""
    attachments = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in disposition:
                attachments.append({
                    "filename": part.get_filename() or "untitled",
                    "content_type": content_type,
                    "size": len(part.get_payload(decode=True) or b""),
                })
            elif content_type == "text/plain" and not body_plain:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    body_plain = payload.decode(charset, errors="replace")
            elif content_type == "text/html" and not body_html:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    body_html = payload.decode(charset, errors="replace")
    else:
        content_type = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace")
            if content_type == "text/html":
                body_html = text
            else:
                body_plain = text

    return ParsedEmail(
        uid=uid,
        subject=subject,
        sender=sender,
        to=to,
        cc=cc,
        date=date,
        body_plain=body_plain,
        body_html=body_html,
        attachments=attachments,
        flags=flags or [],
    )


def _decode_header(value: str) -> str:
    if not value:
        return ""
    decoded_parts = email.header.decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(part)
    return " ".join(result)


def _decode_address_list(value: str) -> list[str]:
    if not value:
        return []
    return [_decode_header(addr.strip()) for addr in value.split(",") if addr.strip()]


def _parse_date(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        return parsed.isoformat()
    except Exception:
        return value
