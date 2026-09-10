document.addEventListener("DOMContentLoaded", () => {
  const chatLog = document.getElementById("chat-log");
  const userInput = document.getElementById("user-input");
  const sendBtn = document.getElementById("send-btn");
  const clearBtn = document.getElementById("clear-chat-btn");
  const statusIndicator = document.getElementById("connection-status");
  const activeModelName = document.getElementById("active-model-name");
  const toolsList = document.getElementById("tools-list");

  let socket = null;
  let isGenerating = false;
  let activeToolCard = null;

  // Tab switching
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".view-panel").forEach((p) => p.classList.remove("active"));

      btn.classList.add("active");
      const target = document.getElementById(`${btn.dataset.tab}-tab`);
      if (target) target.classList.add("active");
    });
  });

  // Fetch status
  async function loadStatus() {
    try {
      const res = await fetch("/api/status");
      if (res.ok) {
        const data = await res.json();
        activeModelName.textContent = (data.model || "QWEN2:1.5B").toUpperCase();
        if (data.status === "online") {
          statusIndicator.className = "meta-badge online";
          statusIndicator.querySelector(".meta-text").textContent = "ONLINE";
        } else {
          statusIndicator.className = "meta-badge offline";
          statusIndicator.querySelector(".meta-text").textContent = "OFFLINE";
        }
      }
    } catch (e) {
      console.warn("Status offline:", e);
    }
  }

  // Fetch tools
  async function loadTools() {
    try {
      const res = await fetch("/api/tools");
      if (res.ok) {
        const data = await res.json();
        renderTools(data.tools || []);
      }
    } catch (e) {
      console.warn("Tools load failed:", e);
    }
  }

  function renderTools(tools) {
    if (!toolsList) return;
    toolsList.innerHTML = "";
    tools.forEach((tool) => {
      const box = document.createElement("div");
      box.className = "retro-tool-box";
      const shortcut = tool.slash_command ? `<span class="box-shortcut">CMD: ${tool.slash_command}</span>` : "";
      box.innerHTML = `
        <div class="box-head">
          <span class="box-tool-name">${tool.name.toUpperCase()}</span>
          <span class="box-perm ${tool.permission}">[${tool.permission}]</span>
        </div>
        <div class="box-desc">${escapeHtml(tool.description)}</div>
        ${shortcut}
      `;
      toolsList.appendChild(box);
    });
  }

  // WebSocket
  function initWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log("[VICTOR] WebSocket link established");
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        handleServerEvent(payload);
      } catch (err) {
        console.error("Message parse error", err);
      }
    };

    socket.onclose = () => {
      setTimeout(initWebSocket, 3000);
    };
  }

  function handleServerEvent(payload) {
    if (payload.type === "event") {
      const evt = payload.event;
      if (evt.topic === "tool.started") {
        createToolCard(evt.data.tool, evt.data.parameters);
      } else if (evt.topic === "tool.completed") {
        finishToolCard(evt.data.tool, evt.data.duration, evt.data.output);
      } else if (evt.topic === "tool.failed") {
        failToolCard(evt.data.tool, evt.data.error, evt.data.output);
      }
    } else if (payload.type === "chat_result") {
      appendVictorMessage(payload.data.content);
      setGenerating(false);
    }
  }

  function createToolCard(toolName, parameters) {
    const card = document.createElement("div");
    card.className = "retro-tool-card running";
    card.innerHTML = `
      <div class="tool-top-bar">
        <span>┌── [ EXEC: ${toolName.toUpperCase()} ]</span>
        <span>STATUS: BUSY</span>
      </div>
      <div class="tool-body-content">&gt; PARAMS: ${JSON.stringify(parameters)}</div>
    `;
    chatLog.appendChild(card);
    chatLog.scrollTop = chatLog.scrollHeight;
    activeToolCard = card;
  }

  function finishToolCard(toolName, duration, output) {
    if (activeToolCard) {
      activeToolCard.className = "retro-tool-card success";
      const durText = duration !== undefined ? `${duration}s` : "";
      activeToolCard.querySelector(".tool-top-bar").innerHTML = `
        <span>├── [ FINISHED: ${toolName.toUpperCase()} ]</span>
        <span>TIME: ${durText}</span>
      `;
      let preview = "";
      if (typeof output === "object") {
        if (output.formatted) {
          preview = output.formatted;
        } else if (output.results) {
          preview = output.results.map((r, i) => `[${i + 1}] ${r.title}\n    ${r.url}`).join("\n");
        } else {
          preview = JSON.stringify(output, null, 2);
        }
      } else {
        preview = String(output);
      }
      if (preview.length > 500) {
        preview = preview.slice(0, 500) + "... [truncated]";
      }
      activeToolCard.querySelector(".tool-body-content").textContent = preview;
    }
  }

  function failToolCard(toolName, error, output) {
    if (activeToolCard) {
      activeToolCard.className = "retro-tool-card failed";
      activeToolCard.querySelector(".tool-top-bar").innerHTML = `
        <span style="color:var(--red-alert)">├── [ FAILED: ${toolName.toUpperCase()} ]</span>
        <span style="color:var(--red-alert)">ERR: ${error || "FAIL"}</span>
      `;
      activeToolCard.querySelector(".tool-body-content").textContent = String(output);
    }
  }

  function appendUserMessage(text) {
    const msg = document.createElement("div");
    msg.className = "term-msg user-entry";
    const time = new Date().toTimeString().split(" ")[0];
    msg.innerHTML = `
      <div class="msg-wire">
        <span class="wire-label">[ USER // IN ]</span>
        <span class="wire-time">${time}</span>
      </div>
      <div class="msg-content">${escapeHtml(stripEmojis(text))}</div>
    `;
    chatLog.appendChild(msg);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  function appendVictorMessage(text) {
    const msg = document.createElement("div");
    msg.className = "term-msg victor-entry";
    const time = new Date().toTimeString().split(" ")[0];
    const cleaned = stripEmojis(text);
    msg.innerHTML = `
      <div class="msg-wire">
        <span class="wire-label">[ VICTOR // OUT ]</span>
        <span class="wire-time">${time}</span>
      </div>
      <div class="msg-content">${formatContent(cleaned)}</div>
    `;
    chatLog.appendChild(msg);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  function stripEmojis(str) {
    if (!str) return "";
    return str.replace(/([\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD10-\uDDFF])/g, "");
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatContent(str) {
    if (!str) return "";
    let clean = escapeHtml(str);
    clean = clean.replace(/```([a-zA-Z0-9]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      return `<pre><code>${code.trim()}</code></pre>`;
    });
    clean = clean.replace(/`([^`]+)`/g, "<code>$1</code>");
    clean = clean.replace(/\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    return clean;
  }

  function setGenerating(generating) {
    isGenerating = generating;
    sendBtn.disabled = generating;
    sendBtn.textContent = generating ? "[ BUSY... ]" : "[ EXEC ⏎ ]";
  }

  async function sendMessage() {
    const text = userInput.value.trim();
    if (!text || isGenerating) return;

    appendUserMessage(text);
    userInput.value = "";
    setGenerating(true);

    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ message: text }));
    } else {
      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text }),
        });
        const data = await res.json();
        appendVictorMessage(data.content);
      } catch (err) {
        appendVictorMessage(`[COMMUNICATION ERROR]: ${err}`);
      } finally {
        setGenerating(false);
      }
    }
  }

  // Clear chat
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      chatLog.innerHTML = "";
      appendVictorMessage("Context memory cleared. Node ready.");
      fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: "/clear", reset: true }),
      });
    });
  }

  // Quick chip click
  document.addEventListener("click", (e) => {
    if (e.target.classList.contains("cmd-chip") && e.target.dataset.prompt) {
      userInput.value = e.target.dataset.prompt;
      sendMessage();
    }
  });

  sendBtn.addEventListener("click", sendMessage);

  userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendMessage();
    }
  });

  // Init
  loadStatus();
  loadTools();
  initWebSocket();
});
