# IMAP Protocol

## What is IMAP?

IMAP (Internet Message Access Protocol, RFC 3501) is the standard protocol for **reading** email from a server. Unlike POP3 (which downloads and deletes), IMAP keeps messages on the server and lets multiple clients access the same mailbox simultaneously.

## IMAP vs POP3

| Feature | IMAP | POP3 |
|---------|------|------|
| Messages stay on server | Yes | No (by default) |
| Multiple clients | Yes | Problematic |
| Server-side folders | Yes | No |
| Server-side search | Yes | No |
| Bandwidth | Downloads on demand | Downloads everything |
| Offline access | Partial (cached) | Full (downloaded) |

IMAP is the better choice for modern email workflows where you access email from multiple devices.

## Key Concepts

### Mailboxes (Folders)
IMAP organizes messages into mailboxes (folders). Standard ones include:
- `INBOX` (the only required one)
- `Sent`, `Drafts`, `Trash`, `Spam`/`Junk`
- Custom user-created folders

### UIDs vs Sequence Numbers
Messages can be identified two ways:
- **Sequence numbers**: 1, 2, 3... -- positional, change when messages are deleted
- **UIDs**: Unique identifiers, stable across sessions

**This project uses UIDs exclusively.** If you use sequence numbers and message #5 gets deleted, what was #6 becomes #5 -- every reference breaks. UIDs don't have this problem.

Each mailbox has a `UIDVALIDITY` value. If it changes, all UIDs are invalidated (rare, but possible after server maintenance).

### Flags
Messages have flags indicating state:
- `\Seen` -- Message has been read
- `\Answered` -- Message has been replied to
- `\Flagged` -- User-flagged/starred
- `\Deleted` -- Marked for deletion (not yet expunged)
- `\Draft` -- Message is a draft

### SEARCH

IMAP has a powerful server-side search. This is what makes the agentic search in this project possible -- Claude translates natural language into IMAP SEARCH criteria:

```
SEARCH FROM "alice" SUBJECT "budget" SINCE 01-Jan-2025
```

Common search keys:
| Key | Meaning |
|-----|---------|
| `ALL` | All messages |
| `FROM "string"` | From header contains string |
| `TO "string"` | To header contains string |
| `SUBJECT "string"` | Subject contains string |
| `BODY "string"` | Body contains string |
| `SINCE date` | Internal date on or after |
| `BEFORE date` | Internal date before |
| `SEEN` / `UNSEEN` | Read / unread |
| `FLAGGED` / `UNFLAGGED` | Starred / not starred |
| `LARGER n` | Larger than n bytes |
| `SMALLER n` | Smaller than n bytes |
| `OR key1 key2` | Either condition |
| `NOT key` | Negate condition |

Date format is always `DD-Mon-YYYY` (e.g., `06-Feb-2025`).

Criteria can be combined. Multiple criteria on the same line are AND-ed:
```
SEARCH FROM "alice" SINCE 01-Jan-2025 UNSEEN
```
This means: from alice AND since Jan 1 AND unread.

### FETCH

Once you have UIDs from SEARCH, you FETCH message data:

```
UID FETCH 1234 (ENVELOPE BODY[TEXT] FLAGS)
```

What you can fetch:
- `ENVELOPE` -- Parsed header structure (from, to, subject, date)
- `BODY[HEADER]` -- Raw headers
- `BODY[TEXT]` -- Message body
- `RFC822` -- Complete raw message
- `FLAGS` -- Message flags
- `BODY.PEEK[...]` -- Same as BODY but doesn't set \Seen flag

## The IMAP Session

```
C: [connects to imap.gmail.com:993 over TLS]
S: * OK IMAP4rev1 Service Ready
C: a001 LOGIN user@gmail.com password
S: a001 OK LOGIN completed
C: a002 LIST "" "*"
S: * LIST (\HasNoChildren) "/" "INBOX"
S: * LIST (\HasNoChildren) "/" "Sent"
S: a002 OK LIST completed
C: a003 SELECT INBOX
S: * 42 EXISTS
S: * OK [UIDVALIDITY 1234567890]
S: a003 OK [READ-WRITE] SELECT completed
C: a004 UID SEARCH FROM "alice" SINCE 01-Jan-2025
S: * SEARCH 1001 1015 1042
S: a004 OK SEARCH completed
C: a005 UID FETCH 1042 (ENVELOPE BODY.PEEK[TEXT] FLAGS)
S: * 35 FETCH (UID 1042 ENVELOPE (...) BODY[TEXT] "Hello..." FLAGS (\Seen))
S: a005 OK FETCH completed
C: a006 LOGOUT
S: * BYE IMAP4rev1 server logging out
S: a006 OK LOGOUT completed
```

Each command has a tag (`a001`, `a002`, etc.) that matches the response, allowing pipelined commands.

## How Python's imaplib Maps to This

```python
import imaplib

# Connect + login
conn = imaplib.IMAP4_SSL("imap.gmail.com", 993)   # TLS connection
conn.login("user@gmail.com", "app-password")        # LOGIN

# List folders
conn.list()                                          # LIST "" "*"

# Select mailbox
conn.select("INBOX")                                 # SELECT INBOX

# Search
typ, data = conn.uid("search", None, 'FROM "alice"') # UID SEARCH FROM "alice"
uids = data[0].split()                               # [b'1001', b'1015', b'1042']

# Fetch
typ, data = conn.uid("fetch", b"1042", "(RFC822)")   # UID FETCH 1042 (RFC822)
raw_message = data[0][1]                              # Raw bytes

# Parse with email module
import email
msg = email.message_from_bytes(raw_message)
print(msg["Subject"])
print(msg["From"])

conn.logout()                                         # LOGOUT
```

## Gmail-Specific Notes

Gmail maps its labels to IMAP folders:
- `INBOX` -> Inbox
- `[Gmail]/Sent Mail` -> Sent
- `[Gmail]/Drafts` -> Drafts
- `[Gmail]/Trash` -> Trash
- `[Gmail]/Spam` -> Spam
- `[Gmail]/All Mail` -> All Mail (everything)

Gmail requires an **App Password** for IMAP access (regular password won't work with 2FA enabled). Generate one at: Google Account -> Security -> 2-Step Verification -> App Passwords.
