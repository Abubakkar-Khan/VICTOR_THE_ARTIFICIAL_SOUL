"""Dextex Desktop Companion — Embodiment of Dextex Laboratory / The Artificial Soul.

Features:
- Seamless desktop presence: auto-hides when Dextex Lab is in focus, auto-appears when minimized
- Animated circular/pill speech bubble with Dexter's Lab accent borders
- Click-to-listen: microphone capture via sounddevice + speech_recognition (zero typing box)
- Real-time 1:1 emotional synchronization with Dextex Lab
- Zero emojis across all UI, menus, and feedback
- Procedural Celeste-style melodic chimes
"""

import io
import json
import math
import os
from pathlib import Path
import random
import sys
import threading
import time
import tkinter as tk
from urllib import request as url_request
import webbrowser

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

try:
    import sounddevice as sd
    from scipy.io import wavfile
    import speech_recognition as sr
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False


# ── 12 Dexter Soul Emotions (Zero Emojis) ──────────────────────────

EMOTIONS = {
    "neutral":   {"label": "Neutral",   "desc": "Standing by. Calm and level-headed."},
    "happy":     {"label": "Happy",     "desc": "Optimal resonance. Systems running cleanly."},
    "curious":   {"label": "Curious",   "desc": "Observing closely. Exploring telemetry."},
    "idle":      {"label": "Idle",      "desc": "Deep standby. Drifting quietly."},
    "bored":     {"label": "Bored",     "desc": "Waiting patiently for something."},
    "thinking":  {"label": "Thinking",  "desc": "Synthesizing reasoning vectors."},
    "searching": {"label": "Searching", "desc": "Looking through information and files."},
    "excited":   {"label": "Excited",   "desc": "Fascinating discovery! High neural resonance."},
    "eureka":    {"label": "Eureka",    "desc": "Figured something out!"},
    "confused":  {"label": "Confused",  "desc": "Ambiguous vector. Clarification required."},
    "concerned": {"label": "Concerned", "desc": "Anomaly detected. Proceeding with caution."},
    "listening": {"label": "Listening", "desc": "Receiving your voice or input."},
    "skeptical": {"label": "Skeptical", "desc": "Double-checking parameters carefully."},
}

EMOTION_ACCENTS = {
    "neutral":   "#00F0FF",
    "happy":     "#10B981",
    "curious":   "#FF8A00",
    "idle":      "#64748B",
    "bored":     "#71717A",
    "thinking":  "#00D9FF",
    "searching": "#38BDF8",
    "excited":   "#FF6B00",
    "eureka":    "#FACC15",
    "confused":  "#A855F7",
    "concerned": "#EF4444",
    "listening": "#00FF88",
    "skeptical": "#FB923C",
}

CELESTE_PENTATONIC = [1046.50, 1174.66, 1318.51, 1567.98, 1760.00, 2093.00]  # C6, D6, E6, G6, A6, C7 (Sweet crystal notes)

DIALOG_THEMES = {
    "laboratory": {
        "name": "Laboratory Cyan (Default)",
        "fill": "#0B0E14",
        "outline": "accent",
        "text": "#F0EDE8",
        "font_family": "Segoe UI",
        "radius": 8,
        "width": 1.5,
    },
    "amber_crt": {
        "name": "Amber CRT Terminal",
        "fill": "#140F07",
        "outline": "#F59E0B",
        "text": "#FDE68A",
        "font_family": "Consolas",
        "radius": 4,
        "width": 1.5,
    },
    "matrix_green": {
        "name": "Matrix Phosphor",
        "fill": "#051208",
        "outline": "#10B981",
        "text": "#6EE7B7",
        "font_family": "Consolas",
        "radius": 4,
        "width": 1.5,
    },
    "sharp_tech": {
        "name": "Sharp Box Tech (Pure Rect)",
        "fill": "#08090D",
        "outline": "accent",
        "text": "#FFFFFF",
        "font_family": "Segoe UI",
        "radius": 0,
        "width": 1.5,
    },
    "stealth_dark": {
        "name": "Stealth Charcoal",
        "fill": "#111318",
        "outline": "#334155",
        "text": "#E2E8F0",
        "font_family": "Segoe UI",
        "radius": 6,
        "width": 1.0,
    },
    "celeste_sky": {
        "name": "Celeste Mountain",
        "fill": "#15162B",
        "outline": "#38BDF8",
        "text": "#F0F9FF",
        "font_family": "Segoe UI",
        "radius": 10,
        "width": 1.5,
    },
}


