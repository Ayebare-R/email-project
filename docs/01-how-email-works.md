# How Email Works: The Big Picture

## The Email Pipeline

When you click "Send" on an email, a surprisingly complex chain of events takes place across multiple servers and protocols. Here's the full journey:

```
[Your Email Client]          (MUA - Mail User Agent)
       |
       | SMTP (port 587)
       v
[Your Email Server]          (MSA - Mail Submission Agent)
       |
       | Internal processing
       v
[Outbound Mail Server]       (MTA - Mail Transfer Agent)
       |
       | DNS MX lookup for recipient's domain
       | SMTP (port 25)
       v
[Recipient's Mail Server]    (MTA - Mail Transfer Agent)
       |
       | Internal delivery
       v
[Recipient's Mailbox]        (MDA - Mail Delivery Agent)
       |
       | IMAP (port 993) or POP3 (port 995)
       v
[Recipient's Email Client]   (MUA - Mail User Agent)
```

## Key Actors

### MUA (Mail User Agent)
The email client -- Gmail's web interface, Apple Mail, Thunderbird, or this project's web UI. It's what the human interacts with. It speaks SMTP to send and IMAP (or POP3) to receive.

### MSA (Mail Submission Agent)
The first server your email hits. It authenticates you (username + password), checks that you're allowed to send, and passes the message along. Usually the same physical server as your email provider's MTA but listening on port 587 instead of 25.

### MTA (Mail Transfer Agent)
The workhorse. MTAs relay messages between servers using SMTP. When your MTA needs to deliver to `alice@example.com`, it:
1. Queries DNS for the MX records of `example.com`
2. Connects to the highest-priority MX server via SMTP on port 25
3. Transfers the message

If delivery fails, the MTA queues the message and retries (typically for up to 5 days).

### MDA (Mail Delivery Agent)
Once the recipient's MTA accepts the message, the MDA places it in the correct mailbox. This is where server-side filtering (spam detection, folder rules) happens.

## Store-and-Forward

Email uses a **store-and-forward** model, unlike real-time communication:
- Each server in the chain **stores** the message locally
- Then **forwards** it to the next server
- If the next server is unavailable, the message waits in a queue

This is why email is resilient -- the sender and recipient don't need to be online at the same time, and intermediate servers can buffer during outages.

## How This Project Fits In

This email assistant acts as an MUA (Mail User Agent):
- It uses **IMAP** to connect to your mail server and read your mailbox
- It uses **SMTP** to submit outgoing messages to your mail server
- The AI layer sits between you and the IMAP protocol, translating natural language queries into IMAP SEARCH commands

```
[You] <-> [Web UI] <-> [FastAPI Backend] <-> [IMAP/SMTP] <-> [Your Email Server]
                             |
                             v
                      [Claude AI API]
                   (search, summarize, draft)
```

## Types of Email Access

| Method | Protocol | How it works | Server-side state |
|--------|----------|-------------|-------------------|
| Webmail | HTTP(S) | Browser talks to the email provider's web app | Yes |
| IMAP | IMAP4 | Client syncs with server, messages stay on server | Yes |
| POP3 | POP3 | Client downloads messages, optionally deletes from server | Minimal |
| Exchange/MAPI | MAPI/EWS | Microsoft proprietary protocol | Yes |

IMAP is the standard for non-web email access because it keeps messages on the server and supports multiple clients viewing the same mailbox simultaneously.
