from dataclasses import dataclass
from typing import Optional


@dataclass
class SearchCriteria:
    from_addr: Optional[str] = None
    to_addr: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    since: Optional[str] = None    # DD-Mon-YYYY
    before: Optional[str] = None   # DD-Mon-YYYY
    flagged: Optional[bool] = None
    unseen: Optional[bool] = None


def build_imap_search(criteria: SearchCriteria) -> str:
    parts = []

    if criteria.from_addr:
        parts.append(f'FROM "{criteria.from_addr}"')
    if criteria.to_addr:
        parts.append(f'TO "{criteria.to_addr}"')
    if criteria.subject:
        parts.append(f'SUBJECT "{criteria.subject}"')
    if criteria.body:
        parts.append(f'BODY "{criteria.body}"')
    if criteria.since:
        parts.append(f"SINCE {criteria.since}")
    if criteria.before:
        parts.append(f"BEFORE {criteria.before}")
    if criteria.flagged is True:
        parts.append("FLAGGED")
    elif criteria.flagged is False:
        parts.append("UNFLAGGED")
    if criteria.unseen is True:
        parts.append("UNSEEN")
    elif criteria.unseen is False:
        parts.append("SEEN")

    if not parts:
        return "ALL"
    return "(" + " ".join(parts) + ")"
