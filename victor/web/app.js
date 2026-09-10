document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const messageStream = document.getElementById("message-stream");
  const userInput = document.getElementById("user-input");
  const btnSubmit = document.getElementById("btn-submit");
  const btnClearFeed = document.getElementById("clear-feed-btn");
  const connPill = document.getElementById("conn-pill");
  const activeCoreModel = document.getElementById("active-core-model");
  const workflowPulseDot = document.getElementById("workflow-pulse-dot");
  const pipelineLastTime = document.getElementById("pipeline-last-time");
  const toolsCatalog = document.getElementById("tools-catalog");

  // Workflow Inspector Elements
  const nodeInspector = document.getElementById("node-inspector");
  const closeInspectorBtn = document.getElementById("close-inspector-btn");
  const inspNodeName = document.getElementById("insp-node-name");
  const inspNodeStatus = document.getElementById("insp-node-status");
  const inspNodeDuration = document.getElementById("insp-node-duration");
  const inspNodeData = document.getElementById("insp-node-data");

  // Node telemetry store
  const telemetryStore = {
    input: { name: "USER DIRECTIVE", status: "STANDBY", duration: "-", data: "Awaiting input." },
    magi: { name: "COGNITIVE PLANNER", status: "STANDBY", duration: "-", data: "Idle." },
    tool: { name: "TOOL EXECUTION", status: "STANDBY", duration: "-", data: "No tool active." },
    obs: { name: "OBSERVATION & DATA", status: "STANDBY", duration: "-", data: "No data buffered." },
    synth: { name: "NATURAL RECURSION", status: "STANDBY", duration: "-", data: "Awaiting synthesis." },
  };

  let socket = null;
  let isTransmitting = false;

  // Tab Navigation
  document.querySelectorAll(".nav-pill").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".nav-pill").forEach((p) => p.classList.remove("active"));
      document.querySelectorAll(".panel-section").forEach((sec) => sec.classList.remove("active"));

      btn.classList.add("active");
      const viewId = `view-${btn.dataset.view}`;
      const targetSec = document.getElementById(viewId);
      if (targetSec) targetSec.classList.add("active");
    });
  });

  // Fetch initial status
  async function loadStatus() {
    try {
      const res = await fetch("/api/status");
      if (res.ok) {
        const data = await res.json();
        activeCoreModel.textContent = (data.model || "QWEN2:1.5B").toUpperCase();
        if (data.status === "online") {
          connPill.className = "pill-badge status-online";
          connPill.querySelector(".pill-text").textContent = "ONLINE";
        } else {
          connPill.className = "pill-badge status-offline";
          connPill.querySelector(".pill-text").textContent = "OFFLINE";
        }
      }
    } catch (e) {
      console.warn("Status offline", e);
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
      console.warn("Tools load fail", e);
    }
  }

  function renderTools(tools) {
    if (!toolsCatalog) return;
    toolsCatalog.innerHTML = "";
    tools.forEach((tool) => {
      const card = document.createElement("div");
      card.className = "catalog-card";
      const shortcut = tool.slash_command ? `<div class="card-shortcut">DIRECTIVE: ${tool.slash_command}</div>` : "";
      card.innerHTML = `
        <div class="card-top">
          <span class="card-title">${tool.name.toUpperCase()}</span>
          <span class="card-badge ${tool.permission}">[${tool.permission}]</span>
        </div>
        <div class="card-desc">${escapeHtml(tool.description)}</div>
        ${shortcut}
      `;
      toolsCatalog.appendChild(card);
    });
  }

  // WebSocket
  function initWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log("[VICTOR // NERV] WebSocket telemetry linked");
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        handleServerPayload(payload);
      } catch (err) {
        console.error("Payload error", err);
      }
    };

    socket.onclose = () => {
      setTimeout(initWebSocket, 2500);
    };
  }

  // Live Workflow State Machine
  function resetWorkflowNodes() {
    const nodes = ["input", "magi", "tool", "obs", "synth"];
    nodes.forEach((n) => {
      setNodeState(n, "STANDBY", "standby");
    });
    document.querySelectorAll(".signal-wire").forEach((w) => w.classList.remove("active"));
    workflowPulseDot.classList.remove("pulsing");
  }

  function setNodeState(nodeKey, statusText, statusClass, previewText = null, rawData = null) {
    const nodeEl = document.getElementById(`node-${nodeKey}`);
    const statusEl = document.getElementById(`status-node-${nodeKey}`);
    const previewEl = document.getElementById(`preview-${nodeKey}`);

    if (nodeEl && statusEl) {
      nodeEl.className = `magi-node ${statusClass === "running" ? "active" : statusClass === "locked" ? "locked" : ""}`;
      statusEl.className = `node-status-pill ${statusClass}`;
      statusEl.textContent = statusText;

      if (previewText && previewEl) {
        previewEl.textContent = previewText;
      }

      telemetryStore[nodeKey].status = statusText;
      if (previewText) telemetryStore[nodeKey].data = previewText;
      if (rawData) telemetryStore[nodeKey].data = rawData;
    }
  }

  function handleServerPayload(payload) {
    if (payload.type === "event") {
      const evt = payload.event;
      const topic = evt.topic;
      const data = evt.data || {};

      if (topic === "agent.started") {
        workflowPulseDot.classList.add("pulsing");
        setNodeState("input", "LOCKED", "locked", data.user_message || data.command);
        setNodeState("magi", "PLANNING", "running", "Analyzing directive...");
        document.getElementById("path-1-2")?.classList.add("active");

      } else if (topic === "agent.thinking") {
        const state = data.state || "synthesizing";
        if (state === "synthesizing") {
          setNodeState("synth", "SYNTHESIS", "running", "Formulating natural response...");
          document.getElementById("path-4-5")?.classList.add("active");
        }

      } else if (topic === "tool.started") {
        const toolName = data.tool || "tool";
        setNodeState("magi", "LOCKED", "locked", `Selected: ${toolName}`);
        document.getElementById("path-2-3")?.classList.add("active");
        setNodeState("tool", "RUNNING", "running", `Executing ${toolName}`, data.parameters);

      } else if (topic === "tool.completed") {
        const toolName = data.tool || "tool";
        const dur = data.duration !== undefined ? `${data.duration}s` : "OK";
        setNodeState("tool", `LOCKED [${dur}]`, "locked", `${toolName} finished in ${dur}`, data.output);
        telemetryStore.tool.duration = dur;

        document.getElementById("path-3-4")?.classList.add("active");
        setNodeState("obs", "BUFFERED", "locked", "Observation formatted", data.output);

      } else if (topic === "tool.failed") {
        setNodeState("tool", "FAILED", "standby", data.error, data.output);

      } else if (topic === "agent.completed") {
        const dur = data.duration !== undefined ? `${data.duration}s` : "0.0s";
        setNodeState("synth", `LOCKED [${dur}]`, "locked", "Natural output stream ready");
        telemetryStore.synth.duration = dur;
        if (pipelineLastTime) pipelineLastTime.textContent = dur;
        workflowPulseDot.classList.remove("pulsing");
        setTimeout(() => {
          document.querySelectorAll(".signal-wire").forEach((w) => w.classList.remove("active"));
        }, 1200);
      }

    } else if (payload.type === "chat_result") {
      appendVictorPacket(payload.data.content);
      setTransmitting(false);
    }
  }

  // Interactive Node Inspector
  document.querySelectorAll(".magi-node").forEach((node) => {
    node.addEventListener("click", () => {
      const nodeKey = node.dataset.node;
      const info = telemetryStore[nodeKey];
      if (info) {
        inspNodeName.textContent = info.name;
        inspNodeStatus.textContent = info.status;
        inspNodeDuration.textContent = info.duration || "-";
        
        let displayData = info.data;
        if (typeof displayData === "object") {
          displayData = JSON.stringify(displayData, null, 2);
        }
        inspNodeData.textContent = displayData;
        nodeInspector.classList.add("open");
      }
    });
  });

  if (closeInspectorBtn) {
    closeInspectorBtn.addEventListener("click", () => {
      nodeInspector.classList.remove("open");
    });
  }

  const btnReplay = document.getElementById("btn-replay-trace");
  if (btnReplay) {
    btnReplay.addEventListener("click", resetWorkflowNodes);
  }

  // Chat stream rendering
  function appendUserPacket(text) {
    const packet = document.createElement("div");
    packet.className = "speech-packet user-packet";
    const time = new Date().toTimeString().split(" ")[0];
    packet.innerHTML = `
      <div class="packet-head">
        <span class="packet-author">USER</span>
        <span class="packet-time">${time}</span>
        <span class="packet-sig">SIG: DIRECTIVE_IN</span>
      </div>
      <div class="packet-body">${escapeHtml(stripEmojis(text))}</div>
    `;
    messageStream.appendChild(packet);
    messageStream.scrollTop = messageStream.scrollHeight;
  }

  function appendVictorPacket(text) {
    const packet = document.createElement("div");
    packet.className = "speech-packet victor-packet";
    const time = new Date().toTimeString().split(" ")[0];
    const cleanText = stripEmojis(text);
    packet.innerHTML = `
      <div class="packet-head">
        <span class="packet-author">VICTOR</span>
        <span class="packet-time">${time}</span>
        <span class="packet-sig">SIG: SYNTH_OUT</span>
      </div>
      <div class="packet-body">${formatMarkdownText(cleanText)}</div>
    `;
    messageStream.appendChild(packet);
    messageStream.scrollTop = messageStream.scrollHeight;
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

  function formatMarkdownText(str) {
    if (!str) return "";
    let clean = escapeHtml(str);
    // Code blocks
    clean = clean.replace(/```([a-zA-Z0-9]*)\n([\s\S]*?)```/g, (m, lang, code) => {
      return `<pre><code>${code.trim()}</code></pre>`;
    });
    // Inline code
    clean = clean.replace(/`([^`]+)`/g, "<code>$1</code>");
    // Bold
    clean = clean.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    // Markdown links
    clean = clean.replace(/\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    return clean;
  }

  function setTransmitting(transmitting) {
    isTransmitting = transmitting;
    btnSubmit.disabled = transmitting;
    btnSubmit.querySelector("span").textContent = transmitting ? "SYNCING..." : "TRANSMIT";
  }

  async function sendDirective() {
    const text = userInput.value.trim();
    if (!text || isTransmitting) return;

    appendUserPacket(text);
    userInput.value = "";
    setTransmitting(true);

    // Reset workflow nodes for the new trace
    resetWorkflowNodes();
    setNodeState("input", "INGESTING", "running", text);

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
        appendVictorPacket(data.content);
        setNodeState("synth", "LOCKED", "locked", "Synthesized response ready");
      } catch (err) {
        appendVictorPacket(`[COMMUNICATION ERROR]: ${err}`);
      } finally {
        setTransmitting(false);
      }
    }
  }

  // Clear feed
  if (btnClearFeed) {
    btnClearFeed.addEventListener("click", () => {
      messageStream.innerHTML = "";
      appendVictorPacket("Memory feed wiped. Ready for new input.");
      resetWorkflowNodes();
      fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: "/clear", reset: true }),
      });
    });
  }

  // Quick Action Chips
  document.querySelectorAll(".chip-action").forEach((btn) => {
    btn.addEventListener("click", () => {
      const cmd = btn.dataset.cmd;
      if (cmd) {
        userInput.value = cmd;
        sendDirective();
      }
    });
  });

  btnSubmit.addEventListener("click", sendDirective);

  userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendDirective();
    }
  });

  // Init
  loadStatus();
  loadTools();
  initWebSocket();
});
