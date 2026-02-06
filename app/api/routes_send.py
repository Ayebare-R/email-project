from fastapi import APIRouter, Request, HTTPException
from app.models.schemas import SendRequest, SendResponse
from app.smtp.client import SMTPClient

router = APIRouter(prefix="/api", tags=["send"])


@router.post("/send", response_model=SendResponse)
def send_email(req: SendRequest, request: Request):
    settings = request.app.state.settings
    if not settings.smtp_host or not settings.smtp_user:
        raise HTTPException(status_code=400, detail="SMTP not configured")

    try:
        smtp = SMTPClient(
            host=settings.smtp_host,
            port=settings.smtp_port,
            user=settings.smtp_user,
            password=settings.smtp_password,
        )
        smtp.send(
            to=req.to,
            subject=req.subject,
            body=req.body,
            in_reply_to=req.in_reply_to,
        )
        return SendResponse(success=True, message="Email sent successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send: {e}")
