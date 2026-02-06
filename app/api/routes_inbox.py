from fastapi import APIRouter, Request, HTTPException, Query
from app.models.schemas import InboxResponse, EmailSummary, EmailDetail, FoldersResponse
from app.imap.parser import parse_email

router = APIRouter(prefix="/api", tags=["inbox"])


@router.get("/folders", response_model=FoldersResponse)
def list_folders(request: Request):
    imap = request.app.state.imap
    if not imap.is_connected:
        raise HTTPException(status_code=400, detail="Not connected")
    try:
        folders = imap.list_folders()
        return FoldersResponse(folders=folders)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inbox", response_model=InboxResponse)
def get_inbox(
    request: Request,
    folder: str = Query("INBOX"),
    limit: int = Query(50, ge=1, le=200),
):
    imap = request.app.state.imap
    if not imap.is_connected:
        raise HTTPException(status_code=400, detail="Not connected")

    try:
        uids = imap.search("ALL", folder=folder)
        headers = imap.fetch_headers(uids, limit=limit)
        emails = [
            EmailSummary(
                uid=h["uid"],
                subject=h["subject"],
                sender=h["sender"],
                date=h["date"],
                is_read=h["is_read"],
            )
            for h in headers
        ]
        return InboxResponse(folder=folder, total=len(uids), emails=emails)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/email/{uid}", response_model=EmailDetail)
def get_email(uid: str, request: Request, folder: str = Query("INBOX")):
    imap = request.app.state.imap
    if not imap.is_connected:
        raise HTTPException(status_code=400, detail="Not connected")

    try:
        imap.select_folder(folder)
        msg = imap.fetch_full(uid)
        flags = imap.fetch_flags(uid)
        parsed = parse_email(uid, msg, flags)
        return EmailDetail(
            uid=parsed.uid,
            subject=parsed.subject,
            sender=parsed.sender,
            to=parsed.to,
            cc=parsed.cc,
            date=parsed.date,
            body_plain=parsed.body_plain,
            body_html=parsed.body_html,
            attachments=parsed.attachments,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
