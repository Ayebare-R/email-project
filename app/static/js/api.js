const API = {
  async post(url, data) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Request failed");
    }
    return res.json();
  },

  async get(url) {
    const res = await fetch(url);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Request failed");
    }
    return res.json();
  },

  // Auth
  connect(data) {
    return this.post("/api/connect", data);
  },
  status() {
    return this.get("/api/status");
  },

  // Inbox
  folders() {
    return this.get("/api/folders");
  },
  inbox(folder = "INBOX", limit = 50) {
    return this.get(`/api/inbox?folder=${encodeURIComponent(folder)}&limit=${limit}`);
  },
  email(uid, folder = "INBOX") {
    return this.get(`/api/email/${uid}?folder=${encodeURIComponent(folder)}`);
  },

  // Search
  search(query) {
    return this.post("/api/search", { query });
  },

  // AI
  summarize(uid) {
    return this.post("/api/summarize", { uid });
  },
  draftReply(uid, instruction) {
    return this.post("/api/draft-reply", { uid, instruction });
  },
  categorize(uids) {
    return this.post("/api/categorize", { uids });
  },
  actionItems(uid) {
    return this.post("/api/action-items", { uid });
  },

  // Send
  send(data) {
    return this.post("/api/send", data);
  },
};
