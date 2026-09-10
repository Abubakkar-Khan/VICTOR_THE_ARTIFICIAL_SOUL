/**
 * VICTOR // soulOS - Frontend Orchestration Engine
 * Gamified Gen-Z Retro-Modern UI with Web Audio Synth FX,
 * XP & Level Progression, Achievements, Borderless Chat, and Live Workflow Sync.
 */

document.addEventListener("DOMContentLoaded", () => {
  // ---------------------------------------------------------------------------
  // 1. DOM Elements
  // ---------------------------------------------------------------------------
  const chatStream = document.getElementById("chat-stream");
  const chatInput = document.getElementById("chat-input");
  const btnSend = document.getElementById("btn-send");
  const clearChatBtn = document.getElementById("clear-chat-btn");
  const exportChatBtn = document.getElementById("export-chat-btn");
  const sparkPromptBtn = document.getElementById("spark-prompt-btn");
  const statusPill = document.getElementById("status-pill");
  const sfxToggleBtn = document.getElementById("sfx-toggle-btn");
  const sfxLabel = document.getElementById("sfx-label");

  // Gamified Player Elements
  const playerLevel = document.getElementById("player-level");
  const levelTitle = document.getElementById("level-title");
  const xpText = document.getElementById("xp-text");
  const xpBarFill = document.getElementById("xp-bar-fill");
  const streakCountEl = document.getElementById("streak-count");
  const achievementToast = document.getElementById("achievement-toast");
  const achieveTitle = document.getElementById("achieve-title");

  // Workflow Graph Elements
  const workflowBeacon = document.getElementById("workflow-beacon");
  const wfLatency = document.getElementById("wf-latency");
  const resetGraphBtn = document.getElementById("reset-graph-btn");
  const telemetryDrawer = document.getElementById("telemetry-drawer");
  const closeDrawerBtn = document.getElementById("close-drawer-btn");
  const drawerNodeName = document.getElementById("drawer-node-name");
  const drawerNodeStatus = document.getElementById("drawer-node-status");
  const drawerNodeDuration = document.getElementById("drawer-node-duration");
  const drawerNodePayload = document.getElementById("drawer-node-payload");
  const capabilitiesGrid = document.getElementById("capabilities-grid");

  // SVG signal wires
  const wires = {
    "1-2": document.getElementById("wire-1-2"),
    "2-3": document.getElementById("wire-2-3"),
    "3-4": document.getElementById("wire-3-4"),
    "4-5": document.getElementById("wire-4-5"),
  };

  // ---------------------------------------------------------------------------
  // 2. Web Audio API Procedural Synth Sound FX Engine
  // ---------------------------------------------------------------------------
  let audioCtx = null;
  let sfxEnabled = localStorage.getItem("victor_sfx_enabled") !== "false";

  function initAudioContext() {
    if (!audioCtx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        audioCtx = new AudioContextClass();
      }
    }
    if (audioCtx && audioCtx.state === "suspended") {
      audioCtx.resume();
    }
  }

  // Update SFX Button UI
  function updateSfxButtonUI() {
    if (sfxLabel) {
      sfxLabel.textContent = sfxEnabled ? "SFX: ON" : "SFX: OFF";
    }
    if (sfxToggleBtn) {
      if (sfxEnabled) {
        sfxToggleBtn.classList.add("active");
      } else {
        sfxToggleBtn.classList.remove("active");
      }
    }
  }
  updateSfxButtonUI();

  if (sfxToggleBtn) {
    sfxToggleBtn.addEventListener("click", () => {
      sfxEnabled = !sfxEnabled;
      localStorage.setItem("victor_sfx_enabled", sfxEnabled ? "true" : "false");
      updateSfxButtonUI();
      if (sfxEnabled) {
        playSfx("transmit");
      }
    });
  }

  function playSfx(type) {
    if (!sfxEnabled) return;
    try {
      initAudioContext();
      if (!audioCtx) return;
      const now = audioCtx.currentTime;

      if (type === "transmit") {
        // High-pitch sci-fi blip / transmit chirp (880Hz -> 1320Hz)
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(880, now);
        osc.frequency.exponentialRampToValueAtTime(1320, now + 0.07);
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(now);
        osc.stop(now + 0.09);

      } else if (type === "tool_start") {
        // Subtle cyber sweep down (650Hz -> 320Hz)
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = "triangle";
        osc.frequency.setValueAtTime(650, now);
        osc.frequency.exponentialRampToValueAtTime(320, now + 0.12);
        gain.gain.setValueAtTime(0.09, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.13);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(now);
        osc.stop(now + 0.14);

      } else if (type === "tool_done") {
        // Double cyber confirmation blip
        [0, 0.07].forEach((delay, idx) => {
          const osc = audioCtx.createOscillator();
          const gain = audioCtx.createGain();
          osc.type = "sine";
          osc.frequency.setValueAtTime(idx === 0 ? 600 : 920, now + delay);
          gain.gain.setValueAtTime(0.08, now + delay);
          gain.gain.exponentialRampToValueAtTime(0.001, now + delay + 0.06);
          osc.connect(gain);
          gain.connect(audioCtx.destination);
          osc.start(now + delay);
          osc.stop(now + delay + 0.07);
        });

      } else if (type === "achieve" || type === "level_up") {
        // Sparkling 4-tone ascending fanfare (C5, E5, G5, C6)
        const freqs = [523.25, 659.25, 783.99, 1046.50];
        freqs.forEach((freq, idx) => {
          const osc = audioCtx.createOscillator();
          const gain = audioCtx.createGain();
          osc.type = "sine";
          osc.frequency.setValueAtTime(freq, now + idx * 0.08);
          gain.gain.setValueAtTime(0.12, now + idx * 0.08);
          gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.08 + 0.18);
          osc.connect(gain);
          gain.connect(audioCtx.destination);
          osc.start(now + idx * 0.08);
          osc.stop(now + idx * 0.08 + 0.2);
        });
      }
    } catch (err) {
      console.warn("Audio synthesis error:", err);
    }
  }

  // ---------------------------------------------------------------------------
  // 3. Gamification: XP, Levels, Streaks & Achievements
  // ---------------------------------------------------------------------------
  const LEVEL_TIERS = [
    { level: 1, title: "SYNAPSE SEED", minXp: 0, maxXp: 150 },
    { level: 2, title: "NEURAL LINK", minXp: 150, maxXp: 350 },
    { level: 3, title: "OPERATOR", minXp: 350, maxXp: 650 },
    { level: 4, title: "CYBER ADEPT", minXp: 650, maxXp: 1050 },
    { level: 5, title: "SYSTEM ARCHITECT", minXp: 1050, maxXp: 1600 },
    { level: 6, title: "SOUL SYNCED", minXp: 1600, maxXp: 2400 },
    { level: 7, title: "TRANSCENDENT", minXp: 2400, maxXp: 999999 },
  ];

  let currentXp = parseInt(localStorage.getItem("victor_user_xp") || "0", 10);
  let streakCount = parseInt(localStorage.getItem("victor_streak_count") || "1", 10);
  let unlockedAchievements = JSON.parse(localStorage.getItem("victor_unlocked_achievements") || "[]");

  function getTierForXp(xp) {
    for (let i = LEVEL_TIERS.length - 1; i >= 0; i--) {
      if (xp >= LEVEL_TIERS[i].minXp) {
        return LEVEL_TIERS[i];
      }
    }
    return LEVEL_TIERS[0];
  }

  function updatePlayerUI() {
    const tier = getTierForXp(currentXp);
    if (playerLevel) playerLevel.textContent = String(tier.level).padStart(2, "0");
    if (levelTitle) levelTitle.textContent = tier.title;

    const tierRange = tier.maxXp - tier.minXp;
    const progressInTier = currentXp - tier.minXp;
    if (xpText) xpText.textContent = `${progressInTier} / ${tierRange} XP`;

    const pct = Math.min(100, Math.max(0, (progressInTier / tierRange) * 100));
    if (xpBarFill) xpBarFill.style.width = `${pct}%`;

    if (streakCountEl) streakCountEl.textContent = String(streakCount);
  }

  function addXp(amount) {
    const oldTier = getTierForXp(currentXp);
    currentXp += amount;
    localStorage.setItem("victor_user_xp", currentXp);

    // Floating XP Gain Micro-animation
    const xpContainer = document.querySelector(".xp-container");
    if (xpContainer) {
      const badge = document.createElement("div");
      badge.className = "xp-gain-badge";
      badge.textContent = `+${amount} XP`;
      xpContainer.appendChild(badge);
      setTimeout(() => badge.remove(), 1200);
    }

    updatePlayerUI();

    // Check for Level Up
    const newTier = getTierForXp(currentXp);
    if (newTier.level > oldTier.level) {
      playSfx("level_up");
      triggerAchievement(`CONSCIOUSNESS ELEVATED: LVL ${newTier.level}`);
    }
  }

  let toastTimer = null;
  function triggerAchievement(title) {
    if (!achievementToast || !achieveTitle) return;
    achieveTitle.textContent = title;
    achievementToast.classList.add("show");
    playSfx("achieve");

    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      achievementToast.classList.remove("show");
    }, 3800);
  }

  function checkAchievement(id, title) {
    if (unlockedAchievements.includes(id)) return;
    unlockedAchievements.push(id);
    localStorage.setItem("victor_unlocked_achievements", JSON.stringify(unlockedAchievements));
    triggerAchievement(title);
  }

  function incrementStreak() {
    streakCount += 1;
    localStorage.setItem("victor_streak_count", streakCount);
    if (streakCountEl) streakCountEl.textContent = String(streakCount);
    if (streakCount === 5) {
      checkAchievement("streak_5", "FLOW STATE: 5X STREAK");
    }
  }

  updatePlayerUI();

  // ---------------------------------------------------------------------------
  // 4. Creative Sparks & Prompts Generator
  // ---------------------------------------------------------------------------
  const SPARK_PROMPTS = [
    "/calc 144 * 12 + (2 ** 8)",
    "/search latest advancements in local AI agent memory",
    "/file config/victor.yaml",
    "Explain quantum superposition using a cybernetic metaphor.",
    "What are the core design principles of Nothing OS and neo-brutalism?",
    "/calc (365 * 24 * 60) / 7",
    "/search lightweight small language models 2026",
    "Simulate a brief dialog between a kernel thread and an AI daemon.",
    "How does Victor use recursive tool loops to synthesize human answers?",
    "/calc 3.14159265 * (42 ** 2)",
    "Write a short retro-futuristic haiku about an awakening artificial soul.",
    "/tools"
  ];

  if (sparkPromptBtn) {
    sparkPromptBtn.addEventListener("click", () => {
      initAudioContext();
      playSfx("transmit");
      const randomPrompt = SPARK_PROMPTS[Math.floor(Math.random() * SPARK_PROMPTS.length)];
      if (chatInput) {
        chatInput.value = randomPrompt;
        chatInput.focus();
      }
      addXp(15);
      checkAchievement("spark_plug", "CREATIVE SPARK INJECTED");
    });
  }

  // ---------------------------------------------------------------------------
  // 5. Telemetry Store & Live Interactive Workflow Graph
  // ---------------------------------------------------------------------------
  const telemetryStore = {
    input: { name: "01 // INGESTION", status: "STANDBY", duration: "-", data: "Standing by for user directive." },
    magi: { name: "02 // COGNITIVE CORE", status: "STANDBY", duration: "-", data: "Decision Matrix idle." },
    tool: { name: "03 // TOOL HARNESS", status: "STANDBY", duration: "-", data: "No tool currently engaged." },
    obs: { name: "04 // OBSERVATION BUFFER", status: "STANDBY", duration: "-", data: "Buffer empty." },
    synth: { name: "05 // RECURSIVE SYNTHESIS", status: "STANDBY", duration: "-", data: "Awaiting observation input." },
  };

  function resetWorkflowNodes() {
    const nodeKeys = ["input", "magi", "tool", "obs", "synth"];
    nodeKeys.forEach((key) => {
      setCardState(key, "STANDBY", "standby");
    });
    Object.values(wires).forEach((wire) => {
      if (wire) wire.classList.remove("active");
    });
    if (workflowBeacon) workflowBeacon.classList.remove("pulsing");
  }

  function setCardState(nodeKey, statusText, statusClass, previewText = null, rawData = null) {
    const card = document.getElementById(`wf-node-${nodeKey}`);
    const statusEl = document.getElementById(`wf-status-${nodeKey}`);
    const descEl = document.getElementById(`wf-desc-${nodeKey}`);

    if (card && statusEl) {
      card.className = `pipeline-card ${statusClass === "running" ? "active" : statusClass === "locked" ? "locked" : ""}`;
      statusEl.className = `p-card-status ${statusClass}`;
      statusEl.textContent = statusText;

      if (previewText && descEl) {
        descEl.textContent = previewText;
      }

      telemetryStore[nodeKey].status = statusText;
      if (previewText) telemetryStore[nodeKey].data = previewText;
      if (rawData) telemetryStore[nodeKey].data = rawData;
    }
  }

  // Node Inspector Drawer
  document.querySelectorAll(".pipeline-card").forEach((card) => {
    card.addEventListener("click", () => {
      const nodeKey = card.dataset.node;
      const info = telemetryStore[nodeKey];
      if (info && telemetryDrawer) {
        drawerNodeName.textContent = info.name;
        drawerNodeStatus.textContent = info.status;
        drawerNodeDuration.textContent = info.duration || "-";

        let displayData = info.data;
        if (typeof displayData === "object") {
          displayData = JSON.stringify(displayData, null, 2);
        }
        drawerNodePayload.textContent = displayData;
        telemetryDrawer.classList.add("open");
        playSfx("transmit");
      }
    });
  });

  if (closeDrawerBtn && telemetryDrawer) {
    closeDrawerBtn.addEventListener("click", () => {
      telemetryDrawer.classList.remove("open");
    });
  }

  if (resetGraphBtn) {
    resetGraphBtn.addEventListener("click", () => {
      resetWorkflowNodes();
      playSfx("transmit");
    });
  }

  // ---------------------------------------------------------------------------
  // 6. Tab Navigation Switcher
  // ---------------------------------------------------------------------------
  document.querySelectorAll(".switch-tab").forEach((tabBtn) => {
    tabBtn.addEventListener("click", () => {
      initAudioContext();
      document.querySelectorAll(".switch-tab").forEach((btn) => btn.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.remove("active"));

      tabBtn.classList.add("active");
      const targetPanelId = `panel-${tabBtn.dataset.tab}`;
      const targetPanel = document.getElementById(targetPanelId);
      if (targetPanel) {
        targetPanel.classList.add("active");
      }
    });
  });

  // ---------------------------------------------------------------------------
  // 7. Borderless Chat Rendering & Formatting (Strictly No Borders)
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

  function formatMarkdownText(str) {
    if (!str) return "";
    let clean = escapeHtml(str);
    // Multi-line code blocks
    clean = clean.replace(/```([a-zA-Z0-9]*)\n([\s\S]*?)```/g, (m, lang, code) => {
      return `<pre><code>${code.trim()}</code></pre>`;
    });
    // Inline code
    clean = clean.replace(/`([^`]+)`/g, "<code>$1</code>");
    // Bold text
    clean = clean.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    // Links
    clean = clean.replace(/\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    return clean;
  }

  function appendUserMessage(text) {
    const row = document.createElement("div");
    row.className = "convo-row user-row";
    const time = new Date().toTimeString().split(" ")[0];

    row.innerHTML = `
      <div class="convo-avatar">U</div>
      <div class="convo-content">
        <div class="convo-header">
          <span class="convo-sender">User</span>
          <span class="convo-time">${time}</span>
        </div>
        <div class="convo-text">${escapeHtml(stripEmojis(text))}</div>
      </div>
    `;

    chatStream.appendChild(row);
    chatStream.scrollTop = chatStream.scrollHeight;
  }

  function appendVictorMessage(text) {
    const row = document.createElement("div");
    row.className = "convo-row victor-row";
    const time = new Date().toTimeString().split(" ")[0];
    const cleanRaw = stripEmojis(text);

    row.innerHTML = `
      <div class="convo-avatar">V</div>
      <div class="convo-content">
        <div class="convo-header">
          <span class="convo-sender">Victor</span>
          <span class="convo-time">${time}</span>
        </div>
        <div class="convo-text">${formatMarkdownText(cleanRaw)}</div>
        <div class="msg-actions">
          <button class="micro-btn btn-copy" title="Copy Victor's response">[COPY]</button>
        </div>
      </div>
    `;

    // Copy to clipboard handler
    const copyBtn = row.querySelector(".btn-copy");
    if (copyBtn) {
      copyBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(cleanRaw).then(() => {
          copyBtn.textContent = "[COPIED]";
          playSfx("transmit");
          setTimeout(() => {
            copyBtn.textContent = "[COPY]";
          }, 1500);
        });
      });
    }

    chatStream.appendChild(row);
    chatStream.scrollTop = chatStream.scrollHeight;
  }

  // ---------------------------------------------------------------------------
  // 8. WebSocket Telemetry & Chat Transport
  // ---------------------------------------------------------------------------
  let socket = null;
  let isTransmitting = false;

  function setTransmitting(transmitting) {
    isTransmitting = transmitting;
    if (btnSend) {
      btnSend.disabled = transmitting;
      const textSpan = btnSend.querySelector("span");
      if (textSpan) textSpan.textContent = transmitting ? "SYNCING..." : "SEND";
    }
  }

  function initWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log("[VICTOR // soulOS] WebSocket link established");
      if (statusPill) {
        statusPill.className = "status-capsule online";
        statusPill.querySelector(".status-name").textContent = "ONLINE";
      }
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        handleServerPayload(payload);
      } catch (err) {
        console.error("Payload parse error:", err);
      }
    };

    socket.onclose = () => {
      if (statusPill) {
        statusPill.className = "status-capsule";
        statusPill.querySelector(".status-name").textContent = "RECONNECTING";
      }
      setTimeout(initWebSocket, 2500);
    };
  }

  function handleServerPayload(payload) {
    if (payload.type === "event") {
      const evt = payload.event;
      const topic = evt.topic;
      const data = evt.data || {};

      if (topic === "agent.started") {
        if (workflowBeacon) workflowBeacon.classList.add("pulsing");
        if (wires["1-2"]) wires["1-2"].classList.add("active");
        setCardState("input", "INGESTING", "running", data.user_message || data.command);
        setCardState("magi", "PLANNING", "running", "Evaluating directives & intent...");

      } else if (topic === "agent.thinking") {
        const state = data.state || "synthesizing";
        if (state === "synthesizing") {
          if (wires["4-5"]) wires["4-5"].classList.add("active");
          setCardState("synth", "SYNTHESIS", "running", "Formulating natural response stream...");
        }

      } else if (topic === "tool.started") {
        const toolName = data.tool || "capability";
        if (wires["2-3"]) wires["2-3"].classList.add("active");
        setCardState("magi", "LOCKED", "locked", `Selected: ${toolName}`);
        setCardState("tool", "RUNNING", "running", `Executing ${toolName}`, data.parameters);
        playSfx("tool_start");

      } else if (topic === "tool.completed") {
        const toolName = data.tool || "capability";
        const dur = data.duration !== undefined ? `${data.duration}s` : "OK";
        setCardState("tool", `LOCKED [${dur}]`, "locked", `${toolName} executed successfully`, data.output);
        telemetryStore.tool.duration = dur;

        if (wires["3-4"]) wires["3-4"].classList.add("active");
        setCardState("obs", "BUFFERED", "locked", "Observation payload formatted", data.output);
        playSfx("tool_done");
        addXp(50);

        // Tool-specific achievements
        if (toolName === "calculator") {
          checkAchievement("calc_math", "CALC MATRIX: Deterministic Execution");
        } else if (toolName === "web_search") {
          checkAchievement("web_recon", "CYBER RECON: Web Intelligence Gathered");
        } else if (toolName === "file_read" || toolName === "file_list") {
          checkAchievement("filesystem", "DATA VAULT: File System Inspection");
        }

      } else if (topic === "tool.failed") {
        setCardState("tool", "FAILED", "standby", data.error, data.output);

      } else if (topic === "agent.completed") {
        const dur = data.duration !== undefined ? `${data.duration}s` : "0.0s";
        setCardState("synth", `LOCKED [${dur}]`, "locked", "Natural output stream ready");
        telemetryStore.synth.duration = dur;
        if (wfLatency) wfLatency.textContent = dur;
        if (workflowBeacon) workflowBeacon.classList.remove("pulsing");

        setTimeout(() => {
          Object.values(wires).forEach((w) => w && w.classList.remove("active"));
        }, 1500);
      }

    } else if (payload.type === "chat_result") {
      appendVictorMessage(payload.data.content);
      playSfx("transmit");
      addXp(25);
      incrementStreak();
      checkAchievement("first_contact", "FIRST CONTACT: Neural Link Established");
      setTransmitting(false);
    }
  }

  async function sendDirective() {
    const text = chatInput.value.trim();
    if (!text || isTransmitting) return;

    initAudioContext();
    playSfx("transmit");
    appendUserMessage(text);
    chatInput.value = "";
    setTransmitting(true);

    // Reset workflow graph for the incoming directive trace
    resetWorkflowNodes();
    setCardState("input", "INGESTING", "running", text);

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
        playSfx("transmit");
        addXp(25);
        incrementStreak();
        checkAchievement("first_contact", "FIRST CONTACT: Neural Link Established");
        setCardState("synth", "LOCKED", "locked", "Natural output stream ready");
      } catch (err) {
        appendVictorMessage(`[COMMUNICATION ERROR]: ${err}`);
      } finally {
        setTransmitting(false);
      }
    }
  }

  // Send bindings
  if (btnSend) btnSend.addEventListener("click", sendDirective);

  if (chatInput) {
    chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        sendDirective();
      }
    });
  }

  // Quick Action Capsules
  document.querySelectorAll(".quick-chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      const cmd = btn.dataset.cmd;
      if (cmd && chatInput) {
        chatInput.value = cmd;
        sendDirective();
      }
    });
  });

  // Reset Conversation
  if (clearChatBtn) {
    clearChatBtn.addEventListener("click", () => {
      initAudioContext();
      playSfx("transmit");
      chatStream.innerHTML = "";
      appendVictorMessage("Memory feed reset. Victor is ready for new directives.");
      resetWorkflowNodes();
      fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: "/clear", reset: true }),
      });
    });
  }

  // Export Conversation to Markdown
  if (exportChatBtn) {
    exportChatBtn.addEventListener("click", () => {
      initAudioContext();
      playSfx("transmit");

      const rows = chatStream.querySelectorAll(".convo-row");
      const dateStr = new Date().toISOString();
      const currentTier = getTierForXp(currentXp);

      let markdown = `# VICTOR // soulOS CONVERSATION EXPORT\n`;
      markdown += `Generated: ${dateStr}\n`;
      markdown += `Operator Level: LVL ${currentTier.level} [${currentTier.title}] (${currentXp} XP)\n`;
      markdown += `Streak: ${streakCount} cycles\n\n---\n\n`;

      rows.forEach((row) => {
        const isUser = row.classList.contains("user-row");
        const sender = isUser ? "User" : "Victor";
        const time = row.querySelector(".convo-time")?.textContent || "";
        const text = row.querySelector(".convo-text")?.innerText || "";
        markdown += `### ${sender} (${time})\n\n${text}\n\n`;
      });

      const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `victor-chat-${Date.now()}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      checkAchievement("data_exporter", "DATA PACKET ARCHIVED");
    });
  }

  // ---------------------------------------------------------------------------
  // 9. Load Capabilities & System Status
  // ---------------------------------------------------------------------------
  async function loadStatus() {
    try {
      const res = await fetch("/api/status");
      if (res.ok) {
        const data = await res.json();
        if (statusPill) {
          if (data.status === "online") {
            statusPill.className = "status-capsule online";
            statusPill.querySelector(".status-name").textContent = "ONLINE";
          } else {
            statusPill.className = "status-capsule";
            statusPill.querySelector(".status-name").textContent = "OFFLINE";
          }
        }
      }
    } catch (e) {
      console.warn("Status check error:", e);
    }
  }

  async function loadTools() {
    try {
      const res = await fetch("/api/tools");
      if (res.ok) {
        const data = await res.json();
        renderCapabilities(data.tools || []);
      }
    } catch (e) {
      console.warn("Tools load error:", e);
    }
  }

  function renderCapabilities(tools) {
    if (!capabilitiesGrid) return;
    capabilitiesGrid.innerHTML = "";
    tools.forEach((tool) => {
      const card = document.createElement("div");
      card.className = "cap-card";
      const shortcut = tool.slash_command
        ? `<div class="cap-shortcut">DIRECTIVE: ${tool.slash_command}</div>`
        : "";
      card.innerHTML = `
        <div class="cap-head">
          <span class="cap-name">${tool.name.toUpperCase()}</span>
          <span class="cap-badge ${tool.permission}">[${tool.permission}]</span>
        </div>
        <div class="cap-desc">${escapeHtml(tool.description)}</div>
        ${shortcut}
      `;
      capabilitiesGrid.appendChild(card);
    });
  }

  // ---------------------------------------------------------------------------
  // 10. Initialization
  // ---------------------------------------------------------------------------
  loadStatus();
  loadTools();
  initWebSocket();
});
