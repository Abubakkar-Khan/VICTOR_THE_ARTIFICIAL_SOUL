/* ================================================================
   Dextex // The Artificial Soul
   Gamified Terminal Client, Dynamic Emotion Theming & Cognitive Audio
   Version 2.7.0
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

  const EMOTION_MOTTOS = {
    thinking:  'THINK. EXPLORE. SOLVE. REPEAT.',
    happy:     'IDEAS INTO ACTION.',
    excited:   'IDEAS INTO ACTION.',
    curious:   'CURIOSITY BUILDS BETTER ANSWERS.',
    neutral:   'CURIOSITY BUILDS BETTER ANSWERS.',
    confused:  'SAME CURIOSITY. BIGGER POSSIBILITIES.',
    skeptical: 'SAME CURIOSITY. BIGGER POSSIBILITIES.',
    concerned: 'ANOMALY DETECTED. RECALIBRATING.',
    eureka:    'INSIGHT UNLOCKED. EUREKA.',
    listening: 'RECEIVING INPUT VECTOR...',
    idle:      'CURIOSITY BUILDS BETTER ANSWERS.',
    bored:     'WAITING FOR NEXT DIRECTIVE.'
  };

  const MOTTO_LINES = {
    thinking:  ['THINK.', 'EXPLORE.', 'SOLVE.', 'REPEAT.'],
    happy:     ['IDEAS', 'INTO', 'ACTION.', ''],
    excited:   ['IDEAS', 'INTO', 'ACTION.', ''],
    curious:   ['CURIOSITY', 'BUILDS', 'BETTER', 'ANSWERS.'],
    neutral:   ['CURIOSITY', 'BUILDS', 'BETTER', 'ANSWERS.'],
    confused:  ['SAME', 'CURIOSITY.', 'BIGGER', 'POSSIBILITIES.'],
    skeptical: ['SAME', 'CURIOSITY.', 'BIGGER', 'POSSIBILITIES.'],
    concerned: ['ANOMALY', 'DETECTED.', 'RECALIBRATING.', ''],
    eureka:    ['INSIGHT', 'UNLOCKED.', 'EUREKA.', ''],
    listening: ['RECEIVING', 'INPUT', 'VECTOR...', ''],
    idle:      ['CURIOSITY', 'BUILDS', 'BETTER', 'ANSWERS.'],
    bored:     ['WAITING', 'FOR NEXT', 'DIRECTIVE.', '']
  };


  // ── Celeste-Style Procedural Audio Synthesizer ─────────────────
  // Electronic pentatonic blips & warm chimes (no robotic TTS)

  class CelesteSynthesizer {
    constructor() {
      this.ctx = null;
      this.enabled = true;
      this.volume = 0.028; // Soft and sweet, never piercing or jarring
      this.pentatonic = [783.99, 880.00, 1046.50, 1174.66, 1318.51, 1567.98, 1760.00]; // High crystal notes
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
        const overtone = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        const overtoneGain = this.ctx.createGain();

        const freq = freqOverride || this.pentatonic[Math.floor(Math.random() * this.pentatonic.length)];
        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, now);

        overtone.type = 'sine';
        overtone.frequency.setValueAtTime(freq * 2, now);

        // Smooth 2ms attack ramp, delicate bell decay
        gain.gain.setValueAtTime(0.0001, now);
        gain.gain.linearRampToValueAtTime(this.volume, now + 0.002);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.075);

        overtoneGain.gain.setValueAtTime(0.0001, now);
        overtoneGain.gain.linearRampToValueAtTime(this.volume * 0.12, now + 0.002);
        overtoneGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.040);

        osc.connect(gain);
        overtone.connect(overtoneGain);
        gain.connect(this.ctx.destination);
        overtoneGain.connect(this.ctx.destination);

        osc.start(now);
        overtone.start(now);
        osc.stop(now + 0.08);
        overtone.stop(now + 0.08);
      } catch (e) {}
    }

    playSpeechStream(tokenCount = 3) {
      if (!this.enabled) return;
      const count = Math.min(tokenCount, 4);
      for (let i = 0; i < count; i++) {
        setTimeout(() => {
          this.playBlip();
        }, i * 48);
      }
    }

    playThinkingArpeggio() {
      if (!this.enabled) return;
      this._init();
      if (!this.ctx) return;

      try {
        const notes = [783.99, 1046.50, 1318.51]; // G5, C6, E6 (Gentle ascending Celeste triad)
        notes.forEach((freq, idx) => {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          const start = this.ctx.currentTime + (idx * 0.06);

          osc.type = 'sine';
          osc.frequency.setValueAtTime(freq, start);

          gain.gain.setValueAtTime(0.0001, start);
          gain.gain.linearRampToValueAtTime(this.volume * 0.8, start + 0.005);
          gain.gain.exponentialRampToValueAtTime(0.0001, start + 0.18);

          osc.connect(gain);
          gain.connect(this.ctx.destination);

          osc.start(start);
          osc.stop(start + 0.19);
        });
      } catch (e) {}
    }

    playEmotionCue(emotion) {
      if (!this.enabled) return;
      this._init();
      if (!this.ctx) return;

      const cues = {
        happy: [1046.50, 1318.51],
        excited: [1046.50, 1318.51, 1567.98],
        eureka: [783.99, 1046.50, 1318.51, 1567.98],
        curious: [880.00, 1174.66],
        searching: [783.99, 1046.50, 1174.66],
        thinking: [880.00, 1046.50],
        confused: [987.77, 880.00],
        concerned: [783.99, 698.46],
        listening: [1046.50, 1174.66],
        skeptical: [987.77, 1046.50, 932.33],
        neutral: [1046.50],
        idle: [783.99],
        bored: [698.46]
      };

      const seq = cues[emotion] || [1046.50];
      seq.forEach((freq, idx) => {
        setTimeout(() => {
          this.playBlip(freq);
        }, idx * 55);
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
  const mottoText = $('#motto-text');
  const dexterBgAvatar = $('#dexter-bg-avatar');
  const statementText = $('#statement-text');
  const cursorBlock = $('#cursor-block');
  const userInquiryTrace = $('#user-inquiry-trace');
  const inquiryText = $('#inquiry-text');
  const conversationScrollArea = $('#conversation-scroll-area');
  const dialogueCenterpiece = $('#dialogue-centerpiece');

  const dexterAvatar = $('#dexter-avatar') || $('#victor-avatar');
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
  const selectClickAction = $('#select-click-action');
  const selectDialogTheme = $('#select-dialog-theme');
  const shellStatus = $('#shell-status');

  const permModal = $('#permission-modal');
  const permDesc = $('#perm-desc');
  const permDetails = $('#perm-details');
  const btnPermAllow = $('#btn-perm-allow');
  const btnPermAlways = $('#btn-perm-always');
  const btnPermDeny = $('#btn-perm-deny');


  // ── Dynamic Emotion & UI Theming Engine ────────────────────────
  // Dynamically alters document dataset so all CSS variables shift smoothly

  function updateMotto(emo) {
    const lines = MOTTO_LINES[emo] || MOTTO_LINES.neutral;
    for (let i = 1; i <= 4; i++) {
      const el = document.getElementById(`motto-line-${i}`);
      if (el) el.textContent = lines[i - 1] || '';
    }
    if (mottoText) {
      mottoText.textContent = EMOTION_MOTTOS[emo] || 'CURIOSITY BUILDS BETTER ANSWERS.';
    }
  }

  function triggerScreenGlitch() {
    document.body.dataset.glitch = 'true';
    synth.playBlip(329.63);
    setTimeout(() => {
      delete document.body.dataset.glitch;
    }, 720);
  }

  function setEmotion(name, playCue = true, updatePersonality = false) {
    if (!EMOTIONS[name]) name = 'neutral';
    currentEmotion = name;
    const data = EMOTIONS[name];

    // Shift entire HTML / Body Theme Color Variables!
    document.documentElement.dataset.emotion = name;
    document.body.dataset.emotion = name;

    // Update centered atmospheric background character
    if (dexterBgAvatar) {
      dexterBgAvatar.src = data.sprite;
    }

    // Update dynamic top motto blocks
    updateMotto(name);

    // Smooth sprite transition for secondary/hidden avatar
    if (dexterAvatar) {
      dexterAvatar.style.opacity = '0.35';
      setTimeout(() => {
        dexterAvatar.src = data.sprite;
        dexterAvatar.style.opacity = '1';
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


  // ── Unified Voice Input & Speech-to-Text (Click-to-Listen) ─────
  let isListeningVoice = false;
  let speechRecognitionInstance = null;

  async function toggleVoiceListening() {
    if (isListeningVoice) {
      stopVoiceListening();
      return;
    }

    isListeningVoice = true;
    setEmotion('listening', false);
    if (btnVoice) btnVoice.classList.add('listening');
    if (voiceListeningBar) voiceListeningBar.style.display = 'flex';
    if (voiceTranscriptPreview) voiceTranscriptPreview.textContent = 'Listening... speak naturally';
    synth.playBlip(783.99);

    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRec) {
      try {
        const recognition = new SpeechRec();
        speechRecognitionInstance = recognition;
        recognition.lang = 'en-US';
        recognition.continuous = false;
        recognition.interimResults = true;

        recognition.onresult = (event) => {
          let transcript = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            transcript += event.results[i][0].transcript;
          }
          if (voiceTranscriptPreview) voiceTranscriptPreview.textContent = `"${transcript}"`;
          if (event.results[0] && event.results[0].isFinal) {
            if (chatInput) chatInput.value = transcript.trim();
            stopVoiceListening();
            synth.playBlip(1046.50);
            sendMessage();
          }
        };

        recognition.onerror = (e) => {
          console.warn('Browser SpeechRecognition error, falling back to hardware mic:', e);
          fallbackBackendListen();
        };

        recognition.onend = () => {
          if (isListeningVoice) {
            stopVoiceListening();
          }
        };

        recognition.start();
        return;
      } catch (err) {
        console.warn('Could not start web SpeechRecognition:', err);
      }
    }

    // Fallback in WebView2 or desktop app: record hardware microphone directly via backend
    await fallbackBackendListen();
  }

  async function fallbackBackendListen() {
    if (voiceTranscriptPreview) voiceTranscriptPreview.textContent = 'Recording microphone... speak now';
    try {
      const res = await fetch('/api/stt/listen', { method: 'POST' });
      const data = await res.json();
      if (data.status === 'ok' && data.text && data.text.trim()) {
        const heard = data.text.trim();
        if (voiceTranscriptPreview) voiceTranscriptPreview.textContent = `"${heard}"`;
        if (chatInput) chatInput.value = heard;
        synth.playBlip(1046.50);
        setTimeout(() => {
          stopVoiceListening();
          sendMessage();
        }, 350);
      } else {
        if (voiceTranscriptPreview) voiceTranscriptPreview.textContent = data.message || "Didn't catch that. Click mic to speak.";
        setTimeout(() => stopVoiceListening(), 1800);
      }
    } catch (e) {
      if (voiceTranscriptPreview) voiceTranscriptPreview.textContent = "Mic listener offline. Click mic to retry.";
      setTimeout(() => stopVoiceListening(), 1800);
    }
  }

  function stopVoiceListening() {
    isListeningVoice = false;
    if (speechRecognitionInstance) {
      try { speechRecognitionInstance.stop(); } catch (e) {}
      speechRecognitionInstance = null;
    }
    if (btnVoice) btnVoice.classList.remove('listening');
    if (voiceListeningBar) voiceListeningBar.style.display = 'none';
    if (currentEmotion === 'listening') {
      setEmotion('neutral', false);
    }
  }

  if (btnVoice) {
    btnVoice.addEventListener('click', (e) => {
      e.preventDefault();
      toggleVoiceListening();
    });
  }

  if (avatarCard) {
    avatarCard.addEventListener('click', (e) => {
      e.preventDefault();
      toggleVoiceListening();
    });
  }

  if (dexterBgAvatar) {
    dexterBgAvatar.addEventListener('click', (e) => {
      e.preventDefault();
      toggleVoiceListening();
    });
  }


  // ── Fluid Navigation & Drawer Panels ───────────────────────────

  function openDrawer(viewName) {
    if (viewName !== 'chat' && currentView === viewName && hudDrawerOverlay && hudDrawerOverlay.classList.contains('open')) {
      closeDrawer();
      return;
    }
    currentView = viewName;

    // Update bottom tabs
    $$('.nav-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.view === viewName);
    });

    if (viewName === 'chat') {
      if (hudDrawerOverlay) hudDrawerOverlay.classList.remove('open');
      $$('.drawer-panel').forEach(d => d.classList.remove('active'));
      if (viewTitle) viewTitle.textContent = 'DEXTER ONLINE';
      return;
    }

    // Open overlay and activate specific drawer panel
    if (hudDrawerOverlay) hudDrawerOverlay.classList.add('open');
    $$('.drawer-panel').forEach(d => {
      d.classList.toggle('active', d.id === `view-${viewName}`);
    });

    if (viewName === 'tasks') {
      if (viewTitle) viewTitle.textContent = 'COGNITIVE TASK PIPELINE';
      loadTasks();
    } else if (viewName === 'memory') {
      if (viewTitle) viewTitle.textContent = 'PERSISTENT MEMORY MATRIX';
      loadMemory();
    } else if (viewName === 'tools') {
      if (viewTitle) viewTitle.textContent = 'CONNECTED CAPABILITIES & TOOLS';
      loadTools();
    } else if (viewName === 'settings') {
      if (viewTitle) viewTitle.textContent = 'SYSTEM CONFIGURATION & COMPANION';
      loadSettings();
    }
  }

  function closeDrawer() {
    openDrawer('chat');
  }

  $$('.nav-tab').forEach(tab => {
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


  // ── Scrollable Conversation Stream & Statement Rendering ────────

  let typewriterTimer = null;
  let hasConversationStarted = false;

  function renderStatementInStream(sender, text) {
    const clean = stripEmojis(text || '').trim();
    if (!clean) return;

    // Transition from centered initial statement to scrollable stream
    if (!hasConversationStarted) {
      hasConversationStarted = true;
      if (dialogueCenterpiece) dialogueCenterpiece.style.display = 'none';
      if (chatFeed) chatFeed.style.display = 'flex';
    }

    if (sender === 'You') {
      const userTurn = document.createElement('div');
      userTurn.className = 'msg-turn-user';
      userTurn.innerHTML = `
        <span class="user-badge">[ YOU ]</span>
        <div class="user-text">${formatMarkdown(clean)}</div>
      `;
      chatFeed.appendChild(userTurn);
      scrollToBottom();
      return;
    }

    // Assistant / Dexter turn
    $$('.msg-turn-dexter.latest-statement').forEach(el => {
      el.classList.remove('latest-statement');
      const cur = el.querySelector('.cursor-block');
      if (cur) cur.remove();
    });

    const botTurn = document.createElement('div');
    botTurn.className = 'msg-turn-dexter latest-statement';

    const badge = document.createElement('span');
    badge.className = 'dexter-badge';
    badge.textContent = `[ DEXTER // ${currentEmotion.toUpperCase()} ]`;
    botTurn.appendChild(badge);

    const body = document.createElement('div');
    body.className = 'dexter-text';
    botTurn.appendChild(body);

    const cursor = document.createElement('span');
    cursor.className = 'cursor-block';
    cursor.innerHTML = '&#9608;';
    botTurn.appendChild(cursor);

    chatFeed.appendChild(botTurn);
    scrollToBottom();

    if (typewriterTimer) clearInterval(typewriterTimer);
    let i = 0;
    const step = clean.length > 200 ? 4 : (clean.length > 80 ? 2 : 1);
    const speed = clean.length > 200 ? 8 : (clean.length > 80 ? 14 : 20);

    typewriterTimer = setInterval(() => {
      if (i >= clean.length) {
        clearInterval(typewriterTimer);
        typewriterTimer = null;
        body.innerHTML = formatMarkdown(clean);
        return;
      }
      body.textContent += clean.slice(i, i + step);
      i += step;
      if (i % (step * 8) === 0) {
        synth.playBlip();
      }
      scrollToBottom();
    }, speed);
  }

  function appendThinking() {
    removeThinking();
    if (!hasConversationStarted) {
      hasConversationStarted = true;
      if (dialogueCenterpiece) dialogueCenterpiece.style.display = 'none';
      if (chatFeed) chatFeed.style.display = 'flex';
    }

    const el = document.createElement('div');
    el.className = 'msg-turn-dexter thinking';
    el.id = 'active-thinking-bubble';

    const body = document.createElement('div');
    body.className = 'dexter-text';
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
      if (conversationScrollArea) {
        conversationScrollArea.scrollTop = conversationScrollArea.scrollHeight;
      }
    });
  }

  // Textarea auto-resize
  if (chatInput) {
    chatInput.addEventListener('input', () => {
      chatInput.style.height = 'auto';
      chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
    });
  }


  // ── Send Message ───────────────────────────────────────────────

  function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    renderStatementInStream('You', text);
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
        renderStatementInStream('Dexter', 'Connection interrupted. Recalibrating neural core.');
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
      }
      chatFeed.style.display = 'none';
      hasConversationStarted = false;
      if (dialogueCenterpiece) {
        dialogueCenterpiece.style.display = 'flex';
      }
      if (statementText) {
        statementText.textContent = 'Ready when you are.';
      }
      if (userInquiryTrace) {
        userInquiryTrace.style.display = 'none';
      }
      if (inquiryText) {
        inquiryText.textContent = '';
      }
      setEmotion('neutral', false);
      fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: '/clear' })
      }).catch(() => {});
    });
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
      renderStatementInStream('Dexter', text);
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

      if (topic === 'agent.glitch') {
        triggerScreenGlitch();
        setEmotion('skeptical', true, true);
      }

      if (topic === 'agent.started') {
        const userMsg = (data.user_message || '').trim();
        if (userMsg) {
          if (userInquiryTrace && inquiryText) {
            inquiryText.textContent = userMsg;
            userInquiryTrace.style.display = 'flex';
          }
          // Check if message is already in feed to prevent duplicate when sent from this web UI
          const allTurns = chatFeed ? chatFeed.querySelectorAll('.msg-turn-user') : [];
          const lastTurn = allTurns.length ? allTurns[allTurns.length - 1] : null;
          const lastText = lastTurn ? lastTurn.textContent : '';
          if (!lastText.includes(userMsg)) {
            renderStatementInStream('You', userMsg);
          }
        }
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
        if (data.content) {
          const botText = stripEmojis(data.content.trim());
          const assistantTurns = chatFeed ? chatFeed.querySelectorAll('.msg-turn-dexter') : [];
          const lastAssistant = assistantTurns.length ? assistantTurns[assistantTurns.length - 1] : null;
          const lastText = lastAssistant ? lastAssistant.textContent : '';
          if (!lastText.includes(botText)) {
            renderStatementInStream('Dexter', botText);
            synth.playSpeechStream(6);
          }
        }
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
      tasksContainer.innerHTML = '<div class="tasks-empty">No active tasks. Dextex logs multi-step operations here.</div>';
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
        if (selectClickAction && data.companion_options.click_action) {
          selectClickAction.value = data.companion_options.click_action;
        }
        if (selectDialogTheme && data.companion_options.dialog_theme) {
          selectDialogTheme.value = data.companion_options.dialog_theme;
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

  if (selectClickAction) {
    selectClickAction.addEventListener('change', async () => {
      const actionVal = selectClickAction.value;
      try {
        await fetch('/api/mascot/options', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ click_action: actionVal })
        });
      } catch (e) {}
    });
  }

  if (selectDialogTheme) {
    selectDialogTheme.addEventListener('change', async () => {
      const themeVal = selectDialogTheme.value;
      try {
        await fetch('/api/mascot/options', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ dialog_theme: themeVal })
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
    permDesc.textContent = data.description || 'Dextex requests authorization for an external computer action.';
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


  // ── Cellular Automata Background Canvas ─────────────────────────

  function initParticleCanvas() {
    const canvas = document.getElementById('particle-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const cellSize = 10; // Pixel size for each discrete cell
    const cellGap = 1;   // Gap between grid cells
    let cols = 0;
    let rows = 0;
    let grid = null;     // 1D array of cell states: 1 = alive, 0 = dead
    let alphaGrid = null;// Smooth fade alphas (0.0 to 1.0)

    function seedGrid() {
      const total = cols * rows;
      grid = new Uint8Array(total);
      alphaGrid = new Float32Array(total);
      // Seed ~7% of cells randomly to start a calm living simulation
      for (let i = 0; i < total; i++) {
        if (Math.random() < 0.07) {
          grid[i] = 1;
          alphaGrid[i] = Math.random() * 0.6 + 0.4;
        }
      }
      // Add Conway gliders or small oscillator seeds
      spawnSeedPattern(Math.floor(cols / 4), Math.floor(rows / 4));
      spawnSeedPattern(Math.floor((cols * 3) / 4), Math.floor((rows * 3) / 4));
    }

    function spawnSeedPattern(cx, cy) {
      if (!grid || cols === 0 || rows === 0) return;
      const patterns = [
        // Glider
        [[0,1],[1,2],[2,0],[2,1],[2,2]],
        // Blinker / small cluster
        [[0,0],[0,1],[0,2],[1,1],[1,2]],
        // Beacon
        [[0,0],[0,1],[1,0],[2,3],[3,2],[3,3]],
        // Toad
        [[1,1],[1,2],[1,3],[2,0],[2,1],[2,2]]
      ];
      const p = patterns[Math.floor(Math.random() * patterns.length)];
      for (const [dx, dy] of p) {
        const x = (cx + dx + cols) % cols;
        const y = (cy + dy + rows) % rows;
        const idx = y * cols + x;
        grid[idx] = 1;
        alphaGrid[idx] = 1.0;
      }
    }

    function resize() {
      const parent = canvas.parentElement || document.body;
      const w = parent.clientWidth || window.innerWidth;
      const h = parent.clientHeight || window.innerHeight;
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
        const newCols = Math.max(10, Math.floor(w / cellSize));
        const newRows = Math.max(10, Math.floor(h / cellSize));
        if (newCols !== cols || newRows !== rows) {
          cols = newCols;
          rows = newRows;
          seedGrid();
        }
      }
    }
    resize();

    if (window.ResizeObserver && canvas.parentElement) {
      const ro = new ResizeObserver(() => resize());
      ro.observe(canvas.parentElement);
    } else {
      window.addEventListener('resize', resize);
    }

    function getAccentRgb() {
      const emo = currentEmotion || 'neutral';
      const map = {
        happy: '255, 107, 0',
        thinking: '245, 158, 11',
        curious: '0, 240, 255',
        excited: '255, 85, 0',
        eureka: '250, 204, 21',
        confused: '234, 179, 8',
        concerned: '239, 68, 68',
        listening: '16, 185, 129',
        searching: '6, 182, 212',
        skeptical: '251, 146, 60'
      };
      return map[emo] || '56, 189, 248';
    }

    // Step cellular automata generation (Conway B3/S23)
    let lastStepTime = 0;
    const stepInterval = 160; // ~6 updates per second for smooth, contemplative life
    let generationCount = 0;

    function stepAutomata() {
      if (!grid || cols === 0 || rows === 0) return;
      const nextGrid = new Uint8Array(cols * rows);
      let liveCount = 0;

      for (let r = 0; r < rows; r++) {
        const rTop = (r - 1 + rows) % rows;
        const rBot = (r + 1) % rows;
        const rOffset = r * cols;
        const topOffset = rTop * cols;
        const botOffset = rBot * cols;

        for (let c = 0; c < cols; c++) {
          const cLeft = (c - 1 + cols) % cols;
          const cRight = (c + 1) % cols;

          // Count 8 neighbors
          const neighbors =
            grid[topOffset + cLeft] +
            grid[topOffset + c] +
            grid[topOffset + cRight] +
            grid[rOffset + cLeft] +
            grid[rOffset + cRight] +
            grid[botOffset + cLeft] +
            grid[botOffset + c] +
            grid[botOffset + cRight];

          const current = grid[rOffset + c];
          let next = 0;
          if (current === 1) {
            next = (neighbors === 2 || neighbors === 3) ? 1 : 0;
          } else {
            next = (neighbors === 3) ? 1 : 0;
          }
          nextGrid[rOffset + c] = next;
          if (next === 1) liveCount++;
        }
      }

      grid = nextGrid;
      generationCount++;

      // Reseed if population drops too low or every 120 generations
      if (liveCount < (cols * rows * 0.02) || generationCount % 120 === 0) {
        const rx = Math.floor(Math.random() * (cols - 4));
        const ry = Math.floor(Math.random() * (rows - 4));
        spawnSeedPattern(rx, ry);
      }
    }

    // Main render loop with smooth interpolation
    let lastFrameTime = performance.now();

    function render(now) {
      const dt = Math.min(60, now - lastFrameTime);
      lastFrameTime = now;

      // Update simulation step
      if (now - lastStepTime > stepInterval) {
        stepAutomata();
        lastStepTime = now;
      }

      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);
      const rgb = getAccentRgb();

      if (!grid || cols === 0 || rows === 0) {
        requestAnimationFrame(render);
        return;
      }

      // Smooth fade transition for alphas
      const fadeSpeed = 0.06;
      const baseMaxAlpha = 0.18; // Soft, subtle, non-distracting presence

      for (let r = 0; r < rows; r++) {
        const rOffset = r * cols;
        const y = r * cellSize;
        for (let c = 0; c < cols; c++) {
          const idx = rOffset + c;
          const target = grid[idx] ? 1.0 : 0.0;
          let a = alphaGrid[idx];

          if (a < target) {
            a = Math.min(target, a + fadeSpeed * 1.5);
          } else if (a > target) {
            a = Math.max(0.0, a - fadeSpeed * 0.6);
          }
          alphaGrid[idx] = a;

          if (a > 0.015) {
            const x = c * cellSize;
            const drawAlpha = a * baseMaxAlpha;
            ctx.fillStyle = `rgba(${rgb}, ${drawAlpha.toFixed(3)})`;
            // Clean pixel-style discrete square cell
            ctx.fillRect(x + cellGap, y + cellGap, cellSize - cellGap * 2, cellSize - cellGap * 2);
          }
        }
      }

      requestAnimationFrame(render);
    }

    requestAnimationFrame(render);
  }


  // ── Multi-Conversation Thread Manager ─────────────────────────

  const STORAGE_KEY_CHATS = 'dexter_chats_v2';
  let conversations = [];
  let activeChatId = null;

  function loadConversations() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY_CHATS);
      if (raw) {
        conversations = JSON.parse(raw);
      }
    } catch (e) {
      conversations = [];
    }

    if (!conversations.length) {
      const now = Date.now();
      conversations = [
        { id: 'chat-1', title: 'Untitled Chat', updated_at: now - 2 * 60 * 1000, turns: [] },
        { id: 'chat-2', title: 'Project Ideas', updated_at: now - 60 * 60 * 1000, turns: [] },
        { id: 'chat-3', title: 'Code Review', updated_at: now - 3 * 60 * 60 * 1000, turns: [] },
        { id: 'chat-4', title: 'Random Thoughts', updated_at: now - 24 * 60 * 60 * 1000, turns: [] },
        { id: 'chat-5', title: 'Web App Setup', updated_at: now - 48 * 60 * 60 * 1000, turns: [] }
      ];
      saveConversations();
    }

    activeChatId = conversations[0].id;
    renderSidebarRecentChats();
    updateActiveChatDisplay();
  }

  function saveConversations() {
    try {
      localStorage.setItem(STORAGE_KEY_CHATS, JSON.stringify(conversations));
    } catch (e) {}
  }

  function getTimeAgoLabel(timestamp) {
    const diffMs = Date.now() - timestamp;
    const mins = Math.floor(diffMs / 60000);
    if (mins < 60) return `${Math.max(1, mins)}m`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h`;
    const days = Math.floor(hours / 24);
    return `${days}d`;
  }

  function renderSidebarRecentChats() {
    const container = document.getElementById('recent-chats-list');
    const badge = document.getElementById('chats-count-badge');
    if (badge) badge.textContent = conversations.length;
    if (!container) return;

    container.innerHTML = '';
    conversations.forEach((chat) => {
      const item = document.createElement('div');
      item.className = `chat-item ${chat.id === activeChatId ? 'active' : ''}`;
      item.innerHTML = `
        <span class="chat-item-dot"></span>
        <span class="chat-item-title">${chat.title}</span>
        <span class="chat-item-time">${getTimeAgoLabel(chat.updated_at)}</span>
      `;
      item.addEventListener('click', () => switchConversation(chat.id));
      container.appendChild(item);
    });
  }

  function updateActiveChatDisplay() {
    const activeChat = conversations.find(c => c.id === activeChatId);
    const titleEl = document.getElementById('active-chat-title');
    if (titleEl && activeChat) {
      titleEl.textContent = activeChat.title;
    }
  }

  function createNewConversation() {
    const newId = 'chat-' + Date.now();
    const newChat = {
      id: newId,
      title: 'Untitled Chat',
      updated_at: Date.now(),
      turns: []
    };
    conversations.unshift(newChat);
    activeChatId = newId;
    saveConversations();
    renderSidebarRecentChats();
    updateActiveChatDisplay();
    clearStreamCanvas();
  }

  function switchConversation(id) {
    const chat = conversations.find(c => c.id === id);
    if (!chat) return;
    activeChatId = id;
    renderSidebarRecentChats();
    updateActiveChatDisplay();
    clearStreamCanvas();

    if (chat.turns && chat.turns.length) {
      chat.turns.forEach(turn => {
        renderStatementInStream(turn.sender, turn.text, false);
      });
    }
  }

  function clearStreamCanvas() {
    if (chatFeed) {
      chatFeed.innerHTML = '<div id="chat-empty"></div>';
      chatFeed.style.display = 'none';
    }
    if (dialogueCenterpiece) {
      dialogueCenterpiece.style.display = 'flex';
    }
    hasConversationStarted = false;
  }

  const activeTitleEl = document.getElementById('active-chat-title');
  if (activeTitleEl) {
    activeTitleEl.addEventListener('blur', () => {
      const newTitle = activeTitleEl.textContent.trim() || 'Untitled Chat';
      const chat = conversations.find(c => c.id === activeChatId);
      if (chat) {
        chat.title = newTitle;
        saveConversations();
        renderSidebarRecentChats();
      }
    });

    activeTitleEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        activeTitleEl.blur();
      }
    });
  }

  const btnNewChat = document.getElementById('btn-new-chat');
  if (btnNewChat) {
    btnNewChat.addEventListener('click', createNewConversation);
  }


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
            if (selectDialogTheme && data.companion_options.dialog_theme) {
              selectDialogTheme.value = data.companion_options.dialog_theme;
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
    if (typeof initVoice === 'function') initVoice();
    initWebSocket();
    initParticleCanvas();
    loadConversations();

    // Sidebar collapse toggle
    const btnToggleSidebar = document.getElementById('btn-toggle-sidebar');
    const appSidebar = document.getElementById('app-sidebar');
    if (btnToggleSidebar && appSidebar) {
      btnToggleSidebar.addEventListener('click', () => {
        appSidebar.classList.toggle('sidebar-collapsed');
        // Update CSS variable for drawer overlay positioning
        const isCollapsed = appSidebar.classList.contains('sidebar-collapsed');
        document.documentElement.style.setProperty('--sidebar-w', isCollapsed ? '58px' : '240px');
      });
    }
  }

  init();

})();
