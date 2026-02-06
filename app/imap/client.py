import imaplib
import email
import time
import logging
from email.message import EmailMessage
from typing import Optional

logger = logging.getLogger(__name__)


class IMAPClient:
    def __init__(self, host: str, port: int, user: str, password: str):
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._conn: Optional[imaplib.IMAP4_SSL] = None
        self._selected_folder: Optional[str] = None
        self._last_activity: float = 0

    def connect(self) -> None:
        """Establish a fresh IMAP connection and login."""
        self._close_quiet()
        self._conn = imaplib.IMAP4_SSL(self._host, self._port)
        self._conn.login(self._user, self._password)
        self._selected_folder = None
        self._last_activity = time.time()
        logger.info("IMAP connected to %s as %s", self._host, self._user)

    def disconnect(self) -> None:
        self._close_quiet()

    def _close_quiet(self) -> None:
        """Silently close any existing connection."""
        if self._conn:
            try:
                self._conn.logout()
            except Exception:
                pass
            self._conn = None
            self._selected_folder = None

    def reconfigure(self, host: str, port: int, user: str, password: str) -> None:
        self.disconnect()
        self._host = host
        self._port = port
        self._user = user
        self._password = password

    @property
    def is_connected(self) -> bool:
        """Lightweight connection check -- avoids noop unless connection is stale."""
        if not self._conn:
            return False
        # If active recently (within 5 min), trust it without a round-trip
        if time.time() - self._last_activity < 300:
            return True
        # Stale -- do a noop to verify
        try:
            self._conn.noop()
            self._last_activity = time.time()
            return True
        except Exception:
            self._conn = None
            self._selected_folder = None
            return False

    def _ensure_connected(self) -> None:
        """Reconnect if the connection is dead or stale."""
        if self._conn is None:
            self.connect()
            return
        # Gmail drops idle connections after ~10 min; proactively reconnect at 8 min
        if time.time() - self._last_activity > 480:
            logger.info("Connection stale (>8 min idle), reconnecting...")
            self.connect()

    def _retry(self, operation):
        """Execute an IMAP operation with one automatic retry on failure."""
        try:
            result = operation()
            self._last_activity = time.time()
            return result
        except (imaplib.IMAP4.error, imaplib.IMAP4.abort, OSError, BrokenPipeError, ConnectionResetError) as e:
            logger.warning("IMAP operation failed (%s), reconnecting...", e)
            self.connect()
            if self._selected_folder:
                self._conn.select(self._selected_folder)
            result = operation()
            self._last_activity = time.time()
            return result

    def _select_folder(self, folder: str) -> None:
        """Select a folder only if not already selected (avoids redundant SELECTs)."""
        if self._selected_folder != folder:
            self._conn.select(folder)
            self._selected_folder = folder

    def list_folders(self) -> list[str]:
        self._ensure_connected()

        def _do():
            typ, data = self._conn.list()
            folders = []
            for item in data:
                if isinstance(item, bytes):
                    parts = item.decode().rsplit('"', 2)
                    if len(parts) >= 2:
                        folder_name = parts[-2].strip().strip('"')
                        if folder_name:
                            folders.append(folder_name)
            return folders

        return self._retry(_do)

    def select_folder(self, folder: str = "INBOX") -> int:
        self._ensure_connected()

        def _do():
            typ, data = self._conn.select(folder)
            self._selected_folder = folder
            return int(data[0])

        return self._retry(_do)

    def search(self, criteria: str, folder: str = "INBOX") -> list[bytes]:
        self._ensure_connected()

        def _do():
            self._select_folder(folder)
            typ, data = self._conn.uid("search", None, criteria)
            if data[0]:
                return data[0].split()
            return []

        return self._retry(_do)

    def fetch_headers(self, uids: list[bytes], limit: int = 50) -> list[dict]:
        self._ensure_connected()
        uids_to_fetch = uids[-limit:]

        def _do():
            results = []
            for uid in reversed(uids_to_fetch):
                typ, data = self._conn.uid(
                    "fetch", uid, "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)] FLAGS)"
                )
                if not data or data[0] is None:
                    continue

                raw_header = data[0][1] if isinstance(data[0], tuple) else data[0]
                if not isinstance(raw_header, bytes):
                    continue

                msg = email.message_from_bytes(raw_header)

                flags_str = ""
                if isinstance(data[0], tuple):
                    flags_str = data[0][0].decode("utf-8", errors="replace")
                if len(data) > 1 and data[1] and isinstance(data[1], bytes):
                    flags_str += data[1].decode("utf-8", errors="replace")

                is_read = "\\Seen" in flags_str

                results.append({
                    "uid": uid.decode() if isinstance(uid, bytes) else str(uid),
                    "subject": _decode_header(msg.get("Subject", "(No Subject)")),
                    "sender": _decode_header(msg.get("From", "")),
                    "date": msg.get("Date", ""),
                    "is_read": is_read,
                })
            return results

        return self._retry(_do)

    def fetch_full(self, uid: str) -> EmailMessage:
        self._ensure_connected()
        uid_bytes = uid.encode() if isinstance(uid, str) else uid

        def _do():
            typ, data = self._conn.uid("fetch", uid_bytes, "(RFC822)")
            raw = data[0][1]
            return email.message_from_bytes(raw)

        return self._retry(_do)

    def fetch_flags(self, uid: str) -> list[str]:
        self._ensure_connected()
        uid_bytes = uid.encode() if isinstance(uid, str) else uid

        def _do():
            typ, data = self._conn.uid("fetch", uid_bytes, "(FLAGS)")
            if data[0]:
                resp = data[0].decode("utf-8", errors="replace")
                start = resp.find("FLAGS (")
                if start != -1:
                    end = resp.find(")", start + 7)
                    return resp[start + 7 : end].split()
            return []

        return self._retry(_do)


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
