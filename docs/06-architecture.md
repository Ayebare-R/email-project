# Project Architecture

## System Overview

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

## Directory Map

```
app/
  main.py          -- FastAPI app, mounts routes and static files
  config.py        -- Settings dataclass, loaded from .env

  imap/
    client.py      -- IMAPClient: manages connection, search, fetch
    parser.py      -- Converts raw email.message.EmailMessage -> ParsedEmail
    search.py      -- SearchCriteria dataclass -> IMAP SEARCH string

  smtp/
    client.py      -- SMTPClient: send email via SMTP+STARTTLS

  ai/
    claude.py      -- ClaudeClient: thin wrapper around anthropic SDK
    prompts.py     -- System prompt templates for each AI feature
    search_agent.py -- Agentic search loop using Claude tool use
    email_tools.py -- Summarize, draft reply, categorize, action items

  api/
    routes_auth.py   -- POST /api/connect, GET /api/status
    routes_inbox.py  -- GET /api/folders, /api/inbox, /api/email/{uid}
    routes_search.py -- POST /api/search
    routes_ai.py     -- POST /api/summarize, /api/draft-reply, etc.
    routes_send.py   -- POST /api/send

  models/
    schemas.py     -- Pydantic models for all request/response types

  static/
    index.html     -- Single page app shell
    css/style.css  -- All styles
    js/
      api.js       -- fetch() wrappers for all API endpoints
      components.js -- HTML render functions (templates)
      app.js       -- State management, view routing, event binding
```

## Data Flow: Inbox Loading

```
1. Browser loads index.html
2. app.js calls GET /api/status
3. If connected (env vars):
   a. GET /api/folders -> renders sidebar
   b. GET /api/inbox?folder=INBOX -> renders email list
4. If not connected:
   a. Renders connect form
   b. User submits credentials -> POST /api/connect
   c. Server creates IMAPClient, calls .connect()
   d. On success, flow continues from step 3
```

## Data Flow: Agentic Search

This is the core architectural pattern -- a multi-turn tool-use loop:

```
1. User types: "find invoices from last month"
2. Browser: POST /api/search {"query": "find invoices from last month"}
3. FastAPI route calls run_search_agent(query, imap, claude)
4. search_agent.py:
   a. Sends query + imap_search tool definition to Claude API
   b. Claude returns: tool_use(from_addr=None, subject="invoice", since="06-Jan-2026")
   c. We build IMAP query: '(SUBJECT "invoice" SINCE 06-Jan-2026)'
   d. Execute against IMAP server -> get UIDs -> fetch headers
   e. Format results as text, send back to Claude as tool_result
   f. Claude may:
      - Call tool again (refine search) -> go to step b
      - Return text summary -> done
   g. Max 5 iterations to prevent infinite loops
5. Return {summary, emails, imap_query} to browser
6. Browser renders: AI summary + IMAP query shown + email list
```

## Data Flow: AI Features

All AI features follow the same pattern:

```
1. Browser sends UID to API endpoint
2. Route fetches full email from IMAP (fetch_full + parse_email)
3. Route passes ParsedEmail + ClaudeClient to the appropriate email_tools function
4. email_tools function builds a prompt (system + user) and calls claude.complete()
5. Claude's response is returned to the browser
```

## State Management

The app has minimal server-side state:
- `app.state.imap` -- Single IMAPClient instance (mutable: credentials can change via /api/connect)
- `app.state.claude` -- Single ClaudeClient instance
- `app.state.settings` -- Settings dataclass

There is no database. All email state lives on the IMAP server. This keeps the architecture simple but means:
- No offline access
- No caching (every inbox load hits the IMAP server)
- Connection timeouts need reconnection (handled by `_ensure_connected`)

## Why FastAPI?

- **Pydantic integration**: Request/response models are validated automatically
- **Auto-generated docs**: Visit `/docs` for an interactive Swagger UI of all endpoints
- **Type hints**: Clear contract between frontend and backend
- **Performance**: Built on Starlette/uvicorn, handles concurrent requests well

## Why Vanilla JS (No React/Vue)?

- **Zero build step**: No npm, webpack, or bundler. Edit a file, refresh the browser.
- **Educational**: Easier to understand the full request cycle without framework abstractions
- **Lightweight**: Three JS files totaling ~200 lines each
- **Sufficient**: The UI is simple enough that a framework would be overkill

## Security Model

- Credentials are stored in memory only (from .env or connect form)
- HTML email bodies are rendered in sandboxed iframes (no script execution)
- The API is designed for single-user local use, not public deployment
- IMAP connections use TLS (port 993)
- SMTP connections use STARTTLS (port 587)

## Extending the Project

Possible enhancements:
- **OAuth authentication**: Replace app passwords with OAuth2 for Gmail/Outlook
- **Caching**: Add a SQLite cache for email headers to reduce IMAP load
- **WebSocket**: Push real-time updates when new emails arrive (IMAP IDLE)
- **Batch operations**: Categorize/summarize multiple emails at once
- **Attachment preview**: Render common attachment types inline
- **Thread view**: Group emails by conversation thread (In-Reply-To/References headers)
