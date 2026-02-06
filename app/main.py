from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.config import Settings
from app.imap.client import IMAPClient
from app.ai.claude import ClaudeClient
from app.api import routes_auth, routes_inbox, routes_search, routes_ai, routes_send


load_dotenv()

settings = Settings.from_env()
imap_client = IMAPClient(
    host=settings.imap_host,
    port=settings.imap_port,
    user=settings.imap_user,
    password=settings.imap_password,
)
claude_client = ClaudeClient(settings)

app = FastAPI(title="Email Assistant", version="0.1.0")

# Store shared state on the app instance so routes can access it
app.state.settings = settings
app.state.imap = imap_client
app.state.claude = claude_client

app.include_router(routes_auth.router)
app.include_router(routes_inbox.router)
app.include_router(routes_search.router)
app.include_router(routes_ai.router)
app.include_router(routes_send.router)

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
