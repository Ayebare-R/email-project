from fastapi import APIRouter, Request, HTTPException
from app.models.schemas import ConnectRequest, StatusResponse

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/connect")
def connect(req: ConnectRequest, request: Request):
    imap = request.app.state.imap
    settings = request.app.state.settings

    # Reconfigure IMAP client with new credentials
    imap.reconfigure(req.imap_host, req.imap_port, req.imap_user, req.imap_password)

    # Update SMTP settings in memory
    settings.smtp_host = req.smtp_host or req.imap_host.replace("imap", "smtp")
    settings.smtp_port = req.smtp_port
    settings.smtp_user = req.smtp_user or req.imap_user
    settings.smtp_password = req.smtp_password or req.imap_password

    try:
        imap.connect()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {e}")

    return {"status": "connected", "user": req.imap_user}


@router.get("/status", response_model=StatusResponse)
def status(request: Request):
    imap = request.app.state.imap
    connected = imap.is_connected
    return StatusResponse(
        connected=connected,
        user=imap._user if connected else "",
    )
