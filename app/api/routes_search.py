from fastapi import APIRouter, Request, HTTPException
from app.models.schemas import SearchRequest, SearchResponse, EmailSummary
from app.ai.search_agent import run_search_agent

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search_emails(req: SearchRequest, request: Request):
    imap = request.app.state.imap
    claude = request.app.state.claude

    if not imap.is_connected:
        raise HTTPException(status_code=400, detail="Not connected to email server")

    if not claude._api_key:
        raise HTTPException(status_code=400, detail="Anthropic API key not configured")

    try:
        result = run_search_agent(req.query, imap, claude)
        emails = [
            EmailSummary(
                uid=e["uid"],
                subject=e["subject"],
                sender=e["sender"],
                date=e["date"],
                is_read=e.get("is_read", False),
            )
            for e in result["emails"]
        ]
        return SearchResponse(
            summary=result["summary"],
            emails=emails,
            imap_query=result["imap_query"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
