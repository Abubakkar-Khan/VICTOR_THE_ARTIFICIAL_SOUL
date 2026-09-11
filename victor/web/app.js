/**
 * VICTOR — THE ARTIFICIAL SOUL // Modern Control Center Orchestration Engine
 * Complete client implementation with 7 views, integrated animated mascot,
 * Web Speech API (STT & TTS), real-time hierarchical flow, tasks, and memory.
 */

document.addEventListener("DOMContentLoaded", () => {
  // ---------------------------------------------------------------------------
  // 1. Navigation & State
  // ---------------------------------------------------------------------------
  const navItems = document.querySelectorAll(".nav-item");
  const viewPanels = document.querySelectorAll(".view-panel");
  const viewTitle = document.getElementById("view-title");
  const activeModelPill = document.getElementById("active-model-pill");

  // Chat Elements
  const chatFeed = document.getElementById("chat-feed");
  const userChatInput = document.getElementById("user-chat-input");
  const btnChatSend = document.getElementById("btn-chat-send");
  const btnClearChat = document.getElementById("btn-clear-chat");
  const btnExportChat = document.getElementById("btn-export-chat");
  const btnVoiceMic = document.getElementById("btn-voice-mic");
  const btnTtsToggle = document.getElementById("btn-tts-toggle");
  const ttsLabel = document.getElementById("tts-label");

  // Mascot Elements
  const mascotSvg = document.getElementById("mascot-svg");
  const mascotStatePill = document.getElementById("mascot-state-pill");
  const mascotSpeechText = document.getElementById("mascot-speech-text");
  const btnLaunchDesktopMascot = document.getElementById("btn-launch-desktop-mascot");
  const btnSettingsLaunchMascot = document.getElementById("btn-settings-launch-mascot");

  // Workflow Elements
  const workflowTreeNodes = document.getElementById("workflow-tree-nodes");
  const wfBeaconDot = document.getElementById("wf-beacon-dot");
  const flowDrawer = document.getElementById("flow-drawer");
  const btnCloseDrawer = document.getElementById("btn-close-drawer");
  const drawerTitle = document.getElementById("drawer-title");
  const drawerStatus = document.getElementById("drawer-status");
  const drawerPayload = document.getElementById("drawer-payload");
  const btnResetWorkflow = document.getElementById("btn-reset-workflow");

  // Tasks & Memory Elements
  const tasksGrid = document.getElementById("tasks-grid");
  const badgeTasksCount = document.getElementById("badge-tasks-count");
  const factsList = document.getElementById("facts-list");
  const preferencesList = document.getElementById("preferences-list");
  const newFactInput = document.getElementById("new-fact-input");
  const btnAddFact = document.getElementById("btn-add-fact");

  // Tools & Models Elements
  const toolsGrid = document.getElementById("tools-grid");
  const modelsList = document.getElementById("models-list");
  const modelActiveVal = document.getElementById("model-active-val");
  const modelProviderVal = document.getElementById("model-provider-val");

  // Settings & Permission Modal Elements
  const ttsVoiceSelect = document.getElementById("tts-voice-select");
  const ttsRateRange = document.getElementById("tts-rate-range");
  const permissionModal = document.getElementById("permission-modal");
  const permTitle = document.getElementById("perm-title");
  const permDesc = document.getElementById("perm-desc");
  const permDetails = document.getElementById("perm-details");
  const btnPermAllowOnce = document.getElementById("btn-perm-allow-once");
  const btnPermAlwaysAllow = document.getElementById("btn-perm-always-allow");
  const btnPermDeny = document.getElementById("btn-perm-deny");

  let socket = null;
  let isTransmitting = false;
  let ttsEnabled = localStorage.getItem("victor_tts_enabled") !== "false";
  let activePermRequestId = null;

  const viewHeadlines = {
    chat: "Conversation",
    workflow: "Live Execution Flow",
    tasks: "Autonomous Tasks",
    memory: "Persistent Memory",
    tools: "Capabilities & Tools",
    models: "Model Architecture",
    settings: "Settings & Controls",
  };

  function switchView(viewName) {
    navItems.forEach((btn) => btn.classList.toggle("active", btn.dataset.view === viewName));
    viewPanels.forEach((p) => p.classList.toggle("active", p.id === `view-${viewName}`));
    if (viewTitle) viewTitle.textContent = viewHeadlines[viewName] || "Workspace";

    // Refresh specific view data on switch
    if (viewName === "tasks") loadTasks();
    if (viewName === "memory") loadMemory();
    if (viewName === "tools") loadTools();
    if (viewName === "models") loadModels();
  }

  navItems.forEach((btn) => {
    btn.addEventListener("click", () => switchView(btn.dataset.view));
  });

  // ---------------------------------------------------------------------------
  // 2. Animated Mascot State Machine
  // ---------------------------------------------------------------------------
  let currentMascotState = "idle";

  function setMascotState(state, speech = "") {
    currentMascotState = state;
    if (mascotSvg) {
      mascotSvg.className = `mascot-svg ${state}`;
    }
    if (mascotStatePill) {
      mascotStatePill.className = `state-pill ${state}`;
      mascotStatePill.textContent = state.toUpperCase();
    }
    if (speech && mascotSpeechText) {
      mascotSpeechText.textContent = speech.slice(0, 95);
    }
  }

  // ---------------------------------------------------------------------------
  // 3. Voice Support: Speech Recognition (STT) & Speech Synthesis (TTS)
  // ---------------------------------------------------------------------------
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition = null;
  let isListening = false;

  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      isListening = true;
      if (btnVoiceMic) btnVoiceMic.classList.add("listening");
      setMascotState("listening", "Listening to your voice...");
    };

    recognition.onresult = (event) => {
      let transcript = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        transcript += event.results[i][0].transcript;
      }
      if (userChatInput) {
        userChatInput.value = transcript;
      }
    };

    recognition.onend = () => {
      isListening = false;
      if (btnVoiceMic) btnVoiceMic.classList.remove("listening");
      if (userChatInput && userChatInput.value.trim()) {
        sendUserMessage();
      } else {
        setMascotState("idle", "Standing by.");
      }
    };

    recognition.onerror = () => {
      isListening = false;
      if (btnVoiceMic) btnVoiceMic.classList.remove("listening");
      setMascotState("idle");
    };
  }

  if (btnVoiceMic) {
    btnVoiceMic.addEventListener("click", () => {
      if (!recognition) {
        alert("Web Speech API recognition is not supported in this browser.");
        return;
      }
      if (isListening) {
        recognition.stop();
      } else {
        recognition.start();
      }
    });
  }

  // TTS Setup
  function updateTtsButtonUI() {
    if (ttsLabel) ttsLabel.textContent = ttsEnabled ? "Voice: On" : "Voice: Off";
    if (btnTtsToggle) btnTtsToggle.classList.toggle("active", ttsEnabled);
  }
  updateTtsButtonUI();

  if (btnTtsToggle) {
    btnTtsToggle.addEventListener("click", () => {
      ttsEnabled = !ttsEnabled;
      localStorage.setItem("victor_tts_enabled", ttsEnabled ? "true" : "false");
      updateTtsButtonUI();
    });
  }

  let voices = [];
  function populateVoices() {
    if (!window.speechSynthesis || !ttsVoiceSelect) return;
    voices = window.speechSynthesis.getVoices();
    ttsVoiceSelect.innerHTML = "";
    voices.forEach((v, i) => {
      const opt = document.createElement("option");
      opt.value = i;
      opt.textContent = `${v.name} (${v.lang})`;
      if (v.default || v.name.includes("Google") || v.name.includes("Natural")) {
        opt.selected = true;
      }
      ttsVoiceSelect.appendChild(opt);
    });
  }

  if (window.speechSynthesis) {
    populateVoices();
    window.speechSynthesis.onvoiceschanged = populateVoices;
  }

  function speakText(text) {
    if (!ttsEnabled || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();

    const cleanText = text.replace(/`{1,3}[\s\S]*?`{1,3}/g, "").replace(/\[([^\]]+)\]\([^\)]+\)/g, "$1");
    const utterance = new SpeechSynthesisUtterance(cleanText);
    if (ttsVoiceSelect && voices[ttsVoiceSelect.value]) {
      utterance.voice = voices[ttsVoiceSelect.value];
    }
    if (ttsRateRange) {
      utterance.rate = parseFloat(ttsRateRange.value) || 1.0;
    }
    window.speechSynthesis.speak(utterance);
  }

  // ---------------------------------------------------------------------------
  // 4. Borderless Chat Presentation
  // ---------------------------------------------------------------------------
  function stripEmojis(str) {
    if (!str) return "";
    return str.replace(
      /([\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD10-\uDDFF])/g,
      ""
    );
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
    clean = clean.replace(/```([a-zA-Z0-9]*)\n([\s\S]*?)```/g, (m, lang, code) => `<pre><code>${code.trim()}</code></pre>`);
    clean = clean.replace(/`([^`]+)`/g, "<code>$1</code>");
    clean = clean.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    clean = clean.replace(/\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    return clean;
  }

  function appendUserMessage(text) {
    const row = document.createElement("div");
    row.className = "chat-row user-row";
    const time = new Date().toTimeString().split(" ")[0].slice(0, 5);

    row.innerHTML = `
      <div class="avatar-capsule">U</div>
      <div class="speech-content">
        <div class="speech-header">
          <span class="speech-author">User</span>
          <span class="speech-time">${time}</span>
        </div>
        <div class="speech-body">${escapeHtml(stripEmojis(text))}</div>
      </div>
    `;

    chatFeed.appendChild(row);
    chatFeed.scrollTop = chatFeed.scrollHeight;
  }

  function appendVictorMessage(text) {
    const row = document.createElement("div");
    row.className = "chat-row victor-row";
    const time = new Date().toTimeString().split(" ")[0].slice(0, 5);
    const clean = stripEmojis(text);

    row.innerHTML = `
      <div class="avatar-capsule">V</div>
      <div class="speech-content">
        <div class="speech-header">
          <span class="speech-author">Victor</span>
          <span class="speech-time">${time}</span>
        </div>
        <div class="speech-body">${formatMarkdown(clean)}</div>
        <button class="btn-copy-reply">Copy</button>
      </div>
    `;

    const copyBtn = row.querySelector(".btn-copy-reply");
    if (copyBtn) {
      copyBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(clean).then(() => {
          copyBtn.textContent = "Copied!";
          setTimeout(() => (copyBtn.textContent = "Copy"), 1500);
        });
      });
    }

    chatFeed.appendChild(row);
    chatFeed.scrollTop = chatFeed.scrollHeight;

    // Speak response
    speakText(clean);
  }

  // ---------------------------------------------------------------------------
  // 5. WebSocket & Real-Time Telemetry
  // ---------------------------------------------------------------------------
  function setTransmitting(active) {
    isTransmitting = active;
    if (btnChatSend) {
      btnChatSend.disabled = active;
      btnChatSend.querySelector("span").textContent = active ? "Thinking..." : "Send";
    }
  }

  function initWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log("[Victor] WebSocket connected");
      setMascotState("idle", "Connected and standing by.");
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        handleServerMessage(payload);
      } catch (err) {
        console.error("Payload error:", err);
      }
    };

    socket.onclose = () => {
      setTimeout(initWebSocket, 2500);
    };
  }

  function handleServerMessage(payload) {
    if (payload.type === "event") {
      const evt = payload.event;
      const topic = evt.topic;
      const data = evt.data || {};

      if (topic === "agent.started") {
        setMascotState("listening", "Processing your directive...");
        if (wfBeaconDot) wfBeaconDot.classList.add("pulsing");

      } else if (topic === "mascot.state_changed") {
        setMascotState(data.state || "idle", data.message || "");

      } else if (topic === "agent.hierarchical_plan") {
        renderWorkflowTree(data.plan?.nodes || []);

      } else if (topic === "tool.started") {
        setMascotState("working", `Executing ${data.tool}...`);
        updateNodeState(data.tool, "running");

      } else if (topic === "tool.completed") {
        setMascotState("working", `Completed ${data.tool}.`);
        updateNodeState(data.tool, "completed", data.output);

      } else if (topic === "agent.thinking") {
        setMascotState("thinking", "Synthesizing answer...");

      } else if (topic === "agent.completed") {
        setMascotState("completed", "Task finished.");
        if (wfBeaconDot) wfBeaconDot.classList.remove("pulsing");

      } else if (topic === "permission.requested") {
        promptPermissionModal(data);
      }

    } else if (payload.type === "chat_result") {
      appendVictorMessage(payload.data.content);
      setTransmitting(false);
      setMascotState("completed", "Done!");
      setTimeout(() => setMascotState("idle", "Ready for next directive."), 3000);
      loadTasks();
    }
  }

  async function sendUserMessage() {
    const text = userChatInput.value.trim();
    if (!text || isTransmitting) return;

    appendUserMessage(text);
    userChatInput.value = "";
    setTransmitting(true);
    setMascotState("thinking", "Analyzing request...");

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
        appendVictorMessage(`Communication error: ${err}`);
      } finally {
        setTransmitting(false);
        setMascotState("idle");
      }
    }
  }

  if (btnChatSend) btnChatSend.addEventListener("click", sendUserMessage);
  if (userChatInput) {
    userChatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        sendUserMessage();
      }
    });
  }

  // Suggestion Chips
  document.querySelectorAll(".chip-btn").forEach((chip) => {
    chip.addEventListener("click", () => {
      const q = chip.dataset.query;
      if (q && userChatInput) {
        userChatInput.value = q;
        sendUserMessage();
      }
    });
  });

  // Clear & Export Chat
  if (btnClearChat) {
    btnClearChat.addEventListener("click", () => {
      chatFeed.innerHTML = "";
      appendVictorMessage("Conversation cleared. How can I help you?");
      fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: "/clear", reset: true }),
      });
    });
  }

  if (btnExportChat) {
    btnExportChat.addEventListener("click", () => {
      const rows = chatFeed.querySelectorAll(".chat-row");
      let md = `# Victor — Conversation Export\nDate: ${new Date().toISOString()}\n\n`;
      rows.forEach((r) => {
        const isUser = r.classList.contains("user-row");
        const author = isUser ? "User" : "Victor";
        const body = r.querySelector(".speech-body")?.innerText || "";
        md += `### ${author}\n${body}\n\n`;
      });
      const blob = new Blob([md], { type: "text/markdown" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `victor-chat-${Date.now()}.md`;
      a.click();
    });
  }

  // ---------------------------------------------------------------------------
  // 6. Workflow Tree Renderer
  // ---------------------------------------------------------------------------
  let currentTreeNodes = [];

  function renderWorkflowTree(nodes) {
    if (!workflowTreeNodes) return;
    currentTreeNodes = nodes;
    workflowTreeNodes.innerHTML = "";

    nodes.forEach((node) => {
      const card = document.createElement("div");
      card.className = `tree-card ${node.status}`;
      card.dataset.nodeId = node.id;

      card.innerHTML = `
        <div class="card-node-info">
          <span class="node-label">${escapeHtml(node.label)}</span>
          <span class="node-detail">${escapeHtml(node.detail || "")}</span>
        </div>
        <span class="node-status-pill ${node.status}">${node.status}</span>
      `;

      card.addEventListener("click", () => {
        if (drawerTitle) drawerTitle.textContent = node.label;
        if (drawerStatus) drawerStatus.textContent = node.status.toUpperCase();
        if (drawerPayload) drawerPayload.textContent = JSON.stringify(node, null, 2);
        if (flowDrawer) flowDrawer.classList.add("open");
      });

      workflowTreeNodes.appendChild(card);
    });
  }

  function updateNodeState(toolName, status, output = null) {
    document.querySelectorAll(".tree-card").forEach((card) => {
      if (card.innerText.toLowerCase().includes(toolName.toLowerCase())) {
        card.className = `tree-card ${status}`;
        const pill = card.querySelector(".node-status-pill");
        if (pill) {
          pill.className = `node-status-pill ${status}`;
          pill.textContent = status;
        }
      }
    });
  }

  if (btnCloseDrawer && flowDrawer) {
    btnCloseDrawer.addEventListener("click", () => flowDrawer.classList.remove("open"));
  }

  if (btnResetWorkflow && workflowTreeNodes) {
    btnResetWorkflow.addEventListener("click", () => {
      workflowTreeNodes.innerHTML = "<p style='color:#64748b;'>Awaiting task execution plan...</p>";
    });
  }

  // ---------------------------------------------------------------------------
  // 7. Tasks Engine View
  // ---------------------------------------------------------------------------
  async function loadTasks() {
    if (!tasksGrid) return;
    try {
      const res = await fetch("/api/tasks");
      if (res.ok) {
        const data = await res.json();
        renderTasks(data.tasks || []);
      }
    } catch (e) {
      console.warn("Failed to load tasks:", e);
    }
  }

  function renderTasks(tasks) {
    if (!tasksGrid) return;
    tasksGrid.innerHTML = "";
    if (badgeTasksCount) badgeTasksCount.textContent = tasks.length;

    if (tasks.length === 0) {
      tasksGrid.innerHTML = `<div class="card-box" style="grid-column: 1/-1;"><p class="card-desc">No tasks executed yet. Ask Victor to perform an autonomous multi-step workflow!</p></div>`;
      return;
    }

    tasks.forEach((t) => {
      const card = document.createElement("div");
      card.className = "task-card";

      const stepsHtml = (t.steps || []).map((s) => `
        <div class="task-step-item ${s.status}">
          <span class="step-indicator"></span>
          <span>${escapeHtml(s.name)}</span>
        </div>
      `).join("");

      card.innerHTML = `
        <div class="task-card-header">
          <span class="task-goal">${escapeHtml(t.goal)}</span>
          <span class="task-status-tag ${t.status}">${t.status}</span>
        </div>
        <div class="task-steps-list">
          ${stepsHtml || '<span style="color:#64748b;font-size:11px;">Single-step execution</span>'}
        </div>
        <div class="task-meta-footer">
          Duration: ${t.duration || 0}s &bull; ID: ${t.id}
        </div>
      `;
      tasksGrid.appendChild(card);
    });
  }

  // ---------------------------------------------------------------------------
  // 8. Memory View
  // ---------------------------------------------------------------------------
  async function loadMemory() {
    try {
      const res = await fetch("/api/memory");
      if (res.ok) {
        const data = await res.json();
        renderMemoryFacts(data.facts || []);
        renderMemoryPreferences(data.preferences || {});
      }
    } catch (e) {
      console.warn("Memory load fail:", e);
    }
  }

  function renderMemoryFacts(facts) {
    if (!factsList) return;
    factsList.innerHTML = "";
    if (facts.length === 0) {
      factsList.innerHTML = `<p class="card-desc">No facts remembered yet.</p>`;
      return;
    }

    facts.forEach((f) => {
      const item = document.createElement("div");
      item.className = "memory-item-pill";
      item.innerHTML = `
        <span>${escapeHtml(f.fact)}</span>
        <button class="btn-delete-mem" data-id="${f.id}">Forget</button>
      `;
      item.querySelector(".btn-delete-mem").addEventListener("click", async () => {
        await fetch(`/api/memory/fact/${f.id}`, { method: "DELETE" });
        loadMemory();
      });
      factsList.appendChild(item);
    });
  }

  function renderMemoryPreferences(prefs) {
    if (!preferencesList) return;
    preferencesList.innerHTML = "";
    const keys = Object.keys(prefs);
    if (keys.length === 0) {
      preferencesList.innerHTML = `<p class="card-desc">No preferences configured.</p>`;
      return;
    }

    keys.forEach((k) => {
      const item = document.createElement("div");
      item.className = "memory-item-pill";
      item.innerHTML = `
        <span><strong>${escapeHtml(k)}:</strong> ${escapeHtml(prefs[k])}</span>
        <button class="btn-delete-mem" data-key="${k}">Reset</button>
      `;
      item.querySelector(".btn-delete-mem").addEventListener("click", async () => {
        await fetch(`/api/memory/preference/${k}`, { method: "DELETE" });
        loadMemory();
      });
      preferencesList.appendChild(item);
    });
  }

  if (btnAddFact && newFactInput) {
    btnAddFact.addEventListener("click", async () => {
      const val = newFactInput.value.trim();
      if (!val) return;
      await fetch("/api/memory/fact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fact: val }),
      });
      newFactInput.value = "";
      loadMemory();
    });
  }

  // ---------------------------------------------------------------------------
  // 9. Tools View
  // ---------------------------------------------------------------------------
  async function loadTools() {
    if (!toolsGrid) return;
    try {
      const res = await fetch("/api/tools");
      if (res.ok) {
        const data = await res.json();
        renderTools(data.tools || []);
      }
    } catch (e) {
      console.warn("Tools load fail:", e);
    }
  }

  function renderTools(tools) {
    if (!toolsGrid) return;
    toolsGrid.innerHTML = "";
    tools.forEach((t) => {
      const card = document.createElement("div");
      card.className = "tool-card";
      card.innerHTML = `
        <div class="tool-header">
          <span class="tool-name">${escapeHtml(t.name.toUpperCase())}</span>
          <span class="tool-perm ${t.permission}">${t.permission}</span>
        </div>
        <div class="tool-desc">${escapeHtml(t.description)}</div>
      `;
      toolsGrid.appendChild(card);
    });
  }

  // ---------------------------------------------------------------------------
  // 10. Models View
  // ---------------------------------------------------------------------------
  async function loadModels() {
    try {
      const res = await fetch("/api/models");
      if (res.ok) {
        const data = await res.json();
        if (modelActiveVal) modelActiveVal.textContent = data.current;
        if (modelProviderVal) modelProviderVal.textContent = data.provider.toUpperCase();
        renderModelsList(data.available || [], data.current);
      }
    } catch (e) {
      console.warn("Models load fail:", e);
    }
  }

  function renderModelsList(models, current) {
    if (!modelsList) return;
    modelsList.innerHTML = "";
    models.forEach((m) => {
      const item = document.createElement("div");
      item.className = "model-opt-item";
      const isCurrent = m === current;
      item.innerHTML = `
        <span><strong>${escapeHtml(m)}</strong></span>
        <button class="btn-secondary-sm" ${isCurrent ? "disabled" : ""}>
          ${isCurrent ? "Active" : "Switch"}
        </button>
      `;
      if (!isCurrent) {
        item.querySelector("button").addEventListener("click", async () => {
          await fetch("/api/models/switch", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ model_name: m }),
          });
          loadModels();
        });
      }
      modelsList.appendChild(item);
    });
  }

  // ---------------------------------------------------------------------------
  // 11. Permission Prompt Modal
  // ---------------------------------------------------------------------------
  function promptPermissionModal(req) {
    activePermRequestId = req.id;
    if (permTitle) permTitle.textContent = `Victor wants to execute: ${req.action}`;
    if (permDesc) permDesc.textContent = `Action targets: ${req.target}`;
    if (permDetails) permDetails.textContent = JSON.stringify(req.details, null, 2);
    if (permissionModal) permissionModal.classList.add("show");
    setMascotState("waiting", "Needs your permission to continue.");
  }

  async function resolvePermission(decision) {
    if (!activePermRequestId) return;
    await fetch("/api/permissions/respond", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ request_id: activePermRequestId, decision }),
    });
    if (permissionModal) permissionModal.classList.remove("show");
    activePermRequestId = null;
    setMascotState("working");
  }

  if (btnPermAllowOnce) btnPermAllowOnce.addEventListener("click", () => resolvePermission("allow_once"));
  if (btnPermAlwaysAllow) btnPermAlwaysAllow.addEventListener("click", () => resolvePermission("always_allow"));
  if (btnPermDeny) btnPermDeny.addEventListener("click", () => resolvePermission("deny"));

  // ---------------------------------------------------------------------------
  // 12. Desktop Mascot Launcher
  // ---------------------------------------------------------------------------
  async function launchDesktopMascot() {
    try {
      const res = await fetch("/api/mascot/launch", { method: "POST" });
      const data = await res.json();
      if (data.status === "launched") {
        alert("Desktop mascot launched! Look at your desktop.");
      } else {
        alert(`Launch status: ${data.message}`);
      }
    } catch (e) {
      alert(`Could not launch desktop mascot: ${e}`);
    }
  }

  if (btnLaunchDesktopMascot) btnLaunchDesktopMascot.addEventListener("click", launchDesktopMascot);
  if (btnSettingsLaunchMascot) btnSettingsLaunchMascot.addEventListener("click", launchDesktopMascot);

  // ---------------------------------------------------------------------------
  // Initial Status & Link
  // ---------------------------------------------------------------------------
  async function loadInitialStatus() {
    try {
      const res = await fetch("/api/status");
      if (res.ok) {
        const data = await res.json();
        if (activeModelPill) activeModelPill.textContent = (data.model || "QWEN 1.5B").toUpperCase();
        if (badgeTasksCount) badgeTasksCount.textContent = data.tasks_count || 0;
      }
    } catch (e) {
      console.warn("Status offline:", e);
    }
  }

  loadInitialStatus();
  initWebSocket();
});
