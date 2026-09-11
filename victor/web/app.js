/* ================================================================
   Victor — The Artificial Soul
   Workshop Client
   
   Handles WebSocket events, REST API calls, and view rendering.
   Typography-first. Quiet. No emojis.
   ================================================================ */

(function () {
  'use strict';

  // ── State ──────────────────────────────────────────────────────

  let ws = null;
  let wsRetryDelay = 1000;
  let currentView = 'chat';
  let ttsEnabled = false;
  let speechSynth = window.speechSynthesis || null;
  let selectedVoice = null;
  let recognition = null;
  let isListening = false;


  // ── DOM References ─────────────────────────────────────────────

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  const statusDot = $('#status-dot');
  const statusText = $('#status-text');
  const modelName = $('#model-name');
  const viewTitle = $('#view-title');
  const chatFeed = $('#chat-feed');
  const chatEmpty = $('#chat-empty');
  const chatInput = $('#chat-input');
  const btnSend = $('#btn-send');
  const btnMic = $('#btn-mic');
  const btnClear = $('#btn-clear');
  const tasksContainer = $('#tasks-container');
  const tasksEmpty = $('#tasks-empty');
  const factsList = $('#facts-list');
  const prefsList = $('#prefs-list');
  const factInput = $('#fact-input');
  const btnAddFact = $('#btn-add-fact');
  const toolsList = $('#tools-list');
  const modelSelect = $('#model-select');
  const ttsToggle = $('#tts-toggle');
  const voiceSelect = $('#voice-select');
  const btnLaunchMascot = $('#btn-launch-mascot');
  const shellStatus = $('#shell-status');
  const permModal = $('#permission-modal');
  const permDesc = $('#perm-desc');
  const permDetails = $('#perm-details');
  const btnPermAllow = $('#btn-perm-allow');
  const btnPermAlways = $('#btn-perm-always');
  const btnPermDeny = $('#btn-perm-deny');


  // ── Navigation ─────────────────────────────────────────────────

  const viewNames = {
    chat: 'Chat',
    tasks: 'Tasks',
    memory: 'Memory',
    tools: 'Tools',
    settings: 'Settings'
  };

  function switchView(view) {
    currentView = view;
    $$('.nav-item').forEach(btn => btn.classList.toggle('active', btn.dataset.view === view));
    $$('.view-panel').forEach(panel => panel.classList.toggle('active', panel.id === `view-${view}`));
    viewTitle.textContent = viewNames[view] || view;

    // Lazy-load data for views
    if (view === 'tasks') loadTasks();
    if (view === 'memory') loadMemory();
    if (view === 'tools') loadTools();
    if (view === 'settings') loadSettings();

    // Show/hide header clear button (only on chat)
    btnClear.style.display = view === 'chat' ? '' : 'none';
  }

  $$('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => switchView(btn.dataset.view));
  });


  // ── Agent State ────────────────────────────────────────────────

  function setAgentState(state) {
    statusDot.className = 'status-dot';
    if (state === 'thinking' || state === 'working') {
      statusDot.classList.add(state);
    } else if (state === 'error') {
      statusDot.classList.add('error');
    }
    statusText.textContent = state === 'idle' ? 'idle' : state + '...';
    if (state === 'idle' || state === 'done') {
      statusText.textContent = 'idle';
    }
  }


  // ── Text Utilities ─────────────────────────────────────────────

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function stripEmojis(str) {
    return str.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{FE00}-\u{FE0F}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{200D}\u{20E3}\u{E0020}-\u{E007F}]/gu, '').trim();
  }

  function formatMarkdown(text) {
    // Simple markdown: bold, italic, code blocks, inline code, links, line breaks
    let html = escapeHtml(text);

    // Code blocks
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
      return `<pre><code>${code.trim()}</code></pre>`;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bold
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // Italic
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

    // Bare URLs
    html = html.replace(/(^|[\s>])(https?:\/\/[^\s<]+)/gm, '$1<a href="$2" target="_blank" rel="noopener">$2</a>');

    // Line breaks to paragraphs
    const paras = html.split(/\n\n+/).filter(p => p.trim());
    if (paras.length > 1) {
      html = paras.map(p => {
        if (p.startsWith('<pre>')) return p;
        return `<p>${p.replace(/\n/g, '<br>')}</p>`;
      }).join('');
    } else {
      html = html.replace(/\n/g, '<br>');
    }

    return html;
  }


  // ── Chat Rendering ─────────────────────────────────────────────

  function hideEmptyState() {
    if (chatEmpty) chatEmpty.style.display = 'none';
  }

  function appendMessage(sender, text) {
    hideEmptyState();
    const msg = document.createElement('div');
    msg.className = 'message';

    const label = document.createElement('div');
    label.className = 'message-sender';
    label.textContent = sender;

    const body = document.createElement('div');
    body.className = 'message-body';
    body.innerHTML = formatMarkdown(stripEmojis(text));

    msg.appendChild(label);
    msg.appendChild(body);
    chatFeed.appendChild(msg);
    scrollToBottom();
    return msg;
  }

  function appendToolAnnotation(toolName, status, duration) {
    hideEmptyState();
    const ann = document.createElement('div');
    ann.className = `tool-annotation ${status}`;
    let text = toolName.replace(/_/g, ' ');
    if (duration) text += ` \u00B7 ${duration}`;
    ann.textContent = text;
    ann.id = `tool-ann-${toolName}-${Date.now()}`;
    chatFeed.appendChild(ann);
    scrollToBottom();
    return ann;
  }

  function appendThinking() {
    hideEmptyState();
    // Remove previous thinking indicator
    const prev = chatFeed.querySelector('.thinking-indicator');
    if (prev) prev.remove();

    const el = document.createElement('div');
    el.className = 'thinking-indicator';
    el.textContent = 'thinking...';
    chatFeed.appendChild(el);
    scrollToBottom();
    return el;
  }

  function removeThinking() {
    const el = chatFeed.querySelector('.thinking-indicator');
    if (el) el.remove();
  }

  function scrollToBottom() {
    requestAnimationFrame(() => {
      chatFeed.scrollTop = chatFeed.scrollHeight;
    });
  }

  // Auto-resize textarea
  chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 160) + 'px';
  });


  // ── Send Message ───────────────────────────────────────────────

  function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    appendMessage('You', text);
    chatInput.value = '';
    chatInput.style.height = 'auto';

    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'chat', message: text }));
    }
  }

  btnSend.addEventListener('click', sendMessage);
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  btnClear.addEventListener('click', () => {
    chatFeed.innerHTML = '';
    if (chatEmpty) {
      chatFeed.appendChild(chatEmpty);
      chatEmpty.style.display = '';
    }
    fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: '/clear' })
    }).catch(() => {});
  });


  // ── WebSocket ──────────────────────────────────────────────────

  let currentToolAnnotation = null;

  function initWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${location.host}/ws/chat`);

    ws.onopen = () => {
      wsRetryDelay = 1000;
      setAgentState('idle');
    };

    ws.onclose = () => {
      setAgentState('idle');
      setTimeout(initWebSocket, wsRetryDelay);
      wsRetryDelay = Math.min(wsRetryDelay * 1.5, 15000);
    };

    ws.onerror = () => {
      ws.close();
    };

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        handleServerMessage(msg);
      } catch (e) {
        // Ignore malformed messages
      }
    };
  }

  function handleServerMessage(msg) {
    if (msg.type === 'event') {
      const topic = msg.topic || '';
      const data = msg.data || {};

      if (topic === 'agent.started') {
        setAgentState('thinking');
        appendThinking();
      }

      if (topic === 'agent.thinking') {
        setAgentState('thinking');
      }

      if (topic === 'agent.state') {
        setAgentState(data.state || 'idle');
      }

      if (topic === 'tool.started') {
        removeThinking();
        setAgentState('working');
        currentToolAnnotation = appendToolAnnotation(
          data.tool || 'tool',
          'active'
        );
      }

      if (topic === 'tool.completed') {
        if (currentToolAnnotation) {
          currentToolAnnotation.classList.remove('active');
          currentToolAnnotation.classList.add('done');
          const dur = data.duration ? `${data.duration.toFixed(1)}s` : '';
          if (dur) {
            currentToolAnnotation.textContent += ` \u00B7 ${dur}`;
          }
          currentToolAnnotation = null;
        }
      }

      if (topic === 'tool.failed') {
        if (currentToolAnnotation) {
          currentToolAnnotation.classList.remove('active');
          currentToolAnnotation.classList.add('failed');
          currentToolAnnotation = null;
        }
      }

      if (topic === 'agent.completed') {
        setAgentState('idle');
        removeThinking();
      }

      if (topic === 'permission.requested') {
        showPermissionModal(data);
      }

      // Mascot state events (map to agent state)
      if (topic === 'mascot.state_changed') {
        const stateMap = {
          idle: 'idle', listening: 'listening', thinking: 'thinking',
          working: 'working', completed: 'idle', error: 'error',
          perked: 'thinking', focused: 'working', thoughtful: 'thinking',
          happy: 'idle'
        };
        setAgentState(stateMap[data.state] || 'idle');
      }
    }

    if (msg.type === 'chat_result') {
      removeThinking();
      setAgentState('idle');
      const text = stripEmojis(msg.response || msg.data?.response || '');
      if (text) {
        appendMessage('Victor', text);
        if (ttsEnabled) speakText(text);
      }
    }
  }


  // ── Tasks ──────────────────────────────────────────────────────

  async function loadTasks() {
    try {
      const res = await fetch('/api/tasks');
      const data = await res.json();
      renderTasks(data.tasks || []);
    } catch (e) {
      tasksContainer.innerHTML = '<div class="tasks-empty">Could not load tasks.</div>';
    }
  }

  function renderTasks(tasks) {
    tasksContainer.innerHTML = '';
    if (!tasks.length) {
      tasksContainer.innerHTML = '<div class="tasks-empty">No tasks yet. Victor creates tasks when working on multi-step requests.</div>';
      return;
    }

    // Sort: active first, then by most recent
    tasks.sort((a, b) => {
      if (a.status === 'running' && b.status !== 'running') return -1;
      if (b.status === 'running' && a.status !== 'running') return 1;
      return 0;
    });

    tasks.forEach(task => {
      const item = document.createElement('div');
      item.className = 'task-item';

      const title = document.createElement('div');
      title.className = 'task-title';
      title.textContent = task.goal || task.title || 'Untitled task';

      const steps = document.createElement('ul');
      steps.className = 'task-steps';

      (task.steps || []).forEach(step => {
        const li = document.createElement('li');
        li.className = 'task-step';

        const icon = document.createElement('span');
        icon.className = 'step-icon';
        if (step.status === 'completed') {
          icon.classList.add('done');
          icon.innerHTML = '&#10003;';
        } else if (step.status === 'running') {
          icon.classList.add('active');
          icon.innerHTML = '&#9679;';
        } else {
          icon.classList.add('pending');
          icon.innerHTML = '&#9675;';
        }

        const label = document.createElement('span');
        label.textContent = step.name || step.tool || 'Step';

        li.appendChild(icon);
        li.appendChild(label);
        steps.appendChild(li);
      });

      item.appendChild(title);
      item.appendChild(steps);

      if (task.status === 'completed' && task.duration) {
        const dur = document.createElement('div');
        dur.className = 'task-duration';
        dur.textContent = `Finished in ${task.duration.toFixed(1)}s`;
        item.appendChild(dur);
      }

      if (task.outcome) {
        const result = document.createElement('div');
        result.className = 'task-result';
        result.textContent = task.outcome;
        item.appendChild(result);
      }

      tasksContainer.appendChild(item);
    });
  }


  // ── Memory ─────────────────────────────────────────────────────

  async function loadMemory() {
    try {
      const res = await fetch('/api/memory');
      const data = await res.json();
      renderFacts(data.facts || []);
      renderPrefs(data.preferences || {});
    } catch (e) {
      // Silent
    }
  }

  function renderFacts(facts) {
    factsList.innerHTML = '';
    facts.forEach(fact => {
      const li = document.createElement('li');
      li.className = 'memory-item';

      const bullet = document.createElement('span');
      bullet.className = 'memory-bullet';
      bullet.innerHTML = '&bull;';

      const text = document.createElement('span');
      text.className = 'memory-text';
      text.textContent = fact.content || fact.text || fact;

      const del = document.createElement('button');
      del.className = 'memory-delete';
      del.textContent = 'remove';
      del.addEventListener('click', async () => {
        const factId = fact.id || fact.fact_id;
        if (factId) {
          await fetch(`/api/memory/fact/${factId}`, { method: 'DELETE' });
          loadMemory();
        }
      });

      li.appendChild(bullet);
      li.appendChild(text);
      li.appendChild(del);
      factsList.appendChild(li);
    });
  }

  function renderPrefs(prefs) {
    prefsList.innerHTML = '';
    const entries = Array.isArray(prefs) ? prefs : Object.entries(prefs);
    entries.forEach(entry => {
      const li = document.createElement('li');
      li.className = 'memory-item';

      const bullet = document.createElement('span');
      bullet.className = 'memory-bullet';
      bullet.innerHTML = '&bull;';

      const text = document.createElement('span');
      text.className = 'memory-text';
      if (Array.isArray(entry)) {
        text.textContent = `${entry[0]}: ${entry[1]}`;
      } else {
        text.textContent = `${entry.key || ''}: ${entry.value || ''}`;
      }

      li.appendChild(bullet);
      li.appendChild(text);
      prefsList.appendChild(li);
    });
  }

  btnAddFact.addEventListener('click', async () => {
    const text = factInput.value.trim();
    if (!text) return;
    await fetch('/api/memory/fact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: text })
    });
    factInput.value = '';
    loadMemory();
  });

  factInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      btnAddFact.click();
    }
  });


  // ── Tools ──────────────────────────────────────────────────────

  async function loadTools() {
    try {
      const res = await fetch('/api/tools');
      const data = await res.json();
      const tools = data.tools || data;
      renderTools(Array.isArray(tools) ? tools : []);
    } catch (e) {
      toolsList.innerHTML = '<div class="tasks-empty">Could not load tools.</div>';
    }
  }

  function renderTools(tools) {
    toolsList.innerHTML = '';
    tools.forEach(tool => {
      const row = document.createElement('div');
      row.className = 'tool-row';

      const name = document.createElement('span');
      name.className = 'tool-name';
      name.textContent = tool.name;

      const desc = document.createElement('span');
      desc.className = 'tool-desc';
      desc.textContent = tool.description || '';

      const perm = document.createElement('span');
      perm.className = 'tool-perm';
      const permLevel = (tool.permission || 'safe').toLowerCase();
      perm.classList.add(permLevel);
      perm.textContent = permLevel;

      row.appendChild(name);
      row.appendChild(desc);
      row.appendChild(perm);
      toolsList.appendChild(row);
    });
  }


  // ── Settings ───────────────────────────────────────────────────

  async function loadSettings() {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      shellStatus.textContent = data.security?.allow_shell ? 'enabled' : 'disabled';
    } catch (e) {}

    // Load models
    try {
      const res = await fetch('/api/models');
      const data = await res.json();
      modelSelect.innerHTML = '';
      const models = data.available_models || [];
      const current = data.current_model || '';

      models.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m;
        opt.textContent = m;
        if (m === current) opt.selected = true;
        modelSelect.appendChild(opt);
      });

      if (!models.length) {
        const opt = document.createElement('option');
        opt.textContent = current || 'qwen2:1.5b';
        modelSelect.appendChild(opt);
      }
    } catch (e) {}

    // Populate voice list
    populateVoices();
  }

  modelSelect.addEventListener('change', async () => {
    try {
      await fetch('/api/models/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_name: modelSelect.value })
      });
      modelName.textContent = modelSelect.value;
    } catch (e) {}
  });

  // TTS toggle
  ttsToggle.addEventListener('click', () => {
    ttsEnabled = !ttsEnabled;
    ttsToggle.classList.toggle('on', ttsEnabled);
  });

  function populateVoices() {
    if (!speechSynth) return;
    const voices = speechSynth.getVoices();
    voiceSelect.innerHTML = '';
    voices.forEach((v, i) => {
      const opt = document.createElement('option');
      opt.value = i;
      opt.textContent = `${v.name} (${v.lang})`;
      voiceSelect.appendChild(opt);
    });
  }

  if (speechSynth && speechSynth.onvoiceschanged !== undefined) {
    speechSynth.onvoiceschanged = populateVoices;
  }

  voiceSelect.addEventListener('change', () => {
    const voices = speechSynth ? speechSynth.getVoices() : [];
    selectedVoice = voices[parseInt(voiceSelect.value)] || null;
  });

  function speakText(text) {
    if (!speechSynth || !ttsEnabled) return;
    speechSynth.cancel();
    const utt = new SpeechSynthesisUtterance(text);
    if (selectedVoice) utt.voice = selectedVoice;
    utt.rate = 1.0;
    utt.pitch = 1.0;
    speechSynth.speak(utt);
  }

  // Launch mascot
  btnLaunchMascot.addEventListener('click', async () => {
    try {
      await fetch('/api/mascot/launch', { method: 'POST' });
      btnLaunchMascot.textContent = 'Launched';
      setTimeout(() => { btnLaunchMascot.textContent = 'Launch'; }, 2000);
    } catch (e) {}
  });


  // ── Voice Input (STT) ─────────────────────────────────────────

  if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      chatInput.value = transcript;
      sendMessage();
    };

    recognition.onend = () => {
      isListening = false;
      btnMic.classList.remove('active');
      setAgentState('idle');
    };

    recognition.onerror = () => {
      isListening = false;
      btnMic.classList.remove('active');
    };
  }

  btnMic.addEventListener('click', () => {
    if (!recognition) return;
    if (isListening) {
      recognition.stop();
    } else {
      recognition.start();
      isListening = true;
      btnMic.classList.add('active');
      setAgentState('listening');
    }
  });


  // ── Permission Modal ───────────────────────────────────────────

  let pendingPermissionId = null;

  function showPermissionModal(data) {
    pendingPermissionId = data.request_id || data.id;
    permDesc.textContent = data.description || 'Victor wants to perform an action.';
    permDetails.textContent = data.details || data.action || 'system action';
    permModal.classList.add('visible');
  }

  async function resolvePermission(decision) {
    if (!pendingPermissionId) return;
    permModal.classList.remove('visible');
    try {
      await fetch('/api/permissions/respond', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_id: pendingPermissionId, decision })
      });
    } catch (e) {}
    pendingPermissionId = null;
  }

  btnPermAllow.addEventListener('click', () => resolvePermission('allow_once'));
  btnPermAlways.addEventListener('click', () => resolvePermission('always_allow'));
  btnPermDeny.addEventListener('click', () => resolvePermission('deny'));


  // ── Initialization ─────────────────────────────────────────────

  async function init() {
    // Load status
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      modelName.textContent = data.model || 'qwen2:1.5b';
    } catch (e) {}

    // Connect WebSocket
    initWebSocket();
  }

  init();

})();
