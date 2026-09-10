document.addEventListener("DOMContentLoaded", () => {
  const chatMessages = document.getElementById("chat-messages");
  const userInput = document.getElementById("user-input");
  const sendBtn = document.getElementById("send-btn");
  const statusIndicator = document.getElementById("connection-status");
  const activeModelName = document.getElementById("active-model-name");
  const toolsCountBadge = document.getElementById("tools-count-badge");
  const toolsListContainer = document.getElementById("tools-list-container");

  let socket = null;
  let isGenerating = false;
  let currentToolCard = null;

  // Tab navigation
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".nav-item").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".view-tab").forEach((tab) => tab.classList.remove("active"));

      btn.classList.add("active");
      const targetId = `${btn.dataset.tab}-tab`;
      const targetView = document.getElementById(targetId);
      if (targetView) targetView.classList.add("active");
    });
  });

  // Fetch initial status and tools
  async function loadStatus() {
    try {
      const res = await fetch("/api/status");
      if (res.ok) {
        const data = await res.json();
        activeModelName.textContent = data.model || "qwen2:1.5b";
        toolsCountBadge.textContent = data.tools_count;
        if (data.status === "online") {
          statusIndicator.classList.remove("offline");
          statusIndicator.classList.add("online");
          statusIndicator.querySelector(".status-text").textContent = "ONLINE";
        } else {
          statusIndicator.classList.remove("online");
          statusIndicator.classList.add("offline");
          statusIndicator.querySelector(".status-text").textContent = "OFFLINE";
        }
      }
    } catch (e) {
      console.warn("Status check failed:", e);
    }
  }

  async function loadTools() {
    try {
      const res = await fetch("/api/tools");
      if (res.ok) {
        const data = await res.json();
        renderTools(data.tools || []);
      }
    } catch (e) {
      console.warn("Load tools failed:", e);
    }
  }

  function renderTools(tools) {
    if (!toolsListContainer) return;
    toolsListContainer.innerHTML = "";
    tools.forEach((tool) => {
      const card = document.createElement("div");
      card.className = "tool-card";
      const shortcut = tool.slash_command ? `<div class="tool-shortcut">${tool.slash_command}</div>` : "";
      card.innerHTML = `
        <div class="tool-card-head">
          <span class="tool-title">${tool.name}</span>
          <span class="perm-pill ${tool.permission}">${tool.permission}</span>
        </div>
        <p class="tool-desc">${tool.description}</p>
        ${shortcut}
      `;
      toolsListContainer.appendChild(card);
    });
  }

  // WebSocket Connection
  function initWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log("[Victor] WebSocket connected");
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        handleServerEvent(payload);
      } catch (err) {
        console.error("Error parsing message", err);
      }
    };

    socket.onclose = () => {
      console.warn("[Victor] WebSocket disconnected, reconnecting in 3s...");
      setTimeout(initWebSocket, 3000);
    };
  }

  function handleServerEvent(payload) {
    if (payload.type === "event") {
      const evt = payload.event;
      if (evt.topic === "tool.started") {
        createToolCard(evt.data.tool, evt.data.parameters);
      } else if (evt.topic === "tool.completed") {
        completeToolCard(evt.data.tool, evt.data.duration, evt.data.output);
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
    card.className = "tool-execution-card running";
    card.innerHTML = `
      <div class="tool-header-line">
        <span>┌ Executing: ${toolName}...</span>
        <span class="tool-duration">Running</span>
      </div>
      <div class="tool-details-content">${JSON.stringify(parameters, null, 2)}</div>
    `;
    chatMessages.appendChild(card);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    currentToolCard = card;
  }

  function completeToolCard(toolName, duration, output) {
    if (currentToolCard) {
      currentToolCard.className = "tool-execution-card success";
      const durationText = duration !== undefined ? `${duration}s` : "";
      currentToolCard.querySelector(".tool-header-line").innerHTML = `
        <span>└ ${toolName} completed</span>
        <span class="tool-duration">${durationText}</span>
      `;
      let preview = "";
      if (typeof output === "object") {
        preview = JSON.stringify(output, null, 2);
      } else {
        preview = String(output);
      }
      if (preview.length > 300) {
        preview = preview.slice(0, 300) + "... [truncated]";
      }
      currentToolCard.querySelector(".tool-details-content").textContent = preview;
    }
  }

  function failToolCard(toolName, error, output) {
    if (currentToolCard) {
      currentToolCard.className = "tool-execution-card failed";
      currentToolCard.querySelector(".tool-header-line").innerHTML = `
        <span style="color:var(--danger-red)">└ ${toolName} failed: ${error || "Error"}</span>
      `;
      currentToolCard.querySelector(".tool-details-content").textContent = String(output);
    }
  }

  function appendUserMessage(text) {
    const msg = document.createElement("div");
    msg.className = "message-card user-message";
    const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    msg.innerHTML = `
      <div class="msg-avatar">U</div>
      <div class="msg-body">
        <div class="msg-header">
          <span class="msg-author">You</span>
          <span class="msg-time">${time}</span>
        </div>
        <div class="msg-text">${escapeHtml(text)}</div>
      </div>
    `;
    chatMessages.appendChild(msg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendVictorMessage(text) {
    const msg = document.createElement("div");
    msg.className = "message-card victor-message";
    const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    msg.innerHTML = `
      <div class="msg-avatar">V</div>
      <div class="msg-body">
        <div class="msg-header">
          <span class="msg-author">Victor</span>
          <span class="msg-time">${time}</span>
        </div>
        <div class="msg-text">${formatMarkdown(text)}</div>
      </div>
    `;
    chatMessages.appendChild(msg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatMarkdown(str) {
    if (!str) return "";
    let clean = escapeHtml(str);
    // Format code blocks
    clean = clean.replace(/```([a-zA-Z0-9]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      return `<pre><code class="${lang}">${code.trim()}</code></pre>`;
    });
    // Format inline code
    clean = clean.replace(/`([^`]+)`/g, "<code>$1</code>");
    // Format bold
    clean = clean.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    // Format links
    clean = clean.replace(/\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    return clean;
  }

  function setGenerating(generating) {
    isGenerating = generating;
    sendBtn.disabled = generating;
    if (generating) {
      sendBtn.querySelector("span").textContent = "...";
    } else {
      sendBtn.querySelector("span").textContent = "Send";
    }
  }

  async function sendMessage() {
    const text = userInput.value.trim();
    if (!text || isGenerating) return;

    appendUserMessage(text);
    userInput.value = "";
    userInput.style.height = "auto";
    setGenerating(true);

    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ message: text }));
    } else {
      // Fallback to REST endpoint
      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text }),
        });
        const data = await res.json();
        appendVictorMessage(data.content);
      } catch (err) {
        appendVictorMessage(`Encountered error communicating with Victor core: ${err}`);
      } finally {
        setGenerating(false);
      }
    }
  }

  // Quick chip click handlers
  document.addEventListener("click", (e) => {
    if (e.target.classList.contains("chip-btn")) {
      const prompt = e.target.dataset.prompt;
      if (prompt) {
        userInput.value = prompt;
        sendMessage();
      }
    }
  });

  sendBtn.addEventListener("click", sendMessage);

  userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  userInput.addEventListener("input", () => {
    userInput.style.height = "auto";
    userInput.style.height = Math.min(userInput.scrollHeight, 120) + "px";
  });

  // Initialize
  loadStatus();
  loadTools();
  initWebSocket();
});
