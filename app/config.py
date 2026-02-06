import os
from dataclasses import dataclass


@dataclass
class Settings:
    imap_host: str = ""
    imap_port: int = 993
    imap_user: str = ""
    imap_password: str = ""

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            imap_host=os.environ.get("IMAP_HOST", ""),
            imap_port=int(os.environ.get("IMAP_PORT", "993")),
            imap_user=os.environ.get("IMAP_USER", ""),
            imap_password=os.environ.get("IMAP_PASSWORD", ""),
            smtp_host=os.environ.get("SMTP_HOST", ""),
            smtp_port=int(os.environ.get("SMTP_PORT", "587")),
            smtp_user=os.environ.get("SMTP_USER", ""),
            smtp_password=os.environ.get("SMTP_PASSWORD", ""),
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            claude_model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
        )
