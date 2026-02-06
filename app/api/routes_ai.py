from fastapi import APIRouter, Request, HTTPException
from app.models.schemas import (
    SummarizeRequest, SummarizeResponse,
    DraftReplyRequest, DraftReplyResponse,
    CategorizeRequest, CategorizeResponse, CategoryResult,
    ActionItemsRequest, ActionItemsResponse,
)
from app.imap.parser import parse_email
from app.ai.email_tools import (
    summarize_email,
    draft_reply,
    categorize_emails,
    extract_action_items,
)

router = APIRouter(prefix="/api", tags=["ai"])


def _require_connected(request: Request):
    if not request.app.state.imap.is_connected:
        raise HTTPException(status_code=400, detail="Not connected to email server")
    if not request.app.state.claude._api_key:
        raise HTTPException(status_code=400, detail="Anthropic API key not configured")


@router.post("/summarize", response_model=SummarizeResponse)
def summarize(req: SummarizeRequest, request: Request):
    _require_connected(request)
    imap = request.app.state.imap
    claude = request.app.state.claude

    try:
        msg = imap.fetch_full(req.uid)
        flags = imap.fetch_flags(req.uid)
        parsed = parse_email(req.uid, msg, flags)
        summary = summarize_email(parsed, claude)
        return SummarizeResponse(summary=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/draft-reply", response_model=DraftReplyResponse)
def draft_reply_endpoint(req: DraftReplyRequest, request: Request):
    _require_connected(request)
    imap = request.app.state.imap
    claude = request.app.state.claude

    try:
        msg = imap.fetch_full(req.uid)
        flags = imap.fetch_flags(req.uid)
        parsed = parse_email(req.uid, msg, flags)
        result = draft_reply(parsed, req.instruction, claude)
        return DraftReplyResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/categorize", response_model=CategorizeResponse)
def categorize(req: CategorizeRequest, request: Request):
    _require_connected(request)
    imap = request.app.state.imap
    claude = request.app.state.claude

    try:
        # Fetch headers for the requested UIDs
        email_summaries = []
        for uid in req.uids:
            headers = imap.fetch_headers([uid.encode()], limit=1)
            if headers:
                email_summaries.append(headers[0])

        results = categorize_emails(email_summaries, claude)
        return CategorizeResponse(
            results=[
                CategoryResult(
                    uid=r.get("uid", ""),
                    subject=r.get("subject", ""),
                    category=r.get("category", "Unknown"),
                )
                for r in results
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/action-items", response_model=ActionItemsResponse)
def action_items(req: ActionItemsRequest, request: Request):
    _require_connected(request)
    imap = request.app.state.imap
    claude = request.app.state.claude

    try:
        msg = imap.fetch_full(req.uid)
        flags = imap.fetch_flags(req.uid)
        parsed = parse_email(req.uid, msg, flags)
        items = extract_action_items(parsed, claude)
        return ActionItemsResponse(items=items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
