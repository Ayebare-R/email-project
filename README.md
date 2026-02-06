# Email Project

An in-development IMAP email assistant powered by Claude AI. Connect to any IMAP email server, browse your inbox through a web UI, search emails using natural language, and get AI-powered assistance.

```
+-----------+       +------------------+       +----------------+
|           |  HTTP |                  | IMAP  |                |
|  Browser  |<----->|  FastAPI Server  |<----->|  Email Server  |
|  (Web UI) |       |                  | SMTP  |  (Gmail, etc)  |
|           |       +--------+---------+       +----------------+
+-----------+                |
                             | HTTPS
                             v
                    +------------------+
                    |  Anthropic API   |
                    |  (Claude)        |
                    +------------------+
```

## Features

- **Inbox Display** — Browse folders, view emails, see read/unread status
- **Agentic Search** — Describe what you're looking for in plain English; Claude translates it into IMAP search queries and refines automatically
- **Summarize** — Get a 2-3 sentence summary of any email
- **Draft Reply** — Tell the AI what to say and it writes the reply
- **Categorize** — Auto-categorize emails (Action Required, FYI, Marketing, etc.)
- **Extract Action Items** — Pull out tasks and deadlines from emails
- **Send/Reply** — Send emails via SMTP

## Quick Start

### Prerequisites

- Python 3.10+
- An email account with IMAP access (Gmail, Outlook, etc.)
- An [Anthropic API key](https://console.anthropic.com) for AI features

### Gmail Setup

Gmail requires an **App Password** (your regular password won't work):

1. Go to [Google Account](https://myaccount.google.com) → Security → 2-Step Verification
2. At the bottom, click **App Passwords**
3. Create one (name it anything) — you'll get a 16-character password

### Install & Run

```bash
git clone https://github.com/Ayebare-R/email-project.git
cd email-project

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your credentials

python run.py
```

Open **http://localhost:8000** in your browser.

## Configuration

Edit `.env` with your values:

```
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=you@gmail.com
IMAP_PASSWORD=your-app-password

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

ANTHROPIC_API_KEY=sk-ant-xxxxx
```

Or skip the `.env` file and enter credentials through the web UI connect form.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/connect` | Connect to IMAP server |
| GET | `/api/status` | Check connection status |
| GET | `/api/folders` | List mailbox folders |
| GET | `/api/inbox` | List emails in a folder |
| GET | `/api/email/{uid}` | Get full email by UID |
| POST | `/api/search` | AI-powered natural language search |
| POST | `/api/summarize` | Summarize an email |
| POST | `/api/draft-reply` | Generate a reply draft |
| POST | `/api/categorize` | Categorize emails |
| POST | `/api/action-items` | Extract action items |
| POST | `/api/send` | Send an email |

Interactive API docs available at **http://localhost:8000/docs** when the server is running.

## How Agentic Search Works

When you search for something like *"find emails from Sarah about the budget from last month"*:

1. Your query is sent to Claude along with an IMAP search tool definition
2. Claude decides the search parameters (from, subject, date range, etc.)
3. Those parameters are translated into an IMAP SEARCH command
4. The command runs against your email server
5. Results are fed back to Claude, which may refine the search or summarize the findings
6. You see: the AI summary, the raw IMAP query (educational), and the matching emails

## Project Structure

```
app/
  main.py              FastAPI app factory
  config.py            Settings from environment variables
  imap/                IMAP client, email parser, search builder
  smtp/                SMTP client for sending
  ai/                  Claude integration (search agent, email tools)
  api/                 REST API routes
  models/              Pydantic request/response schemas
  static/              Web UI (HTML, CSS, vanilla JS)
docs/                  Educational docs on email protocols
```

## Documentation

The `docs/` folder contains educational material on how the email system works:

- [How Email Works](docs/01-how-email-works.md) — The full send/receive pipeline
- [SMTP Protocol](docs/02-smtp-protocol.md) — Sending email under the hood
- [IMAP Protocol](docs/03-imap-protocol.md) — Reading email, UIDs, SEARCH, FETCH
- [DNS & MX Records](docs/04-dns-mx-records.md) — How email routing works
- [Email Authentication](docs/05-email-authentication.md) — SPF, DKIM, DMARC
- [Architecture](docs/06-architecture.md) — This project's design and data flows

## Tech Stack

- **Backend**: Python, FastAPI, uvicorn
- **Email**: stdlib `imaplib`, `smtplib`, `email`
- **AI**: Anthropic Claude API with tool use
- **Frontend**: Vanilla HTML/CSS/JS (no build step)
