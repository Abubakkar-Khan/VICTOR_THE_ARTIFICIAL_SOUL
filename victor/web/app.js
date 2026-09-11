/* ================================================================
   Victor // The Artificial Soul
   Gamified Terminal Client, Dynamic Emotion Theming & Cognitive Audio
   Version 2.5.0
   ================================================================ */

(function () {
  'use strict';

  // ── 8 Artificial Soul Emotions ──────────────────────────────────

  const EMOTIONS = {
    neutral:   { label: 'NEUTRAL',   sprite: '/static/sprites/neutral.png',   desc: 'Standing by. Calm and level-headed.' },
    happy:     { label: 'HAPPY',     sprite: '/static/sprites/happy.png',     desc: 'Successful / helpful outcome.' },
    curious:   { label: 'CURIOUS',   sprite: '/static/sprites/curious.png',   desc: 'Exploring and learning.' },
    idle:      { label: 'IDLE',      sprite: '/static/sprites/idle.png',      desc: 'Relaxed — nothing happening.' },
    bored:     { label: 'BORED',     sprite: '/static/sprites/bored.png',     desc: 'Waiting patiently for something.' },
    thinking:  { label: 'THINKING',  sprite: '/static/sprites/thinking.png',  desc: 'Synthesizing reasoning vectors.' },
    searching: { label: 'SEARCHING', sprite: '/static/sprites/searching.png', desc: 'Looking through information and files.' },
    excited:   { label: 'EXCITED',   sprite: '/static/sprites/excited.png',   desc: 'Interesting discovery! High resonance.' },
    eureka:    { label: 'EUREKA',    sprite: '/static/sprites/eureka.png',    desc: 'Figured something out!' },
    confused:  { label: 'CONFUSED',  sprite: '/static/sprites/confused.png',  desc: 'Unclear request or problem.' },
    concerned: { label: 'CONCERNED', sprite: '/static/sprites/concerned.png', desc: 'Failure or problem detected.' },
    listening: { label: 'LISTENING', sprite: '/static/sprites/listening.png', desc: 'Receiving your voice or input.' },
    skeptical: { label: 'SKEPTICAL', sprite: '/static/sprites/skeptical.png', desc: 'Something doesn\'t seem right / checking.' }
  };


  // ── Celeste-Style Procedural Audio Synthesizer ─────────────────
  // Electronic pentatonic blips & warm chimes (no robotic TTS)

  class CelesteSynthesizer {
    constructor() {
      this.ctx = null;
      this.enabled = true;
      this.volume = 0.12;
      this.pentatonic = [392.00, 440.00, 523.25, 587.33, 659.25, 783.99, 880.00];
    }

    _init() {
      if (!this.ctx) {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (AudioContextClass) this.ctx = new AudioContextClass();
      }
      if (this.ctx && this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
    }

    playBlip(freqOverride) {
      if (!this.enabled) return;
      this._init();
      if (!this.ctx) return;

      try {
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        const freq = freqOverride || this.pentatonic[Math.floor(Math.random() * this.pentatonic.length)];
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, now);

        gain.gain.setValueAtTime(this.volume, now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.05);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.055);
      } catch (e) {}
    }

    playSpeechStream(tokenCount = 5) {
      if (!this.enabled) return;
      const count = Math.min(tokenCount, 8);
      for (let i = 0; i < count; i++) {
        setTimeout(() => {
          this.playBlip();
        }, i * 45);
      }
    }

    playThinkingArpeggio() {
      if (!this.enabled) return;
      this._init();
      if (!this.ctx) return;

      try {
        const notes = [523.25, 659.25, 783.99]; // C5, E5, G5
        notes.forEach((freq, idx) => {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          const start = this.ctx.currentTime + (idx * 0.07);

          osc.type = 'sine';
          osc.frequency.setValueAtTime(freq, start);

          gain.gain.setValueAtTime(0, start);
          gain.gain.linearRampToValueAtTime(this.volume * 0.8, start + 0.02);
          gain.gain.exponentialRampToValueAtTime(0.0001, start + 0.22);

          osc.connect(gain);
          gain.connect(this.ctx.destination);

          osc.start(start);
          osc.stop(start + 0.23);
        });
      } catch (e) {}
    }

    playEmotionCue(emotion) {
      if (!this.enabled) return;
      this._init();
      if (!this.ctx) return;

      const cues = {
        happy: [659.25, 880.00],
        excited: [587.33, 783.99, 1046.50],
        eureka: [523.25, 659.25, 783.99, 1046.50],
        curious: [440.00, 659.25],
        searching: [440.00, 523.25, 659.25],
        thinking: [523.25, 659.25],
        confused: [493.88, 440.00],
        concerned: [440.00, 392.00],
        listening: [587.33, 659.25],
        skeptical: [493.88, 523.25, 466.16],
        neutral: [523.25],
        idle: [392.00],
        bored: [349.23]
      };

      const seq = cues[emotion] || [523.25];
      seq.forEach((freq, idx) => {
        setTimeout(() => {
          this.playBlip(freq);
        }, idx * 60);
      });
    }
  }

  const synth = new CelesteSynthesizer();


  // ── State ──────────────────────────────────────────────────────

  let ws = null;
  let wsRetryDelay = 1000;
  let currentView = 'chat';
  let currentEmotion = 'neutral';


  // ── DOM Elements ───────────────────────────────────────────────

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  const statusDot = $('#status-dot');
  const statusText = $('#status-text');
  const victorAvatar = $('#victor-avatar');
  const avatarCard = $('#avatar-card');
  const avatarAura = $('#avatar-aura');
  const entityStatusLine = $('#entity-status-line');
  const emotionBadge = $('#emotion-badge');
  const emotionIcon = $('#emotion-icon');
  const emotionName = $('#emotion-name');
  const viewTitle = $('#view-title');
  const modelName = $('#model-name');
  const hudModelPill = $('#hud-model-pill');
  const btnSoundToggle = $('#btn-sound-toggle');
  const soundIndicatorIcon = $('#sound-indicator-icon');
  const btnClear = $('#btn-clear');

  const chatFeed = $('#chat-feed');
  const chatEmpty = $('#chat-empty');
  const chatInput = $('#chat-input');
  const btnSend = $('#btn-send');
  const btnVoice = $('#btn-voice');
  const voiceListeningBar = $('#voice-listening-bar');
  const voiceTranscriptPreview = $('#voice-transcript-preview');

  const hudDrawerOverlay = $('#hud-drawer-overlay');
  const tasksContainer = $('#tasks-container');
  const factsList = $('#facts-list');
  const prefsList = $('#prefs-list');
  const factInput = $('#fact-input');
  const btnAddFact = $('#btn-add-fact');
  const toolsList = $('#tools-list');
  const modelSelect = $('#model-select');
  const modelsGrid = $('#models-grid');
  const btnRefreshModels = $('#btn-refresh-models');
  const soundToggle = $('#sound-toggle');
  const btnLaunchMascot = $('#btn-launch-mascot');
  const toggleAutohide = $('#toggle-autohide');
  const selectCompanionScale = $('#select-companion-scale');
  const shellStatus = $('#shell-status');

  const permModal = $('#permission-modal');
  const permDesc = $('#perm-desc');
  const permDetails = $('#perm-details');
  const btnPermAllow = $('#btn-perm-allow');
  const btnPermAlways = $('#btn-perm-always');
  const btnPermDeny = $('#btn-perm-deny');


  // ── Dynamic Emotion & UI Theming Engine ────────────────────────
  // Dynamically alters document dataset so all CSS variables shift smoothly

  function setEmotion(name, playCue = true, updatePersonality = false) {
    if (!EMOTIONS[name]) name = 'neutral';
    currentEmotion = name;
    const data = EMOTIONS[name];

    // Shift entire HTML / Body Theme Color Variables!
    document.documentElement.dataset.emotion = name;
    document.body.dataset.emotion = name;

    // Smooth sprite transition
    if (victorAvatar) {
      victorAvatar.style.opacity = '0.35';
      setTimeout(() => {
        victorAvatar.src = data.sprite;
        victorAvatar.style.opacity = '1';
      }, 90);
    }

    // Telemetry indicators (zero emoji)
    if (emotionIcon) emotionIcon.textContent = '';
    if (emotionName) emotionName.textContent = data.label;
    if (statusText && updatePersonality) {
      statusText.textContent = data.desc;
    }
    if (entityStatusLine) {
      entityStatusLine.textContent = `SOUL ENGINE // ${data.label}`;
    }

    // Emotion Studio buttons in Settings
    $$('.emo-preview-btn, .emotion-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.emotion === name);
    });

    if (playCue) {
      synth.playEmotionCue(name);
    }
  }


  // ── Dynamic Poke / Click (NO Mechanical Cycling!) ──────────────
  // Clicking Victor pokes him organically; if idle he wakes up, otherwise reacts in-character

  function handleAvatarClick() {
    synth.playBlip(783.99);

    fetch('/api/poke', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })
    .then(res => res.json())
    .then(data => {
      if (data && data.emotion) {
        setEmotion(data.emotion, true, true);
        if (data.message) {
          appendMessage('Victor', data.message);
          synth.playSpeechStream(4);
        }
      }
    })
    .catch(() => {
      // Offline fallback
      if (currentEmotion === 'idle') {
        setEmotion('neutral', true, true);
        appendMessage('Victor', 'Awake. Neural systems active.');
      } else {
        const desc = EMOTIONS[currentEmotion]?.desc || 'Standing by.';
        appendMessage('Victor', desc);
      }
    });
  }

  if (avatarCard) {
    avatarCard.addEventListener('click', handleAvatarClick);
  }


  // ── HUD Navigation & Drawer Overlay ────────────────────────────

  function openDrawer(viewName) {
    currentView = viewName;

    // Update bottom tabs
    $$('.hud-nav-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.view === viewName);
    });

    if (viewName === 'chat') {
      hudDrawerOverlay.classList.remove('open');
      $$('.hud-drawer').forEach(d => d.classList.remove('active'));
      if (viewTitle) viewTitle.textContent = '[ NEURAL CORE // ONLINE ]';
      return;
    }

    // Open overlay and activate specific drawer panel
    hudDrawerOverlay.classList.add('open');
    $$('.hud-drawer').forEach(d => {
      d.classList.toggle('active', d.id === `view-${viewName}`);
    });

    if (viewName === 'tasks') {
      if (viewTitle) viewTitle.textContent = '[ COGNITIVE TASK PIPELINE ]';
      loadTasks();
    } else if (viewName === 'memory') {
      if (viewTitle) viewTitle.textContent = '[ PERSISTENT MEMORY MATRIX ]';
      loadMemory();
    } else if (viewName === 'tools') {
      if (viewTitle) viewTitle.textContent = '[ CONNECTED TOOL REGISTRY ]';
      loadTools();
    } else if (viewName === 'settings') {
      if (viewTitle) viewTitle.textContent = '[ SYSTEM CONFIG & MODELS ]';
      loadSettings();
    }
  }

  function closeDrawer() {
    openDrawer('chat');
  }

  $$('.hud-nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      openDrawer(tab.dataset.view);
    });
  });

  $$('[data-close-drawer]').forEach(btn => {
    btn.addEventListener('click', closeDrawer);
  });

  // Clicking outside drawer in overlay backdrop closes it
  if (hudDrawerOverlay) {
    hudDrawerOverlay.addEventListener('click', (e) => {
      if (e.target === hudDrawerOverlay) {
        closeDrawer();
      }
    });
  }

  // Escape key closes drawer
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeDrawer();
    }
  });

  // Quick model tag in header opens settings
  if (hudModelPill) {
    hudModelPill.addEventListener('click', () => {
      openDrawer('settings');
    });
  }


  // ── Emotion Studio Buttons (Settings) ──────────────────────────

  $$('.emotion-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const emo = btn.dataset.emotion;
      setEmotion(emo, true, true);
      fetch('/api/emotion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ emotion: emo, reason: 'studio_preview' })
      }).catch(() => {});
    });
  });


  // ── Audio Controls ─────────────────────────────────────────────

  function toggleSound() {
    synth.enabled = !synth.enabled;
    const label = synth.enabled ? 'CHIMES' : 'MUTED';
    if (btnSoundToggle) {
      btnSoundToggle.innerHTML = `<span id="sound-indicator-icon">${synth.enabled ? '&#9835;' : '&#10006;'}</span> ${label}`;
    }
    if (soundToggle) {
      soundToggle.classList.toggle('on', synth.enabled);
    }
    if (synth.enabled) {
      synth.playBlip(659.25);
    }
  }

  if (btnSoundToggle) btnSoundToggle.addEventListener('click', toggleSound);
  if (soundToggle) soundToggle.addEventListener('click', toggleSound);


  // ── Text Formatting & Sanitation ───────────────────────────────

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function stripEmojis(str) {
    return str.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{FE00}-\u{FE0F}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{200D}\u{20E3}\u{E0020}-\u{E007F}]/gu, '').trim();
  }

  function formatMarkdown(text) {
    let html = escapeHtml(text);

    // Code blocks
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
      return `<pre><code>${code.trim()}</code></pre>`;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bold & Italic
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

    const paras = html.split(/\n\n+/).filter(p => p.trim());
    if (paras.length > 1) {
      html = paras.map(p => p.startsWith('<pre>') ? p : `<p>${p.replace(/\n/g, '<br>')}</p>`).join('');
    } else {
      html = html.replace(/\n/g, '<br>');
    }

    return html;
  }


  // ── Centered Monologue & Chat Rendering ────────────────────────

  function hideEmptyState() {
    if (chatEmpty) chatEmpty.style.display = 'none';
  }

  function appendMessage(sender, text) {
    hideEmptyState();
    const msg = document.createElement('div');
    const isAssistant = sender.toLowerCase() === 'victor';
    msg.className = `message ${isAssistant ? 'assistant' : 'user'}`;

    if (!isAssistant) {
      const label = document.createElement('div');
      label.className = 'message-sender';
      label.textContent = '[ INQUIRY ]';
      msg.appendChild(label);
    }

    const body = document.createElement('div');
    body.className = 'message-body';
    body.innerHTML = formatMarkdown(stripEmojis(text));
    msg.appendChild(body);

    chatFeed.appendChild(msg);
    scrollToBottom();
    return msg;
  }

  function appendThinking() {
    hideEmptyState();
    removeThinking();

    const el = document.createElement('div');
    el.className = 'message assistant thinking';
    el.id = 'active-thinking-bubble';

    const body = document.createElement('div');
    body.className = 'message-body';
    body.innerHTML = '<span class="thinking-dot"></span><span class="thinking-dot"></span><span class="thinking-dot"></span>';
    el.appendChild(body);

    chatFeed.appendChild(el);
    scrollToBottom();
    return el;
  }

  function removeThinking() {
    const el = $('#active-thinking-bubble');
    if (el) el.remove();
  }

  function scrollToBottom() {
    requestAnimationFrame(() => {
      chatFeed.scrollTop = chatFeed.scrollHeight;
    });
  }

  // Textarea auto-resize
  chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
  });


  // ── Send Message ───────────────────────────────────────────────

  function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    appendMessage('You', text);
    chatInput.value = '';
    chatInput.style.height = 'auto';

    setEmotion('thinking', false);
    appendThinking();
    synth.playThinkingArpeggio();

    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'chat', message: text }));
    } else {
      fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      })
      .then(r => r.json())
      .then(handleChatResponse)
      .catch(() => {
        removeThinking();
        setEmotion('concerned');
      });
    }
  }

  if (btnSend) btnSend.addEventListener('click', sendMessage);
  if (chatInput) {
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }

  if (btnClear) {
    btnClear.addEventListener('click', () => {
      chatFeed.innerHTML = '';
      if (chatEmpty) {
        chatFeed.appendChild(chatEmpty);
        chatEmpty.style.display = '';
      }
      setEmotion('neutral', false);
      fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: '/clear' })
      }).catch(() => {});
    });
  }


  // ── Voice Mode (Speech-to-Text) ───────────────────────────────

  let recognition = null;
  let isListening = false;

  function initVoice() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      if (btnVoice) {
        btnVoice.title = 'Speech Recognition requires Chrome, Edge, or an active microphone permission';
        btnVoice.style.opacity = '0.5';
      }
      return;
    }

    try {
      recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        isListening = true;
        if (btnVoice) btnVoice.classList.add('listening');
        if (voiceListeningBar) {
          voiceListeningBar.style.display = 'flex';
          if (voiceTranscriptPreview) {
            voiceTranscriptPreview.textContent = 'Listening... speak naturally';
          }
        }
        setEmotion('curious', false);
        synth.playBlip(659.25);
      };

      recognition.onresult = (event) => {
        let interim = '';
        let final = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            final += event.results[i][0].transcript;
          } else {
            interim += event.results[i][0].transcript;
          }
        }
        const text = (final || interim).trim();
        if (text) {
          if (voiceTranscriptPreview) {
            voiceTranscriptPreview.textContent = `"${text}"`;
          }
          chatInput.value = text;
          chatInput.style.height = 'auto';
          chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
        }
      };

      recognition.onerror = (event) => {
        console.warn('Speech recognition error:', event.error);
        if (voiceTranscriptPreview) {
          voiceTranscriptPreview.textContent = `Voice status: ${event.error}`;
        }
        stopVoice();
      };

      recognition.onend = () => {
        stopVoice();
      };

      if (btnVoice) {
        btnVoice.addEventListener('click', (e) => {
          e.preventDefault();
          if (isListening) {
            try { recognition.stop(); } catch (err) {}
            stopVoice();
          } else {
            try {
              recognition.start();
            } catch (err) {
              console.warn('Recognition start failed:', err);
            }
          }
        });
      }
    } catch (err) {
      console.warn('Speech recognition initialization error:', err);
    }
  }

  function stopVoice() {
    isListening = false;
    if (btnVoice) btnVoice.classList.remove('listening');
    setTimeout(() => {
      if (!isListening && voiceListeningBar) {
        voiceListeningBar.style.display = 'none';
      }
    }, 1200);
    if (chatInput.value.trim()) {
      chatInput.focus();
      synth.playBlip(880.00);
    }
  }


  // ── WebSocket Telemetry & Cognitive Events ─────────────────────

  function initWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${location.host}/ws/chat`);

    ws.onopen = () => {
      wsRetryDelay = 1000;
      if (statusDot) statusDot.className = 'status-dot online';
      if (statusText && currentEmotion) {
        statusText.textContent = EMOTIONS[currentEmotion]?.desc || 'Neural Core Online';
      }
    };

    ws.onclose = () => {
      if (statusDot) statusDot.className = 'status-dot offline';
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
      } catch (e) {}
    };
  }

  function handleChatResponse(data) {
    removeThinking();

    const text = stripEmojis(data.content || data.response || '');
    if (text) {
      appendMessage('Victor', text);
      synth.playSpeechStream(6);
    }

    if (data.emotion) {
      setEmotion(data.emotion, false, true);
    }
  }

  function handleServerMessage(msg) {
    const eventObj = msg.event || msg;
    const topic = eventObj.topic || msg.topic || '';
    const data = eventObj.data || msg.data || {};

    if (msg.type === 'event' || topic) {
      if (topic === 'agent.emotion') {
        if (data.emotion) {
          setEmotion(data.emotion, true, true);
        }
      }

      if (topic === 'agent.started') {
        appendThinking();
        synth.playThinkingArpeggio();
      }

      if (topic === 'agent.thinking') {
        setEmotion('thinking', false);
      }

      if (topic === 'tool.completed') {
        if (['web_search', 'youtube', 'browser'].includes(data.tool)) {
          setEmotion('excited');
        } else {
          setEmotion('happy');
        }
      }

      if (topic === 'tool.failed') {
        setEmotion('concerned');
      }

      if (topic === 'agent.completed') {
        removeThinking();
        if (data.emotion) {
          setEmotion(data.emotion, false, true);
        }
      }

      if (topic === 'permission.requested') {
        setEmotion('confused');
        showPermissionModal(data);
      }
    }

    if (msg.type === 'chat_result') {
      handleChatResponse(msg.data || msg);
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
      tasksContainer.innerHTML = '<div class="tasks-empty">No active tasks. Victor logs multi-step operations here.</div>';
      return;
    }

    tasks.forEach(task => {
      const card = document.createElement('div');
      card.className = 'task-card';

      const header = document.createElement('div');
      header.className = 'task-header';

      const title = document.createElement('span');
      title.className = 'task-title';
      title.textContent = task.goal || task.title || 'Autonomous Task';

      const status = document.createElement('span');
      status.className = `task-status ${task.status}`;
      status.textContent = (task.status || 'pending').toUpperCase();

      header.appendChild(title);
      header.appendChild(status);
      card.appendChild(header);

      if (task.steps && task.steps.length) {
        const steps = document.createElement('div');
        steps.className = 'task-steps';
        task.steps.forEach(step => {
          const s = document.createElement('div');
          s.className = 'task-step';
          s.textContent = `[>] ${step.name || step.tool}`;
          if (step.duration) {
            const time = document.createElement('span');
            time.className = 'step-time';
            time.textContent = `${step.duration.toFixed(1)}s`;
            s.appendChild(time);
          }
          steps.appendChild(s);
        });
        card.appendChild(steps);
      }

      tasksContainer.appendChild(card);
    });
  }


  // ── Memory ─────────────────────────────────────────────────────

  async function loadMemory() {
    try {
      const res = await fetch('/api/memory');
      const data = await res.json();
      renderFacts(data.facts || []);
      renderPrefs(data.preferences || {});
    } catch (e) {}
  }

  function renderFacts(facts) {
    factsList.innerHTML = '';
    facts.forEach(fact => {
      const li = document.createElement('li');
      li.className = 'memory-item';

      const text = document.createElement('span');
      text.className = 'fact-text';
      text.textContent = fact.content || fact.text || fact;

      const del = document.createElement('button');
      del.className = 'memory-delete-btn';
      del.textContent = '[DEL]';
      del.addEventListener('click', async () => {
        const factId = fact.id || fact.fact_id;
        if (factId) {
          await fetch(`/api/memory/fact/${factId}`, { method: 'DELETE' });
          loadMemory();
        }
      });

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
      const text = document.createElement('span');
      text.className = 'fact-text';
      if (Array.isArray(entry)) {
        text.textContent = `${entry[0]}: ${entry[1]}`;
      } else {
        text.textContent = `${entry.key || ''}: ${entry.value || ''}`;
      }
      li.appendChild(text);
      prefsList.appendChild(li);
    });
  }

  if (btnAddFact) {
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
      setEmotion('happy');
    });
  }

  if (factInput) {
    factInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        btnAddFact.click();
      }
    });
  }


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
      const card = document.createElement('div');
      card.className = 'tool-card';

      const name = document.createElement('div');
      name.className = 'tool-name';
      name.textContent = `[ ${tool.name} ]`;

      const desc = document.createElement('div');
      desc.className = 'tool-desc';
      desc.textContent = tool.description || '';

      card.appendChild(name);
      card.appendChild(desc);
      toolsList.appendChild(card);
    });
  }


  // ── Local Neural Models (Ollama) Switcher ──────────────────────

  async function loadSettings() {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      if (shellStatus) {
        shellStatus.textContent = data.security?.allow_shell ? 'ENABLED' : 'DISABLED';
      }
      if (data.emotion) {
        setEmotion(data.emotion, false);
      }
      if (data.companion_options) {
        if (toggleAutohide) {
          toggleAutohide.classList.toggle('on', data.companion_options.auto_hide !== false);
        }
        if (selectCompanionScale && data.companion_options.scale) {
          selectCompanionScale.value = data.companion_options.scale;
        }
      }
    } catch (e) {}

    await refreshModelsList();
  }

  // Emotion Studio preview buttons
  $$('.emo-preview-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const emo = btn.dataset.emotion;
      if (emo) {
        setEmotion(emo, true, true);
        try {
          await fetch('/api/emotion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ emotion: emo })
          });
        } catch (e) {}
      }
    });
  });

  // Companion Options Handlers
  if (toggleAutohide) {
    toggleAutohide.addEventListener('click', async () => {
      toggleAutohide.classList.toggle('on');
      const isAuto = toggleAutohide.classList.contains('on');
      try {
        await fetch('/api/mascot/options', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ auto_hide: isAuto })
        });
      } catch (e) {}
    });
  }

  if (selectCompanionScale) {
    selectCompanionScale.addEventListener('change', async () => {
      const scaleVal = selectCompanionScale.value;
      try {
        await fetch('/api/mascot/options', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scale: scaleVal })
        });
      } catch (e) {}
    });
  }

  // ── Workshop Focus Tracking (Desktop Companion Continuity) ────
  // When Workshop is active in front, desktop companion auto-hides.
  // When Workshop is minimized or blurred, desktop companion reveals itself.

  function reportWorkshopFocus(focused) {
    fetch('/api/mascot/visibility', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ active: !!focused })
    }).catch(() => {});
  }

  window.addEventListener('focus', () => reportWorkshopFocus(true));
  window.addEventListener('blur', () => reportWorkshopFocus(false));
  document.addEventListener('visibilitychange', () => {
    reportWorkshopFocus(!document.hidden);
  });

  async function refreshModelsList() {
    try {
      if (btnRefreshModels) {
        btnRefreshModels.style.opacity = '0.6';
        const svg = btnRefreshModels.querySelector('svg');
        if (svg) svg.style.transform = 'rotate(180deg)';
      }

      const res = await fetch('/api/models');
      const data = await res.json();

      const detailed = data.models || [];
      const modelNames = data.available_models || data.available || [];
      const current = data.current_model || data.current || '';

      // Update dropdown
      if (modelSelect) {
        modelSelect.innerHTML = '';
        if (detailed.length) {
          detailed.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.name;
            opt.textContent = m.label || m.name;
            if (m.name === current) opt.selected = true;
            modelSelect.appendChild(opt);
          });
        } else if (modelNames.length) {
          modelNames.forEach(name => {
            const opt = document.createElement('option');
            opt.value = name;
            opt.textContent = name;
            if (name === current) opt.selected = true;
            modelSelect.appendChild(opt);
          });
        } else {
          const opt = document.createElement('option');
          opt.value = current || 'qwen:0.5b';
          opt.textContent = current || 'qwen:0.5b (0.5B)';
          modelSelect.appendChild(opt);
        }
      }

      // Update model cards grid
      if (modelsGrid) {
        modelsGrid.innerHTML = '';
        const items = detailed.length ? detailed : modelNames.map(n => ({
          name: n,
          label: n,
          parameter_size: n.includes('0.5') ? '0.5B' : (n.includes('1.5') ? '1.5B' : (n.includes('3') ? '3B' : ''))
        }));

        items.forEach(m => {
          const card = document.createElement('button');
          const isActive = m.name === current;
          card.className = `model-card-btn${isActive ? ' active' : ''}`;
          card.dataset.model = m.name;

          const title = document.createElement('span');
          title.className = 'm-name';
          title.textContent = m.name;

          const tag = document.createElement('span');
          tag.className = 'm-tag';
          tag.textContent = isActive ? '[ ACTIVE ]' : (m.parameter_size || '[ LOCAL ]');

          card.appendChild(title);
          card.appendChild(tag);

          card.addEventListener('click', async () => {
            if (m.name === current) return;
            await doSwitchModel(m.name);
          });

          modelsGrid.appendChild(card);
        });
      }

      if (btnRefreshModels) {
        setTimeout(() => {
          btnRefreshModels.style.opacity = '1';
          const svg = btnRefreshModels.querySelector('svg');
          if (svg) svg.style.transform = '';
        }, 300);
      }
    } catch (e) {
      console.warn('Could not refresh models list:', e);
    }
  }

  async function doSwitchModel(modelNameVal) {
    try {
      await fetch('/api/models/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_name: modelNameVal })
      });
      if (modelName) modelName.textContent = modelNameVal;
      setEmotion('curious', true, true);
      synth.playEmotionCue('happy');
      await refreshModelsList();
    } catch (e) {
      console.warn('Switch model failed:', e);
    }
  }

  if (modelSelect) {
    modelSelect.addEventListener('change', async () => {
      await doSwitchModel(modelSelect.value);
    });
  }

  if (btnRefreshModels) {
    btnRefreshModels.addEventListener('click', async () => {
      synth.playBlip(587.33);
      await refreshModelsList();
    });
  }

  // Launch Mascot
  if (btnLaunchMascot) {
    btnLaunchMascot.addEventListener('click', async () => {
      try {
        await fetch('/api/mascot/launch', { method: 'POST' });
        btnLaunchMascot.textContent = 'COMPANION LAUNCHED';
        synth.playEmotionCue('happy');
        setTimeout(() => { btnLaunchMascot.textContent = 'LAUNCH COMPANION'; }, 2000);
      } catch (e) {}
    });
  }


  // ── Permissions ────────────────────────────────────────────────

  let pendingPermissionId = null;

  function showPermissionModal(data) {
    pendingPermissionId = data.request_id || data.id;
    permDesc.textContent = data.description || 'Victor requests authorization for an external computer action.';
    permDetails.textContent = data.details || data.action || 'system action';
    permModal.classList.add('open');
  }

  async function resolvePermission(decision) {
    if (!pendingPermissionId) return;
    permModal.classList.remove('open');
    try {
      await fetch('/api/permissions/respond', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_id: pendingPermissionId, decision })
      });
      if (decision === 'deny') {
        setEmotion('concerned');
      } else {
        setEmotion('happy');
      }
    } catch (e) {}
    pendingPermissionId = null;
  }

  if (btnPermAllow) btnPermAllow.addEventListener('click', () => resolvePermission('allow_once'));
  if (btnPermAlways) btnPermAlways.addEventListener('click', () => resolvePermission('always_allow'));
  if (btnPermDeny) btnPermDeny.addEventListener('click', () => resolvePermission('deny'));


  // ── Initialization ─────────────────────────────────────────────

  async function init() {
    let attempts = 6;
    while (attempts > 0) {
      try {
        const res = await fetch('/api/status');
        if (res.ok) {
          const data = await res.json();
          if (modelName) modelName.textContent = data.model || 'qwen:0.5b';
          if (data.emotion) {
            setEmotion(data.emotion, false, true);
          }
          if (data.companion_options) {
            if (toggleAutohide) {
              toggleAutohide.classList.toggle('on', data.companion_options.auto_hide !== false);
            }
            if (selectCompanionScale && data.companion_options.scale) {
              selectCompanionScale.value = data.companion_options.scale;
            }
          }
          break;
        }
      } catch (e) {}
      attempts--;
      await new Promise(r => setTimeout(r, 500));
    }

    reportWorkshopFocus(!document.hidden && (document.hasFocus ? document.hasFocus() : true));
    refreshModelsList();
    initVoice();
    initWebSocket();
  }

  init();

})();
