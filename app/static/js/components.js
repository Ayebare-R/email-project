const Components = {
  connectForm() {
    return `
      <div class="connect-card">
        <h2>Connect to Email Server</h2>
        <p class="subtitle">Enter your IMAP credentials to get started. For Gmail, use an App Password.</p>
        <form id="connect-form">
          <div class="form-row">
            <div class="form-group">
              <label>IMAP Host</label>
              <input type="text" id="imap-host" value="imap.gmail.com" required>
            </div>
            <div class="form-group form-group-small">
              <label>Port</label>
              <input type="number" id="imap-port" value="993" required>
            </div>
          </div>
          <div class="form-group">
            <label>Email</label>
            <input type="email" id="imap-user" placeholder="you@gmail.com" required>
          </div>
          <div class="form-group">
            <label>Password (App Password)</label>
            <input type="password" id="imap-password" required>
          </div>
          <details class="smtp-details">
            <summary>SMTP Settings (for sending)</summary>
            <div class="form-row">
              <div class="form-group">
                <label>SMTP Host</label>
                <input type="text" id="smtp-host" value="smtp.gmail.com">
              </div>
              <div class="form-group form-group-small">
                <label>Port</label>
                <input type="number" id="smtp-port" value="587">
              </div>
            </div>
          </details>
          <button type="submit" class="btn btn-primary">Connect</button>
          <div id="connect-error" class="error-msg" hidden></div>
        </form>
      </div>
    `;
  },

  folderList(folders, activeFolder) {
    const items = folders
      .map(
        (f) =>
          `<li class="folder-item ${f === activeFolder ? "active" : ""}" data-folder="${f}">${f}</li>`
      )
      .join("");
    return `<ul class="folder-list">${items}</ul>`;
  },

  emailList(emails) {
    if (!emails.length) {
      return '<div class="empty-state">No emails found</div>';
    }
    return emails
      .map(
        (e) => `
        <div class="email-row ${e.is_read ? "read" : "unread"}" data-uid="${e.uid}">
          <div class="email-sender">${escapeHtml(e.sender)}</div>
          <div class="email-subject">${escapeHtml(e.subject)}</div>
          <div class="email-date">${formatDate(e.date)}</div>
        </div>`
      )
      .join("");
  },

  emailDetail(email) {
    const body = email.body_html
      ? `<iframe class="email-body-frame" sandbox="" srcdoc="${escapeAttr(email.body_html)}"></iframe>`
      : `<pre class="email-body-plain">${escapeHtml(email.body_plain)}</pre>`;

    const attachments = email.attachments.length
      ? `<div class="attachments">
          <strong>Attachments:</strong>
          ${email.attachments.map((a) => `<span class="attachment-badge">${escapeHtml(a.filename)} (${formatBytes(a.size)})</span>`).join("")}
        </div>`
      : "";

    return `
      <div class="email-detail">
        <div class="email-detail-header">
          <button class="btn btn-back" id="btn-back">&larr; Back</button>
          <h2>${escapeHtml(email.subject)}</h2>
          <div class="email-meta">
            <span><strong>From:</strong> ${escapeHtml(email.sender)}</span>
            <span><strong>To:</strong> ${email.to.map(escapeHtml).join(", ")}</span>
            ${email.cc.length ? `<span><strong>CC:</strong> ${email.cc.map(escapeHtml).join(", ")}</span>` : ""}
            <span><strong>Date:</strong> ${formatDate(email.date)}</span>
          </div>
          ${attachments}
        </div>
        <div class="email-detail-body">${body}</div>
        <div class="ai-actions">
          <h3>AI Assistant</h3>
          <div class="ai-buttons">
            <button class="btn btn-ai" id="btn-summarize">Summarize</button>
            <button class="btn btn-ai" id="btn-action-items">Action Items</button>
            <button class="btn btn-ai" id="btn-draft-reply">Draft Reply</button>
          </div>
          <div id="ai-result" class="ai-result" hidden></div>
          <div id="draft-input-area" hidden>
            <textarea id="draft-instruction" placeholder="e.g. Politely decline the meeting, suggest next week instead"></textarea>
            <button class="btn btn-primary" id="btn-generate-draft">Generate Draft</button>
          </div>
          <div id="draft-result" hidden>
            <h4>Draft Reply</h4>
            <textarea id="draft-text" rows="8"></textarea>
            <div class="draft-actions">
              <button class="btn btn-primary" id="btn-send-draft">Send Reply</button>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  searchResults(result) {
    return `
      <div class="search-results">
        <div class="search-summary">
          <h3>Search Results</h3>
          <div class="ai-summary">${escapeHtml(result.summary)}</div>
          <div class="imap-query">
            <strong>IMAP Query:</strong> <code>${escapeHtml(result.imap_query)}</code>
          </div>
        </div>
        <div class="search-email-list">
          ${this.emailList(result.emails)}
        </div>
      </div>
    `;
  },

  loading(message = "Loading...") {
    return `<div class="loading"><div class="spinner"></div><span>${message}</span></div>`;
  },
};

// Utility functions
function escapeHtml(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function escapeAttr(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function formatDate(dateStr) {
  if (!dateStr) return "";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}
