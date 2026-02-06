# email-project

I wanted to understand how email actually works — not the Gmail UI, but the protocols underneath. IMAP, SMTP, MX records, the whole pipeline. So I built a client from scratch.

It connects to any IMAP server, pulls your inbox, and lets you search and read emails through a web interface. The interesting part: search is agentic. You type something like *"find emails from Sarah about the budget from last month"* and Claude figures out the right IMAP SEARCH query, runs it, and can refine if the first attempt doesn't land. The raw IMAP command is shown alongside results so you can see what's happening under the hood.

There's also summarization, reply drafting, and email categorization — all through Claude's API.

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

In development. Works with Gmail and should work with any standard IMAP provider. No database — all state lives on the mail server.
