# SMTP Protocol

## What is SMTP?

SMTP (Simple Mail Transfer Protocol) is the standard protocol for **sending** email. Defined in RFC 5321, it's been the backbone of email delivery since 1982. SMTP is a text-based protocol -- you can literally type SMTP commands by hand using `telnet`.

## Ports

| Port | Purpose | Encryption |
|------|---------|-----------|
| 25 | Server-to-server relay (MTA to MTA) | STARTTLS optional |
| 587 | Client submission (MUA to MSA) | STARTTLS required |
| 465 | Implicit TLS submission (legacy, revived) | TLS from start |

Port 587 is what this project uses. Your email client submits mail to your server on 587, then your server relays it to the recipient's server on port 25.

## The SMTP Conversation

An SMTP exchange is a dialogue between client (C) and server (S):

```
C: [connects to smtp.gmail.com:587]
S: 220 smtp.gmail.com ESMTP ready
C: EHLO myclient.local
S: 250-smtp.gmail.com at your service
S: 250-STARTTLS
S: 250-AUTH LOGIN PLAIN
S: 250 SIZE 35882577
C: STARTTLS
S: 220 2.0.0 Ready to start TLS
   [TLS handshake happens here]
C: EHLO myclient.local
S: 250-smtp.gmail.com at your service
S: 250-AUTH LOGIN PLAIN
S: 250 SIZE 35882577
C: AUTH LOGIN
S: 334 VXNlcm5hbWU6        (Base64 for "Username:")
C: dXNlckBnbWFpbC5jb20=    (Base64 encoded username)
S: 334 UGFzc3dvcmQ6        (Base64 for "Password:")
C: cGFzc3dvcmQ=            (Base64 encoded password)
S: 235 2.7.0 Authentication successful
C: MAIL FROM:<user@gmail.com>
S: 250 2.1.0 OK
C: RCPT TO:<alice@example.com>
S: 250 2.1.5 OK
C: DATA
S: 354 Go ahead
C: From: user@gmail.com
C: To: alice@example.com
C: Subject: Hello
C: Date: Thu, 06 Feb 2026 10:00:00 +0000
C:
C: This is the email body.
C: .
S: 250 2.0.0 OK, message accepted
C: QUIT
S: 221 2.0.0 closing connection
```

## Key SMTP Commands

| Command | Purpose |
|---------|---------|
| `EHLO` | Greeting + request server capabilities (Extended HELLO) |
| `STARTTLS` | Upgrade connection to TLS encryption |
| `AUTH` | Authenticate with username/password |
| `MAIL FROM` | Declare the sender (envelope sender) |
| `RCPT TO` | Declare a recipient (can be called multiple times) |
| `DATA` | Begin the message body (headers + content) |
| `QUIT` | End the session |

## Envelope vs. Headers

A subtle but important distinction:
- **Envelope sender/recipient**: The `MAIL FROM` and `RCPT TO` commands. These are what the servers use for routing. Like the address on the outside of a physical envelope.
- **Header From/To**: Inside the `DATA` section. These are what the email client displays. Like the letterhead inside the envelope.

They can differ. This is how BCC works -- the BCC recipient is in `RCPT TO` but not in the `To:` or `CC:` headers. It's also how email spoofing works (which SPF/DKIM/DMARC try to prevent).

## How Python's smtplib Maps to This

```python
import smtplib
from email.mime.text import MIMEText

msg = MIMEText("Hello!")             # Creates the DATA content
msg["From"] = "user@gmail.com"       # Header From
msg["To"] = "alice@example.com"      # Header To
msg["Subject"] = "Hello"             # Header Subject

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.ehlo()                    # EHLO command
    server.starttls()                # STARTTLS command
    server.ehlo()                    # EHLO again after TLS
    server.login("user", "pass")     # AUTH command
    server.send_message(msg)         # MAIL FROM + RCPT TO + DATA
                                     # (extracted from msg headers)
# Connection closes -> QUIT
```

## STARTTLS vs Implicit TLS

- **STARTTLS** (port 587): Connection starts unencrypted, then upgrades to TLS. The `STARTTLS` command triggers the upgrade.
- **Implicit TLS** (port 465): Connection is TLS from the first byte. No upgrade step needed.

STARTTLS on port 587 is the current standard for email submission. Port 465 was deprecated, then un-deprecated in RFC 8314 (2018) as an alternative.

## Error Codes

SMTP uses 3-digit status codes:
- `2xx`: Success
- `3xx`: Server needs more input
- `4xx`: Temporary failure (retry later)
- `5xx`: Permanent failure (don't retry)

Common ones: `250` (OK), `354` (start data), `421` (service unavailable), `550` (user not found).
