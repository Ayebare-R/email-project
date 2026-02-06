from pydantic import BaseModel
from typing import Optional


class ConnectRequest(BaseModel):
    imap_host: str
    imap_port: int = 993
    imap_user: str
    imap_password: str
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""


class StatusResponse(BaseModel):
    connected: bool
    user: str = ""


class EmailSummary(BaseModel):
    uid: str
    subject: str
    sender: str
    date: str
    is_read: bool


class EmailDetail(BaseModel):
    uid: str
    subject: str
    sender: str
    to: list[str]
    cc: list[str]
    date: str
    body_plain: str
    body_html: str
    attachments: list[dict]


class InboxResponse(BaseModel):
    folder: str
    total: int
    emails: list[EmailSummary]


class FoldersResponse(BaseModel):
    folders: list[str]


class SearchRequest(BaseModel):
    query: str


class SearchResponse(BaseModel):
    summary: str
    emails: list[EmailSummary]
    imap_query: str


class SummarizeRequest(BaseModel):
    uid: str


class SummarizeResponse(BaseModel):
    summary: str


class DraftReplyRequest(BaseModel):
    uid: str
    instruction: str


class DraftReplyResponse(BaseModel):
    draft: str
    subject: str


class CategorizeRequest(BaseModel):
    uids: list[str]


class CategoryResult(BaseModel):
    uid: str
    subject: str
    category: str


class CategorizeResponse(BaseModel):
    results: list[CategoryResult]


class ActionItemsRequest(BaseModel):
    uid: str


class ActionItemsResponse(BaseModel):
    items: list[str]


class SendRequest(BaseModel):
    to: str
    subject: str
    body: str
    in_reply_to: Optional[str] = None


class SendResponse(BaseModel):
    success: bool
    message: str
