const App = {
  state: {
    connected: false,
    user: "",
    folders: [],
    activeFolder: "INBOX",
    emails: [],
    currentEmail: null,
    searchMode: false,
  },

  $main: null,
  $sidebar: null,
  $searchInput: null,
  $header: null,

  async init() {
    this.$main = document.getElementById("main-content");
    this.$sidebar = document.getElementById("sidebar");
    this.$searchInput = document.getElementById("search-input");
    this.$header = document.getElementById("header-status");

    // Check if already connected (e.g., env vars)
    try {
      const status = await API.status();
      if (status.connected) {
        this.state.connected = true;
        this.state.user = status.user;
        await this.loadInbox();
        return;
      }
    } catch {
      // Not connected, show form
    }

    this.showConnect();
  },

  showConnect() {
    this.$sidebar.innerHTML = "";
    this.$main.innerHTML = Components.connectForm();
    this.$header.textContent = "Disconnected";
    this.$header.className = "status disconnected";
    document.getElementById("search-bar").hidden = true;

    document.getElementById("connect-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = e.target.querySelector('button[type="submit"]');
      const errEl = document.getElementById("connect-error");
      btn.disabled = true;
      btn.textContent = "Connecting...";
      errEl.hidden = true;

      try {
        await API.connect({
          imap_host: document.getElementById("imap-host").value,
          imap_port: parseInt(document.getElementById("imap-port").value),
          imap_user: document.getElementById("imap-user").value,
          imap_password: document.getElementById("imap-password").value,
          smtp_host: document.getElementById("smtp-host").value,
          smtp_port: parseInt(document.getElementById("smtp-port").value),
        });
        this.state.connected = true;
        this.state.user = document.getElementById("imap-user").value;
        await this.loadInbox();
      } catch (err) {
        errEl.textContent = err.message;
        errEl.hidden = false;
        btn.disabled = false;
        btn.textContent = "Connect";
      }
    });
  },

  async loadInbox() {
    this.$header.textContent = this.state.user;
    this.$header.className = "status connected";
    document.getElementById("search-bar").hidden = false;
    this.state.searchMode = false;

    // Load folders
    try {
      const foldersResp = await API.folders();
      this.state.folders = foldersResp.folders;
      this.renderSidebar();
    } catch {
      this.$sidebar.innerHTML = '<div class="error-msg">Failed to load folders</div>';
    }

    // Load emails
    this.$main.innerHTML = Components.loading("Loading inbox...");
    try {
      const inbox = await API.inbox(this.state.activeFolder);
      this.state.emails = inbox.emails;
      this.renderEmailList();
    } catch (err) {
      this.$main.innerHTML = `<div class="error-msg">Failed to load emails: ${escapeHtml(err.message)}</div>`;
    }
  },

  renderSidebar() {
    this.$sidebar.innerHTML = Components.folderList(this.state.folders, this.state.activeFolder);

    this.$sidebar.querySelectorAll(".folder-item").forEach((el) => {
      el.addEventListener("click", async () => {
        this.state.activeFolder = el.dataset.folder;
        await this.loadInbox();
      });
    });
  },

  renderEmailList() {
    this.$main.innerHTML = `
      <div class="inbox-header">
        <h2>${escapeHtml(this.state.activeFolder)}</h2>
        <span class="email-count">${this.state.emails.length} emails</span>
      </div>
      <div class="email-list">${Components.emailList(this.state.emails)}</div>
    `;

    this.$main.querySelectorAll(".email-row").forEach((el) => {
      el.addEventListener("click", () => this.openEmail(el.dataset.uid));
    });
  },

  async openEmail(uid) {
    this.$main.innerHTML = Components.loading("Loading email...");
    try {
      const email = await API.email(uid, this.state.activeFolder);
      this.state.currentEmail = email;
      this.$main.innerHTML = Components.emailDetail(email);
      this.bindDetailEvents(email);
    } catch (err) {
      this.$main.innerHTML = `<div class="error-msg">Failed to load email: ${escapeHtml(err.message)}</div>`;
    }
  },

  bindDetailEvents(email) {
    document.getElementById("btn-back").addEventListener("click", () => {
      if (this.state.searchMode) {
        // Can't easily re-render search results, just go back to inbox
        this.loadInbox();
      } else {
        this.renderEmailList();
      }
    });

    document.getElementById("btn-summarize").addEventListener("click", async () => {
      const resultEl = document.getElementById("ai-result");
      resultEl.hidden = false;
      resultEl.innerHTML = Components.loading("Summarizing...");
      try {
        const resp = await API.summarize(email.uid);
        resultEl.innerHTML = `<div class="ai-card"><strong>Summary:</strong><p>${escapeHtml(resp.summary)}</p></div>`;
      } catch (err) {
        resultEl.innerHTML = `<div class="error-msg">${escapeHtml(err.message)}</div>`;
      }
    });

    document.getElementById("btn-action-items").addEventListener("click", async () => {
      const resultEl = document.getElementById("ai-result");
      resultEl.hidden = false;
      resultEl.innerHTML = Components.loading("Extracting action items...");
      try {
        const resp = await API.actionItems(email.uid);
        const items = resp.items.length
          ? `<ul>${resp.items.map((i) => `<li>${escapeHtml(i)}</li>`).join("")}</ul>`
          : "<p>No action items found.</p>";
        resultEl.innerHTML = `<div class="ai-card"><strong>Action Items:</strong>${items}</div>`;
      } catch (err) {
        resultEl.innerHTML = `<div class="error-msg">${escapeHtml(err.message)}</div>`;
      }
    });

    document.getElementById("btn-draft-reply").addEventListener("click", () => {
      document.getElementById("draft-input-area").hidden = false;
      document.getElementById("draft-instruction").focus();
    });

    document.getElementById("btn-generate-draft").addEventListener("click", async () => {
      const instruction = document.getElementById("draft-instruction").value;
      if (!instruction.trim()) return;

      const draftResult = document.getElementById("draft-result");
      draftResult.hidden = false;
      draftResult.innerHTML = Components.loading("Generating draft...");

      try {
        const resp = await API.draftReply(email.uid, instruction);
        draftResult.hidden = false;
        draftResult.innerHTML = `
          <h4>Draft Reply (${escapeHtml(resp.subject)})</h4>
          <textarea id="draft-text" rows="8">${escapeHtml(resp.draft)}</textarea>
          <div class="draft-actions">
            <button class="btn btn-primary" id="btn-send-draft">Send Reply</button>
          </div>
        `;
        document.getElementById("btn-send-draft").addEventListener("click", () => {
          this.sendDraft(email, resp.subject);
        });
      } catch (err) {
        draftResult.innerHTML = `<div class="error-msg">${escapeHtml(err.message)}</div>`;
      }
    });
  },

  async sendDraft(originalEmail, subject) {
    const body = document.getElementById("draft-text").value;
    const btn = document.getElementById("btn-send-draft");
    btn.disabled = true;
    btn.textContent = "Sending...";

    try {
      await API.send({
        to: originalEmail.sender,
        subject: subject,
        body: body,
      });
      btn.textContent = "Sent!";
      btn.className = "btn btn-success";
    } catch (err) {
      btn.disabled = false;
      btn.textContent = "Send Reply";
      alert("Failed to send: " + err.message);
    }
  },

  async doSearch(query) {
    if (!query.trim()) return;
    this.state.searchMode = true;
    this.$main.innerHTML = Components.loading("Searching with AI...");

    try {
      const result = await API.search(query);
      this.$main.innerHTML = Components.searchResults(result);

      // Bind click on search result emails
      this.$main.querySelectorAll(".email-row").forEach((el) => {
        el.addEventListener("click", () => this.openEmail(el.dataset.uid));
      });
    } catch (err) {
      this.$main.innerHTML = `<div class="error-msg">Search failed: ${escapeHtml(err.message)}</div>`;
    }
  },
};

// Boot
document.addEventListener("DOMContentLoaded", () => {
  App.init();

  // Search bar
  document.getElementById("search-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const input = document.getElementById("search-input");
    App.doSearch(input.value);
  });
});