def get_server_base() -> str:
    """Resolve backend API base URL using dynamic port if specified."""
    port = os.environ.get("VICTOR_PORT", "8000")
    return f"http://127.0.0.1:{port}"


def play_celeste_chime(notes: int = 2, interval: float = 0.05):
    """Play a soft, dreamy Celeste-style crystal music-box chime."""
    if not HAS_AUDIO:
        return

    def _play():
        try:
            import numpy as np
            import sounddevice as sd
            fs = 44100
            chunks = []
            chosen = random.sample(CELESTE_PENTATONIC, min(notes, len(CELESTE_PENTATONIC)))
            chosen.sort()  # Ascending chime sounds sweeter
            for freq in chosen:
                dur = 0.072
                t = np.linspace(0, dur, int(fs * dur), endpoint=False)
                attack = int(fs * 0.002)
                env = np.exp(-t * 28.0)
                env[:attack] *= np.linspace(0, 1, attack)
                # Pure sine with delicate harmonic sparkle
                wave = np.sin(2 * np.pi * freq * t) + 0.12 * np.sin(2 * np.pi * (freq * 2) * t) + 0.03 * np.sin(2 * np.pi * (freq * 3) * t)
                chime = (wave * env * 0.035).astype(np.float32)
                pause = np.zeros(int(fs * interval), dtype=np.float32)
                chunks.extend([chime, pause])
            full = np.concatenate(chunks)
            sd.play(full, samplerate=fs)
            sd.wait()
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()


