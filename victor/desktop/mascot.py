"""Victor Desktop Companion — Pixel-Art Embodiment of the Artificial Soul.

Features:
- Seamless desktop presence: auto-hides when Workshop is in focus, auto-appears when minimized
- Animated circular/pill speech bubble with emotional accent borders
- Click-to-listen: microphone capture via sounddevice + speech_recognition (zero typing box)
- Real-time 1:1 emotional synchronization with Workshop
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


# ── 8 Artificial Soul Emotions (Zero Emojis) ───────────────────────

EMOTIONS = {
    "neutral":   {"label": "Neutral",   "desc": "Standing by. Calm and level-headed."},
    "happy":     {"label": "Happy",     "desc": "Optimal resonance. Systems running cleanly."},
    "curious":   {"label": "Curious",   "desc": "Observing closely. Exploring telemetry."},
    "idle":      {"label": "Idle",      "desc": "Deep standby. Drifting quietly."},
    "thinking":  {"label": "Thinking",  "desc": "Synthesizing reasoning vectors."},
    "excited":   {"label": "Excited",   "desc": "Fascinating discovery! High neural resonance."},
    "confused":  {"label": "Confused",  "desc": "Ambiguous vector. Clarification required."},
    "concerned": {"label": "Concerned", "desc": "Anomaly detected. Proceeding with caution."},
}

EMOTION_ACCENTS = {
    "neutral":   "#D4A574",
    "happy":     "#10B981",
    "curious":   "#F59E0B",
    "thinking":  "#38BDF8",
    "excited":   "#FBBF24",
    "confused":  "#C084FC",
    "concerned": "#EF4444",
    "idle":      "#64748B",
}

PENTATONIC_SCALE = [523, 587, 659, 784, 880, 1046]  # C5, D5, E5, G5, A5, C6


def play_celeste_chime(notes: int = 3, interval: float = 0.05):
    """Play a short, melodic Celeste-style procedural electronic chime."""
    if not HAS_WINSOUND:
        return

    def _play():
        try:
            for _ in range(notes):
                freq = random.choice(PENTATONIC_SCALE)
                winsound.Beep(freq, 40)
                time.sleep(interval)
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()


class MascotWindow:
    """Transparent, floating desktop companion embodying Victor's 8 emotional states."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Victor")

        # Window geometry & appearance
        self.width = 240
        self.height = 250
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
        self._is_hidden = False
        self.auto_hide_enabled = True

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
        target_w = 200
        target_h = 145

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
            bg="#111215",
            fg="#E6E6E6",
            activebackground="#202226",
            activeforeground="#D4A574",
            font=("Segoe UI", 9),
            relief="flat",
            bd=1,
        )
        self.menu.add_command(label="Listen (Microphone)", command=self._start_voice_listening)
        self.menu.add_command(label="Open Workshop", command=self._open_workshop)
        self.menu.add_separator()

        # Emotions Submenu (Strictly zero emojis)
        emo_menu = tk.Menu(
            self.menu,
            tearoff=0,
            bg="#111215",
            fg="#E6E6E6",
            activebackground="#202226",
            activeforeground="#D4A574",
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
            label="Auto-Hide When Workshop Active: " + ("ON" if self.auto_hide_enabled else "OFF"),
            command=self._toggle_auto_hide,
        )
        self.menu.add_command(label="Sleep / Standby", command=lambda: self.set_emotion("idle", "Standby mode."))
        self.menu.add_command(label="Quit", command=self.root.destroy)

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

    def show_speech(self, text: str, duration: float = 4.2):
        """Display a smooth circular/pill speech bubble above Victor's portrait."""
        self.speech_text = text[:85] + ("..." if len(text) > 85 else "")
        self.speech_expires = time.time() + duration
        if self.sound_enabled:
            play_celeste_chime(notes=3, interval=0.04)

    def _start_voice_listening(self):
        """Click-to-listen: local microphone speech-to-text without text input boxes."""
        if self.is_listening:
            return

        self.is_listening = True
        self.show_speech("Listening...", duration=6.0)
        if self.sound_enabled:
            play_celeste_chime(notes=2, interval=0.06)

        def _worker():
            try:
                if not HAS_AUDIO:
                    self.root.after(0, lambda: self._on_poke_fallback())
                    return

                fs = 16000
                duration = 3.8
                recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype="int16")
                sd.wait()

                # Check if audio has energy
                import numpy as np
                peak = np.max(np.abs(recording))
                if peak < 400:
                    # Low volume / silence: gentle poke fallback
                    self.root.after(0, lambda: self._on_poke_fallback())
                    return

                wav_io = io.BytesIO()
                wavfile.write(wav_io, fs, recording)
                wav_io.seek(0)

                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_io) as source:
                    audio = recognizer.record(source)
                    text = recognizer.recognize_google(audio)

                if text and text.strip():
                    self.root.after(0, lambda t=text: self._dispatch_chat(t))
                else:
                    self.root.after(0, lambda: self._on_poke_fallback())
            except Exception:
                self.root.after(0, lambda: self._on_poke_fallback())
            finally:
                self.is_listening = False

        threading.Thread(target=_worker, daemon=True).start()

    def _on_poke_fallback(self):
        """Dynamic poke when no voice was captured."""
        def _poke():
            try:
                req = url_request.Request(
                    "http://127.0.0.1:8000/api/poke",
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
        """Send recognized voice prompt to Victor's backend."""
        self.set_emotion("thinking", "Processing...")
        def _send():
            try:
                data = json.dumps({"message": text}).encode("utf-8")
                req = url_request.Request(
                    "http://127.0.0.1:8000/api/chat",
                    data=data,
                    headers={"Content-Type": "application/json"},
                )
                with url_request.urlopen(req, timeout=20) as res:
                    body = json.loads(res.read().decode("utf-8"))
                    content = body.get("content", "")
                    emo = body.get("emotion", "happy")
                    self.root.after(0, lambda c=content, e=emo: self.set_emotion(e, c))
            except Exception:
                self.root.after(0, lambda: self.set_emotion("concerned", "Connection anomaly."))
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
            # Single click activates listening!
            self._start_voice_listening()
        self._dragging = False

    def _on_double_click(self, event):
        # Double click opens Workshop
        self._open_workshop()

    def _open_workshop(self):
        webbrowser.open("http://127.0.0.1:8000")

    def _show_context_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

    def _ws_telemetry(self):
        """Polls server for emotion, telemetry, and auto-hide status."""
        while self.ws_running:
            try:
                with url_request.urlopen("http://127.0.0.1:8000/api/status", timeout=2) as res:
                    data = json.loads(res.read().decode("utf-8"))
                    new_emo = data.get("emotion")
                    if new_emo and new_emo != self.emotion and not self.is_listening:
                        self.root.after(0, lambda e=new_emo: self.set_emotion(e))

                    # Auto-Hide when Workshop is focused in front
                    workshop_focused = data.get("workshop_focused", False)
                    options = data.get("companion_options", {})
                    auto_hide = options.get("auto_hide", self.auto_hide_enabled)

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
        return EMOTION_ACCENTS.get(self.emotion, "#D4A574")

    def _draw(self):
        self.canvas.delete("all")
        t = self.anim_tick

        # Floating / breathing bob effect
        bob_offset = 0
        if self.emotion in ["idle", "neutral", "thinking"]:
            bob_offset = int(round(math.sin(t * 0.08) * 3))
        elif self.emotion in ["excited", "happy"]:
            bob_offset = int(round(abs(math.sin(t * 0.2)) * -5))
        elif self.emotion == "concerned":
            bob_offset = 2

        img_y = 65 + bob_offset

        # Render active emotion sprite
        sprite = self.sprites.get(self.emotion) or self.sprites.get("neutral")
        if sprite:
            self.canvas.create_image(120, img_y + 72, image=sprite)
        else:
            # Fallback circle if PIL is unavailable
            accent = self._get_accent_color()
            self.canvas.create_oval(70, img_y, 170, img_y + 100, fill="#121417", outline=accent, width=2)
            self.canvas.create_text(120, img_y + 50, text=self.emotion.upper(), fill="#E6E6E6", font=("Segoe UI", 10, "bold"))

        # Render animated circular/pill speech bubble
        if self.speech_text and time.time() < self.speech_expires:
            accent = self._get_accent_color()
            bubble_pulse = int(round(math.sin(t * 0.15) * 2))
            
            # Smooth circular bubble geometry
            bx1 = 14
            by1 = 8 + bubble_pulse
            bx2 = 226
            by2 = 56 + bubble_pulse
            
            # Draw circular/pill oval bubble
            self.canvas.create_oval(
                bx1, by1, bx2, by2,
                fill="#0E1012",
                outline=accent,
                width=1.5,
            )
            
            # Connecting speech bubble dots floating towards Victor's head
            self.canvas.create_oval(117, by2 + 2, 123, by2 + 8, fill="#0E1012", outline=accent, width=1)
            self.canvas.create_oval(119, by2 + 9, 121, by2 + 11, fill=accent, outline=accent)

            # Bubble text (clean typography, no emojis)
            self.canvas.create_text(
                120,
                32 + bubble_pulse,
                text=self.speech_text,
                width=190,
                fill="#F0EDE8",
                font=("Segoe UI", 8),
                justify="center",
            )

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
