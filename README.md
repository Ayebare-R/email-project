# email-project

I built this project for two reasons: to get sharper with Claude Code and to understand how email works beneath the surface. (IMAP, SMTP, MX records), the full protocol pipeline.

So I implemented this client. 

It connects directly to any IMAP server, pulls your inbox, and lets you search and read mail through a simple web interface. The interesting part is the search layer: you can type something like “find emails from Sarah about the budget from last month,” and Claude translates that intent into the correct IMAP SEARCH command, executes it, and iterates if needed. The raw protocol commands are shown alongside the results so you can see exactly what’s happening under the hood.
On top of that, there’s summarization, reply drafting, and categorization via Claude’s API. 

The core logic and protocol handling are all implemented directly.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # add your credentials
python run.py          # http://localhost:8000
```

You need three things in `.env`:
- IMAP credentials (for Gmail: use an [App Password](https://myaccount.google.com), not your real password)
- SMTP credentials (usually the same)
- An [Anthropic API key](https://console.anthropic.com)

## What's in here

```
app/
  imap/          connection management, email parsing, search query builder
  smtp/          sending replies
  ai/            claude wrapper, agentic search loop, summarize/draft/categorize
  api/           REST endpoints (FastAPI)
  static/        the frontend — vanilla HTML/CSS/JS, no build step
docs/            writeups on how email protocols work
```

The `docs/` folder is the learning side of this project:

- [How Email Works](docs/01-how-email-works.md) — the full journey from send to receive
- [SMTP](docs/02-smtp-protocol.md) — the actual conversation between mail servers
- [IMAP](docs/03-imap-protocol.md) — how clients read from a mailbox
- [DNS & MX Records](docs/04-dns-mx-records.md) — how servers find each other
- [SPF, DKIM, DMARC](docs/05-email-authentication.md) — why email spoofing is hard now
- [Architecture](docs/06-architecture.md) — how this project is wired together

## Built with

Python · FastAPI · imaplib/smtplib · Anthropic Claude API · vanilla JS

## Status

.Works with Gmail and should work with any standard IMAP provider. No database — all state lives on the mail server.
