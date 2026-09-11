/* ================================================================
   Victor — The Artificial Soul
   Workshop Client & Cognitive Audio Engine
   
   8-Emotion Sprite Integration, Celeste Procedural Sound Synthesis,
   Real-Time Telemetry & Cognitive Intelligence Loop
   ================================================================ */

(function () {
  'use strict';

  // ── 8 Artificial Soul Emotions ──────────────────────────────────

  const EMOTIONS = {
    neutral:   { emoji: '😐', label: 'Neutral',   sprite: '/static/sprites/neutral.png',   color: '#E8E4DE', desc: 'Normal interaction' },
    happy:     { emoji: '😊', label: 'Happy',     sprite: '/static/sprites/happy.png',     color: '#8BA888', desc: 'Successful outcome' },
    curious:   { emoji: '🤔', label: 'Curious',   sprite: '/static/sprites/curious.png',   color: '#C8956C', desc: 'Exploring & learning' },
    idle:      { emoji: '😴', label: 'Idle',      sprite: '/static/sprites/idle.png',      color: '#8A8578', desc: 'Resting & standby' },
    thinking:  { emoji: '🧠', label: 'Thinking',  sprite: '/static/sprites/thinking.png',  color: '#D4A574', desc: 'Processing reasoning' },
    excited:   { emoji: '😮', label: 'Excited',   sprite: '/static/sprites/excited.png',   color: '#F59E0B', desc: 'Interesting discovery' },
    confused:  { emoji: '😕', label: 'Confused',  sprite: '/static/sprites/confused.png',  color: '#E07A5F', desc: 'Unclear problem' },
    concerned: { emoji: '😔', label: 'Concerned', sprite: '/static/sprites/concerned.png', color: '#B85C5C', desc: 'Encountered failure' }
  };


  // ── Celeste-Style Procedural Audio Synthesizer ─────────────────
  // No robotic TTS! Pure electronic pentatonic blips & warm chimes.

  class CelesteSynthesizer {
    constructor() {
      this.ctx = null;
      this.enabled = true;
      this.volume = 0.12;
      // Warm pentatonic frequencies (Hz)
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

    // Single retro dialogue blip
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

    // Melodic speech burst synchronized with response
    playSpeechStream(tokenCount = 5) {
      if (!this.enabled) return;
      const count = Math.min(tokenCount, 8);
      for (let i = 0; i < count; i++) {
        setTimeout(() => {
          this.playBlip();
        }, i * 45);
      }
    }

    // Thinking musical arpeggio
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

    // Emotion-specific sound cue
    playEmotionCue(emotion) {
      if (!this.enabled) return;
      this._init();
      if (!this.ctx) return;

      const cues = {
        happy: [659.25, 880.00],
        excited: [587.33, 783.99, 1046.50],
        curious: [440.00, 659.25],
        thinking: [523.25, 659.25],
        confused: [493.88, 440.00],
        concerned: [440.00, 392.00],
        neutral: [523.25],
        idle: [392.00]
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
  let currentEmotion = 'idle';


  // ── DOM References ─────────────────────────────────────────────

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  const statusDot = $('#status-dot');
  const statusText = $('#status-text');
  const victorAvatar = $('#victor-avatar');
  const avatarCard = $('#avatar-card');
  const avatarFrame = $('.avatar-frame');
  const headerMoodTag = $('#header-mood-tag');
  const emotionBadge = $('#emotion-badge');
  const emotionIcon = $('#emotion-icon');
  const emotionName = $('#emotion-name');
  const cognitiveBadge = $('#cognitive-badge');
  const btnSoundToggle = $('#btn-sound-toggle');
  const soundIndicatorIcon = $('#sound-indicator-icon');

  const modelName = $('#model-name');
  const viewTitle = $('#view-title');
  const chatFeed = $('#chat-feed');
  const chatEmpty = $('#chat-empty');
  const chatInput = $('#chat-input');
  const btnSend = $('#btn-send');
  const btnClear = $('#btn-clear');
  const btnVoice = $('#btn-voice');
  const voiceListeningBar = $('#voice-listening-bar');
  const voiceTranscriptPreview = $('#voice-transcript-preview');

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
  const shellStatus = $('#shell-status');
  const permModal = $('#permission-modal');
  const permDesc = $('#perm-desc');
  const permDetails = $('#perm-details');
  const btnPermAllow = $('#btn-perm-allow');
  const btnPermAlways = $('#btn-perm-always');
  const btnPermDeny = $('#btn-perm-deny');


  // ── Emotion & Artificial Soul State ─────────────────────────────

  const EMOTION_SEQUENCE = [
    'neutral',
    'happy',
    'curious',
    'thinking',
    'excited',
    'confused',
    'concerned',
    'idle'
  ];

  const EMOTION_REACTIONS = {
    neutral: 'Standing by. Calm and level-headed.',
    happy: 'Pleasant state. Systems running cleanly.',
    curious: 'Observing closely. Noticed something intriguing.',
    thinking: 'Synthesizing thoughts. Quiet processing.',
    excited: 'Fascinating discovery! Energy elevated.',
    confused: 'Puzzling state. Query needs clarity.',
    concerned: 'Issue detected. Proceeding with caution.',
    idle: 'Drifting in standby. Ready whenever you are.'
  };

  const MOOD_TAGS = {
    neutral: 'Level-headed',
    happy: 'Pleased',
    curious: 'Inquisitive',
    thinking: 'Reflecting',
    excited: 'Intrigued',
    confused: 'Puzzled',
    concerned: 'Careful',
    idle: 'At rest'
  };

  function setEmotion(name, playCue = true, updatePersonality = false) {
    if (!EMOTIONS[name]) name = 'neutral';
    currentEmotion = name;
    const data = EMOTIONS[name];

    // Update sprite with smooth transition
    if (victorAvatar) {
      victorAvatar.style.opacity = '0.3';
      setTimeout(() => {
        victorAvatar.src = data.sprite;
        victorAvatar.style.opacity = '1';
      }, 90);
    }

    // Update emotion badge
    if (emotionIcon) emotionIcon.textContent = data.emoji;
    if (emotionName) emotionName.textContent = data.label;
    if (emotionBadge) {
      emotionBadge.className = `emotion-badge ${name}`;
    }

    // Update header mood tag
    if (headerMoodTag) {
      headerMoodTag.textContent = MOOD_TAGS[name] || data.label;
    }

    // Update personality status line
    if (updatePersonality && statusText && EMOTION_REACTIONS[name]) {
      statusText.textContent = EMOTION_REACTIONS[name];
    }

    // Highlight active button in Emotion Studio (Settings)
    $$('.emotion-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.emotion === name);
    });

    // Sound cue
    if (playCue) {
      synth.playEmotionCue(name);
    }
  }

  // Interactive Avatar Click: cycle emotions and play chime
  function handleAvatarClick() {
    const nextIdx = (EMOTION_SEQUENCE.indexOf(currentEmotion) + 1) % EMOTION_SEQUENCE.length;
    const nextEmo = EMOTION_SEQUENCE[nextIdx];
    setEmotion(nextEmo, true, true);

    // Inform backend so desktop mascot synchronizes
    fetch('/api/emotion', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ emotion: nextEmo, reason: 'user_click' })
    }).catch(() => {});
  }

  if (avatarCard) {
    avatarCard.addEventListener('click', handleAvatarClick);
  } else if (avatarFrame) {
    avatarFrame.addEventListener('click', handleAvatarClick);
  } else if (victorAvatar) {
    victorAvatar.addEventListener('click', handleAvatarClick);
  }

  // Emotion Studio Buttons
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

    if (view === 'tasks') loadTasks();
    if (view === 'memory') loadMemory();
    if (view === 'tools') loadTools();
    if (view === 'settings') loadSettings();

    btnClear.style.display = view === 'chat' ? '' : 'none';
  }

  $$('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => switchView(btn.dataset.view));
  });


  // ── Agent State & Cognitive Loop ───────────────────────────────

  function setAgentState(state, cognitivePhase = '') {
    statusDot.className = 'status-dot';
    if (state === 'thinking' || state === 'working') {
      statusDot.classList.add(state);
    } else if (state === 'error') {
      statusDot.classList.add('error');
    }

    if (state === 'idle' || state === 'done') {
      statusText.textContent = EMOTION_REACTIONS[currentEmotion] || 'Quietly present';
    } else if (cognitivePhase) {
      statusText.textContent = cognitivePhase;
    } else {
      statusText.textContent = state + '...';
    }

    if (cognitiveBadge) {
      if (cognitivePhase) {
        cognitiveBadge.textContent = cognitivePhase;
        cognitiveBadge.classList.add('active');
      } else if (state === 'thinking') {
        cognitiveBadge.textContent = 'Reasoning • Synthesizing';
        cognitiveBadge.classList.add('active');
      } else if (state === 'working') {
        cognitiveBadge.textContent = 'Acting • Observing';
        cognitiveBadge.classList.add('active');
      } else {
        cognitiveBadge.textContent = 'Perceive • Act • Reflect';
        cognitiveBadge.classList.remove('active');
      }
    }
  }


  // ── Audio Controls ─────────────────────────────────────────────

  function toggleSound() {
    synth.enabled = !synth.enabled;
    const label = synth.enabled ? 'Chimes: On' : 'Chimes: Off';
    btnSoundToggle.innerHTML = `<span id="sound-indicator-icon">${synth.enabled ? '&#9835;' : '&#10006;'}</span> ${label}`;
    if (soundToggle) {
      soundToggle.classList.toggle('on', synth.enabled);
    }
    if (synth.enabled) {
      synth.playBlip(659.25);
    }
  }

  if (btnSoundToggle) {
    btnSoundToggle.addEventListener('click', toggleSound);
  }
  if (soundToggle) {
    soundToggle.addEventListener('click', toggleSound);
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
    html = html.replace(/(^|[\s>])(https?:\/\/[^\s<]+)/gm, '$1<a href="$2" target="_blank" rel="noopener">$2</a>');

    const paras = html.split(/\n\n+/).filter(p => p.trim());
    if (paras.length > 1) {
      html = paras.map(p => p.startsWith('<pre>') ? p : `<p>${p.replace(/\n/g, '<br>')}</p>`).join('');
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

  // Textarea auto-resize
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

    setEmotion('curious', false);
    setAgentState('thinking', 'Perceiving Directive');
    appendThinking();
    synth.playThinkingArpeggio();

    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'chat', message: text }));
    } else {
      // Fallback to REST
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
        setAgentState('idle');
      });
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
    setEmotion('neutral', false);
    fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: '/clear' })
    }).catch(() => {});
  });


  // ── Voice Mode (Speech-to-Text) ───────────────────────────────

  let recognition = null;
  let isListening = false;

  function initVoice() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      if (btnVoice) {
        btnVoice.title = 'Speech Recognition requires Chrome, Edge, or an active microphone permission';
        btnVoice.style.opacity = '0.55';
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
        if (btnVoice) btnVoice.classList.add('recording');
        if (voiceListeningBar) {
          voiceListeningBar.style.display = 'flex';
          if (voiceTranscriptPreview) {
            voiceTranscriptPreview.textContent = 'Listening... speak naturally';
          }
        }
        setEmotion('curious', false, false);
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
          chatInput.style.height = Math.min(chatInput.scrollHeight, 160) + 'px';
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
    if (btnVoice) btnVoice.classList.remove('recording');
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
      } catch (e) {}
    };
  }

  function handleChatResponse(data) {
    removeThinking();
    setAgentState('idle');

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
    // Normal event or nested event format
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
        setAgentState('thinking', 'Perceive & Decompose');
        appendThinking();
        synth.playThinkingArpeggio();
      }

      if (topic === 'agent.thinking') {
        setAgentState('thinking', 'Neural Inference');
        setEmotion('thinking', false);
      }

      if (topic === 'tool.started') {
        removeThinking();
        setAgentState('working', `Acting: ${data.tool || 'tool'}`);
        currentToolAnnotation = appendToolAnnotation(data.tool || 'tool', 'active');
      }

      if (topic === 'tool.completed') {
        if (currentToolAnnotation) {
          currentToolAnnotation.classList.remove('active');
          currentToolAnnotation.classList.add('done');
          const dur = data.duration ? `${data.duration.toFixed(1)}s` : '';
          if (dur) currentToolAnnotation.textContent += ` \u00B7 ${dur}`;
          currentToolAnnotation = null;
        }
        if (['web_search', 'youtube', 'browser'].includes(data.tool)) {
          setEmotion('excited');
        } else {
          setEmotion('happy');
        }
      }

      if (topic === 'tool.failed') {
        if (currentToolAnnotation) {
          currentToolAnnotation.classList.remove('active');
          currentToolAnnotation.classList.add('failed');
          currentToolAnnotation = null;
        }
        setEmotion('concerned');
      }

      if (topic === 'agent.completed') {
        setAgentState('idle');
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
      tasksContainer.innerHTML = '<div class="tasks-empty">No tasks yet. Victor creates autonomous task plans during multi-step cognitive loops.</div>';
      return;
    }

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
    } catch (e) {}
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
    setEmotion('happy');
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
      if (data.emotion) {
        setEmotion(data.emotion, false);
      }
    } catch (e) {}

    await refreshModelsList();
  }

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
          opt.value = current || 'qwen2:1.5b';
          opt.textContent = current || 'qwen2:1.5b (1.5B)';
          modelSelect.appendChild(opt);
        }
      }

      // Update models cards grid
      if (modelsGrid) {
        modelsGrid.innerHTML = '';
        const items = detailed.length ? detailed : modelNames.map(n => ({
          name: n,
          label: n,
          parameter_size: n.includes('0.5') ? '0.5B' : (n.includes('1.5') ? '1.5B' : (n.includes('3') ? '3B' : '')),
          size_str: '',
          is_small: n.includes('0.5') || n.includes('1.5') || n.includes('2') || n.includes('3')
        }));

        items.forEach(m => {
          const card = document.createElement('div');
          const isActive = m.name === current;
          card.className = `model-card${isActive ? ' active' : ''}`;
          card.dataset.model = m.name;

          const header = document.createElement('div');
          header.className = 'model-card-header';

          const title = document.createElement('span');
          title.className = 'model-card-name';
          title.textContent = m.name;

          const badge = document.createElement('span');
          badge.className = 'model-card-badge';
          badge.textContent = isActive ? 'Active' : 'Downloaded';

          header.appendChild(title);
          header.appendChild(badge);

          const meta = document.createElement('div');
          meta.className = 'model-card-meta';

          if (m.parameter_size) {
            const paramPill = document.createElement('span');
            paramPill.className = `model-card-pill${m.is_small ? ' small' : ''}`;
            paramPill.textContent = m.parameter_size;
            meta.appendChild(paramPill);
          }

          if (m.size_str) {
            const sizePill = document.createElement('span');
            sizePill.className = 'model-card-pill';
            sizePill.textContent = m.size_str;
            meta.appendChild(sizePill);
          }

          card.appendChild(header);
          card.appendChild(meta);

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

  // Launch Desktop Mascot
  btnLaunchMascot.addEventListener('click', async () => {
    try {
      await fetch('/api/mascot/launch', { method: 'POST' });
      btnLaunchMascot.textContent = 'Launched';
      synth.playEmotionCue('happy');
      setTimeout(() => { btnLaunchMascot.textContent = 'Launch'; }, 2000);
    } catch (e) {}
  });


  // ── Permission Modal ───────────────────────────────────────────

  let pendingPermissionId = null;

  function showPermissionModal(data) {
    pendingPermissionId = data.request_id || data.id;
    permDesc.textContent = data.description || 'Victor requests authorization for an external computer action.';
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
      if (decision === 'deny') {
        setEmotion('concerned');
      } else {
        setEmotion('happy');
      }
    } catch (e) {}
    pendingPermissionId = null;
  }

  btnPermAllow.addEventListener('click', () => resolvePermission('allow_once'));
  btnPermAlways.addEventListener('click', () => resolvePermission('always_allow'));
  btnPermDeny.addEventListener('click', () => resolvePermission('deny'));


  // ── Initialization ─────────────────────────────────────────────

  async function init() {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      modelName.textContent = data.model || 'qwen2:1.5b';
      if (data.emotion) {
        setEmotion(data.emotion, false, true);
      }
    } catch (e) {}

    refreshModelsList();
    initVoice();
    initWebSocket();
  }

  init();

})();