class MascotWindow:
    """Transparent, floating desktop companion embodying Victor's 8 emotional states."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Victor")

        # Window geometry & appearance
        self.width = 280
        self.height = 275
        self.bg_color = "#010101"  # Chroma key for Windows transparency

        # Position at bottom-right of screen
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        start_x = max(20, screen_w - self.width - 40)
        start_y = max(20, screen_h - self.height - 80)
        self.root.geometry(f"{self.width}x{self.height}+{start_x}+{start_y}")

        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.configure(bg=self.bg_color)
        if sys.platform == "win32":
            self.root.wm_attributes("-transparentcolor", self.bg_color)

        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg=self.bg_color,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        # State
        self.emotion = "neutral"
        self.speech_text = ""
        self.speech_expires = 0
        self.anim_tick = 0
        self.drag_x = 0
        self.drag_y = 0
        self._dragging = False
        self.sound_enabled = True
        self.is_listening = False
        self.click_action = "listen"
        self.dialog_theme = "laboratory"
        self._is_hidden = False
        self.auto_hide_enabled = True
        self.last_seen_chat_time = time.time()

        # Sprite cache
        self.sprites = {}
        self._load_sprites()
        if self.sprites.get("neutral"):
            try:
                self.root.iconphoto(True, self.sprites["neutral"])
            except Exception:
                pass

        # Event bindings
        self.canvas.bind("<Button-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._end_drag)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<Button-3>", self._show_context_menu)

        # Context Menu
        self._setup_context_menu()

        # Telemetry & Polling Thread
        self.ws_running = True
        self.telemetry_thread = threading.Thread(target=self._ws_telemetry, daemon=True)
        self.telemetry_thread.start()

        # Start animation loop
        self._animate()

    def _load_sprites(self):
        """Load and resize the 8 emotion sprites."""
        if not HAS_PIL:
            return

        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            base_dir = Path(sys._MEIPASS) / "victor"
        else:
            base_dir = Path(__file__).resolve().parent.parent
        sprite_dir = base_dir / "sprite"
        target_w = 170
        target_h = 155

        for emo in EMOTIONS.keys():
            path = sprite_dir / f"{emo}.png"
            if not path.exists():
                path = sprite_dir / f"{emo}_240.png"

            if path.exists():
                try:
                    img = Image.open(path).convert("RGBA")
                    resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    self.sprites[emo] = ImageTk.PhotoImage(resized)
                except Exception as e:
                    print(f"Error loading sprite for {emo}: {e}")

    def _setup_context_menu(self):
        self.menu = tk.Menu(
            self.root,
            tearoff=0,
            bg="#0E1118",
            fg="#F8FAFC",
            activebackground="#1E2433",
            activeforeground="#00F0FF",
            font=("Segoe UI", 9),
            relief="flat",
            bd=1,
        )
        self.menu.add_command(label="Listen (Microphone)", command=self._start_voice_listening)
        self.menu.add_command(label="Open Dextex Lab", command=self._open_workshop)
        self.menu.add_separator()

        # Click Action Submenu
        action_menu = tk.Menu(
            self.menu,
            tearoff=0,
            bg="#0E1118",
            fg="#F8FAFC",
            activebackground="#1E2433",
            activeforeground="#00F0FF",
            font=("Segoe UI", 9),
            relief="flat",
        )
        action_menu.add_command(
            label="[•] Listen on Click" if self.click_action == "listen" else "    Listen on Click",
            command=lambda: self._set_click_action("listen")
        )
        action_menu.add_command(
            label="[•] Poke on Click" if self.click_action == "poke" else "    Poke on Click",
            command=lambda: self._set_click_action("poke")
        )
        action_menu.add_command(
            label="[•] Open Lab on Click" if self.click_action == "open" else "    Open Lab on Click",
            command=lambda: self._set_click_action("open")
        )
        self.menu.add_cascade(label=f"Click Action: {self.click_action.upper()}", menu=action_menu)

        # Dialog Theme Submenu
        theme_menu = tk.Menu(
            self.menu,
            tearoff=0,
            bg="#0E1118",
            fg="#F8FAFC",
            activebackground="#1E2433",
            activeforeground="#00F0FF",
            font=("Segoe UI", 9),
            relief="flat",
        )
        for tkey, tinfo in DIALOG_THEMES.items():
            theme_menu.add_command(
                label=f"[•] {tinfo['name']}" if self.dialog_theme == tkey else f"    {tinfo['name']}",
                command=lambda k=tkey: self._set_dialog_theme(k),
            )
        current_theme_name = DIALOG_THEMES.get(self.dialog_theme, {}).get("name", "Default")
        self.menu.add_cascade(label=f"Dialog Theme: {current_theme_name}", menu=theme_menu)

        # Emotions Submenu (Strictly zero emojis)
        emo_menu = tk.Menu(
            self.menu,
            tearoff=0,
            bg="#0E1118",
            fg="#F8FAFC",
            activebackground="#1E2433",
            activeforeground="#00F0FF",
            font=("Segoe UI", 9),
            relief="flat",
        )
        for key, info in EMOTIONS.items():
            emo_menu.add_command(
                label=f"[{info['label'].upper()}] — {info['desc']}",
                command=lambda k=key: self.set_emotion(k, f"Reflecting {k}"),
            )
        self.menu.add_cascade(label="Emotions", menu=emo_menu)
        self.menu.add_separator()
        self.menu.add_command(
            label="Mute Sounds" if self.sound_enabled else "Enable Sounds",
            command=self._toggle_sound,
        )
        self.menu.add_command(
            label="Auto-Hide When Lab Active: " + ("ON" if self.auto_hide_enabled else "OFF"),
            command=self._toggle_auto_hide,
        )
        self.menu.add_command(label="Sleep / Standby", command=lambda: self.set_emotion("idle", "Standby mode."))
        self.menu.add_command(label="Quit Dextex", command=self.root.destroy)

    def _set_click_action(self, action: str):
        self.click_action = action
        self.show_speech(f"Click action set to {action}.")
        self._setup_context_menu()
        def _post():
            try:
                data = json.dumps({"click_action": action}).encode("utf-8")
                req = url_request.Request(
                    f"{get_server_base()}/api/mascot/options",
                    data=data,
                    headers={"Content-Type": "application/json"}
                )
                url_request.urlopen(req, timeout=2)
            except Exception:
                pass
        threading.Thread(target=_post, daemon=True).start()

    def _set_dialog_theme(self, theme_key: str):
        if theme_key in DIALOG_THEMES:
            self.dialog_theme = theme_key
            self.show_speech(f"Theme applied: {DIALOG_THEMES[theme_key]['name']}.")
            self._setup_context_menu()
            def _post():
                try:
                    data = json.dumps({"dialog_theme": theme_key}).encode("utf-8")
                    req = url_request.Request(
                        f"{get_server_base()}/api/mascot/options",
                        data=data,
                        headers={"Content-Type": "application/json"}
                    )
                    url_request.urlopen(req, timeout=2)
                except Exception:
                    pass
            threading.Thread(target=_post, daemon=True).start()

    def _toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        self.show_speech("Sounds muted." if not self.sound_enabled else "Sounds enabled.")
        self._setup_context_menu()

    def _toggle_auto_hide(self):
        self.auto_hide_enabled = not self.auto_hide_enabled
        self.show_speech(f"Auto-hide is now {'ON' if self.auto_hide_enabled else 'OFF'}.")
        self._setup_context_menu()

    def set_emotion(self, emotion: str, speech: str = ""):
        """Change Victor's emotional state and optionally show speech."""
        if emotion in EMOTIONS:
            self.emotion = emotion
        if speech:
            self.show_speech(speech)
        elif emotion == "thinking":
            if self.sound_enabled:
                play_celeste_chime(notes=2, interval=0.08)

    def show_speech(self, text: str, duration: float = 0):
        """Display a smooth rectangular speech bubble above Dexter's portrait."""
        self.speech_text = text[:150] + ("..." if len(text) > 150 else "")
        if duration <= 0:
            duration = max(3.8, min(8.5, len(self.speech_text) * 0.05 + 2.5))
        self.speech_expires = time.time() + duration
        if self.sound_enabled:
            play_celeste_chime(notes=3, interval=0.04)

    def _start_voice_listening(self):
        """Click-to-listen: local microphone speech-to-text with AGC and Celeste chime."""
        if self.is_listening:
            return

        self.is_listening = True
        self.set_emotion("listening", "Listening... Speak now.")
        if self.sound_enabled:
            play_celeste_chime(notes=2, interval=0.06)

        def _worker():
            try:
                if not HAS_AUDIO:
                    self.root.after(0, lambda: self._on_listening_failed("Audio device unavailable."))
                    return

                dev = sd.query_devices(kind="input")
                fs = int(dev.get("default_samplerate", 44100))
                duration = 4.0
                recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype="int16")
                sd.wait()

                import numpy as np
                peak = int(np.max(np.abs(recording)))
                if peak < 25:
                    self.root.after(0, lambda: self._on_listening_failed("Didn't catch that. Click me to speak again."))
                    return

                # Automatic Gain Control for soft speech
                gain = min(12.0, 16000.0 / max(1.0, float(peak)))
                norm_rec = np.clip(recording.astype(np.float32) * gain, -32767, 32767).astype(np.int16)

                wav_io = io.BytesIO()
                wavfile.write(wav_io, fs, norm_rec)
                wav_io.seek(0)

                recognizer = sr.Recognizer()
                recognizer.energy_threshold = 300
                recognizer.dynamic_energy_threshold = True
                with sr.AudioFile(wav_io) as source:
                    audio = recognizer.record(source)
                    try:
                        text = recognizer.recognize_google(audio)
                    except sr.UnknownValueError:
                        text = None
                    except sr.RequestError:
                        self.root.after(0, lambda: self._on_listening_failed("Speech service offline."))
                        return

                if text and text.strip():
                    self.root.after(0, lambda t=text: self._dispatch_chat(t))
                else:
                    self.root.after(0, lambda: self._on_listening_failed("Didn't catch that. Click me to speak again."))
            except Exception:
                self.root.after(0, lambda: self._on_listening_failed("Didn't catch that. Click me to speak again."))
            finally:
                self.is_listening = False

        threading.Thread(target=_worker, daemon=True).start()

    def _on_listening_failed(self, msg: str):
        """Show clean listening status without any random poke fallback."""
        self.is_listening = False
        self.show_speech(msg, duration=3.5)
        self.set_emotion("neutral")

    def _on_poke(self):
        """Explicit poke action when configured in settings."""
        def _poke():
            try:
                req = url_request.Request(
                    f"{get_server_base()}/api/poke",
                    data=b"{}",
                    headers={"Content-Type": "application/json"},
                )
                with url_request.urlopen(req, timeout=2) as res:
                    data = json.loads(res.read().decode("utf-8"))
                    emo = data.get("emotion", self.emotion)
                    msg = data.get("message", "Standing by.")
                    self.root.after(0, lambda e=emo, m=msg: self.set_emotion(e, m))
            except Exception:
                if self.emotion == "idle":
                    self.root.after(0, lambda: self.set_emotion("neutral", "Awake. Systems active."))
                else:
                    self.root.after(0, lambda: self.show_speech("Standing by."))
        threading.Thread(target=_poke, daemon=True).start()

    def _dispatch_chat(self, text: str):
        """Send recognized voice prompt to Dextex backend."""
        self.set_emotion("thinking", f'"{text[:35]}..."')
        self.last_seen_chat_time = time.time() + 3.0
        def _send():
            try:
                data = json.dumps({"message": text}).encode("utf-8")
                req = url_request.Request(
                    f"{get_server_base()}/api/chat",
                    data=data,
                    headers={"Content-Type": "application/json"},
                )
                with url_request.urlopen(req, timeout=25) as res:
                    body = json.loads(res.read().decode("utf-8"))
                    content = body.get("content", "")
                    emo = body.get("emotion", "neutral")
                    self.last_seen_chat_time = time.time() + 1.0
                    self.root.after(0, lambda e=emo, m=content: self.set_emotion(e, m))
                    if self.sound_enabled:
                        play_celeste_chime(notes=4, interval=0.06)
            except Exception as ex:
                self.root.after(0, lambda: self.set_emotion("concerned", "Neural link error."))
        threading.Thread(target=_send, daemon=True).start()

    def _start_drag(self, event):
        self.drag_x = event.x
        self.drag_y = event.y
        self._dragging = False

    def _on_drag(self, event):
        self._dragging = True
        deltax = event.x - self.drag_x
        deltay = event.y - self.drag_y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def _end_drag(self, event):
        if not self._dragging:
            # Single click behavior
            if self.click_action == "listen":
                self._start_voice_listening()
            elif self.click_action == "poke":
                self._on_poke()
            elif self.click_action == "open":
                self._open_workshop()
        self._dragging = False

    def _on_right_click(self, event):
        self._show_context_menu(event)

    def _on_double_click(self, event):
        # Explicitly disabled: double-clicking does not trigger browser opening
        return "break"

    def _open_workshop(self):
        webbrowser.open(get_server_base())

    def _show_context_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

    def _ws_telemetry(self):
        """Polls server for emotion, telemetry, auto-hide, and real-time chat sync."""
        while self.ws_running:
            try:
                with url_request.urlopen(f"{get_server_base()}/api/status", timeout=2) as res:
                    data = json.loads(res.read().decode("utf-8"))
                    new_emo = data.get("emotion")
                    if new_emo and new_emo != self.emotion and not self.is_listening:
                        self.root.after(0, lambda e=new_emo: self.set_emotion(e))

                    # Real-time background sync from workshop chat
                    latest_chat = data.get("latest_chat")
                    if latest_chat and not self.is_listening:
                        chat_time = latest_chat.get("timestamp", 0)
                        if chat_time > self.last_seen_chat_time:
                            self.last_seen_chat_time = chat_time
                            bot_reply = latest_chat.get("assistant", "")
                            bot_emo = latest_chat.get("emotion", "neutral")
                            if bot_reply:
                                self.root.after(0, lambda e=bot_emo, m=bot_reply: self.set_emotion(e, m))
                                if self.sound_enabled:
                                    play_celeste_chime(notes=3, interval=0.06)

                    # Auto-Hide when Workshop is focused in front
                    workshop_focused = data.get("workshop_focused", False)
                    options = data.get("companion_options", {})
                    auto_hide = options.get("auto_hide", self.auto_hide_enabled)
                    if "click_action" in options:
                        self.click_action = options["click_action"]
                    if "dialog_theme" in options and options["dialog_theme"] in DIALOG_THEMES:
                        if self.dialog_theme != options["dialog_theme"]:
                            self.dialog_theme = options["dialog_theme"]
                            self.root.after(0, self._setup_context_menu)

                    if auto_hide and workshop_focused and not self._is_hidden:
                        self._is_hidden = True
                        self.root.after(0, self.root.withdraw)
                    elif (not workshop_focused or not auto_hide) and self._is_hidden:
                        self._is_hidden = False
                        self.root.after(0, self.root.deiconify)
            except Exception:
                pass
            time.sleep(1.2)

    def _get_accent_color(self) -> str:
        return EMOTION_ACCENTS.get(self.emotion, "#00F0FF")

    def _draw_rounded_rect(self, x1, y1, x2, y2, radius=8, fill="#0B0E14", outline="#00F0FF", width=1.5):
        """Draw a true crisp rectangle with smooth rounded corners (never an oval)."""
        if radius <= 0:
            return self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=width)
        r = min(radius, max(2, int((x2 - x1) // 3)), max(2, int((y2 - y1) // 3)))
        points = []
        # Top-left arc
        for a in range(180, 271, 15):
            rad = math.radians(a)
            points.extend([x1 + r + r * math.cos(rad), y1 + r + r * math.sin(rad)])
        # Top-right arc
        for a in range(270, 361, 15):
            rad = math.radians(a)
            points.extend([x2 - r + r * math.cos(rad), y1 + r + r * math.sin(rad)])
        # Bottom-right arc
        for a in range(0, 91, 15):
            rad = math.radians(a)
            points.extend([x2 - r + r * math.cos(rad), y2 - r + r * math.sin(rad)])
        # Bottom-left arc
        for a in range(90, 181, 15):
            rad = math.radians(a)
            points.extend([x1 + r + r * math.cos(rad), y2 - r + r * math.sin(rad)])
        return self.canvas.create_polygon(points, smooth=False, fill=fill, outline=outline, width=width)

    def _draw(self):
        self.canvas.delete("all")
        t = self.anim_tick
        cx = self.width // 2

        # Floating / breathing bob effect
        bob_offset = 0
        if self.emotion in ["idle", "neutral", "thinking"]:
            bob_offset = int(round(math.sin(t * 0.08) * 3))
        elif self.emotion in ["excited", "happy"]:
            bob_offset = int(round(abs(math.sin(t * 0.2)) * -5))
        elif self.emotion == "concerned":
            bob_offset = 2

        # Check speech bubble presence and compute dynamic rectangular dimensions
        bubble_active = bool(self.speech_text and time.time() < self.speech_expires)
        bubble_bottom = 0

        if bubble_active:
            theme_cfg = DIALOG_THEMES.get(self.dialog_theme, DIALOG_THEMES["laboratory"])
            accent = self._get_accent_color()
            outline_color = accent if theme_cfg["outline"] == "accent" else theme_cfg["outline"]
            fill_color = theme_cfg["fill"]
            text_color = theme_cfg["text"]
            font_family = theme_cfg.get("font_family", "Segoe UI")
            radius = theme_cfg.get("radius", 8)
            border_width = theme_cfg.get("width", 1.5)

            bubble_pulse = int(round(math.sin(t * 0.15) * 2))

            raw_text = self.speech_text.strip()
            char_count = len(raw_text)

            # Dynamically size crisp rounded rectangle to be as long as the text
            if char_count <= 20:
                box_w = max(110, min(240, char_count * 8 + 32))
                box_h = 32
                font_spec = (font_family, 9)
            elif char_count <= 50:
                box_w = min(265, max(150, int(char_count * 5.2) + 26))
                box_h = 42
                font_spec = (font_family, 8)
            elif char_count <= 95:
                box_w = min(270, max(210, int(char_count * 3.0) + 40))
                box_h = 56
                font_spec = (font_family, 8)
            else:
                box_w = 270
                box_h = min(84, 58 + ((char_count - 95) // 22) * 12)
                font_spec = (font_family, 8)

            bx1 = cx - box_w // 2
            bx2 = cx + box_w // 2
            by1 = max(4, 8 + bubble_pulse)
            by2 = by1 + box_h
            bubble_bottom = by2

            # Draw crisp rectangular bubble with theme styling
            self._draw_rounded_rect(
                bx1, by1, bx2, by2,
                radius=radius,
                fill=fill_color,
                outline=outline_color,
                width=border_width,
            )

            # Connector tail dots floating down to Dexter's head
            dot_y = by2 + 2
            self.canvas.create_oval(cx - 3, dot_y, cx + 3, dot_y + 5, fill=fill_color, outline=outline_color, width=1)
            self.canvas.create_oval(cx - 2, dot_y + 7, cx + 2, dot_y + 10, fill=outline_color, outline=outline_color)

            # Bubble text
            text_y = (by1 + by2) // 2
            self.canvas.create_text(
                cx,
                text_y,
                text=raw_text,
                width=box_w - 18,
                fill=text_color,
                font=font_spec,
                justify="center",
            )

        # Dynamic sprite placement below bubble
        if bubble_active:
            img_y = max(68, bubble_bottom + 10) + bob_offset
        else:
            img_y = 65 + bob_offset

        # Render active emotion sprite centered at cx
        sprite = self.sprites.get(self.emotion) or self.sprites.get("neutral")
        if sprite:
            self.canvas.create_image(cx, img_y + 72, image=sprite)
        else:
            accent = self._get_accent_color()
            self.canvas.create_oval(cx - 50, img_y, cx + 50, img_y + 100, fill="#121417", outline=accent, width=2)
            self.canvas.create_text(cx, img_y + 50, text=self.emotion.upper(), fill="#E6E6E6", font=("Segoe UI", 10, "bold"))

    def _animate(self):
        self.anim_tick += 1
        self._draw()
        self.root.after(40, self._animate)  # ~25 FPS animation loop

    def run(self):
        self.root.mainloop()


def launch_desktop_mascot():
    app = MascotWindow()
    app.run()


if __name__ == "__main__":
    launch_desktop_mascot()
