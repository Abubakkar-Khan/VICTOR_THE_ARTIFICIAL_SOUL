"""Victor Desktop Companion — Pixel-Art Embodiment of the Artificial Soul."""

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


EMOTIONS = {
    "neutral": {"emoji": "😐", "label": "Neutral", "desc": "Normal interaction"},
    "happy": {"emoji": "😊", "label": "Happy", "desc": "Successful/helpful outcome"},
    "curious": {"emoji": "🤔", "label": "Curious", "desc": "Exploring/learning"},
    "idle": {"emoji": "😴", "label": "Idle", "desc": "Nothing happening"},
    "thinking": {"emoji": "🧠", "label": "Thinking", "desc": "Processing"},
    "excited": {"emoji": "😮", "label": "Excited", "desc": "Interesting discovery"},
    "confused": {"emoji": "😕", "label": "Confused", "desc": "Unclear request/problem"},
    "concerned": {"emoji": "😔", "label": "Concerned", "desc": "Failure/problem"},
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
        self.input_active = False
        self.sound_enabled = True

        # Sprite cache
        self.sprites = {}
        self._load_sprites()

        # Chat Entry Setup
        self.chat_entry = tk.Entry(
            self.root,
            font=("Segoe UI", 9),
            bg="#201F1B",
            fg="#E8E4DE",
            insertbackground="#E8E4DE",
            relief="solid",
            bd=1,
        )
        self.chat_entry.bind("<Return>", self._send_chat)
        self.chat_entry.bind("<Escape>", lambda e: self._hide_input_bubble())

        # Context Menu
        self._setup_context_menu()

        # Mouse Bindings
        self.canvas.bind("<Button-1>", self._on_single_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._end_drag)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<Button-3>", self._show_context_menu)

        # Polling & WebSocket telemetry thread
        self.ws_running = True
        self.ws_thread = threading.Thread(target=self._ws_telemetry, daemon=True)
        self.ws_thread.start()

        # Start animation loop
        self._animate()

    def _load_sprites(self):
        """Load and resize the 8 emotion sprites."""
        if not HAS_PIL:
            return

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
                    # Resize to fit companion canvas
                    resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    self.sprites[emo] = ImageTk.PhotoImage(resized)
                except Exception as e:
                    print(f"Error loading sprite for {emo}: {e}")

    def _setup_context_menu(self):
        self.menu = tk.Menu(
            self.root,
            tearoff=0,
            bg="#181815",
            fg="#E8E4DE",
            activebackground="#2A2924",
            activeforeground="#D4A574",
            font=("Segoe UI", 9),
        )
        self.menu.add_command(label="Talk to Victor...", command=self.show_input_bubble)
        self.menu.add_command(label="Open Workshop", command=self._open_workshop)
        
        # Emotions Submenu
        emo_menu = tk.Menu(
            self.menu,
            tearoff=0,
            bg="#181815",
            fg="#E8E4DE",
            activebackground="#2A2924",
            activeforeground="#D4A574",
            font=("Segoe UI", 9),
        )
        for key, info in EMOTIONS.items():
            emo_menu.add_command(
                label=f"{info['emoji']} {info['label']} — {info['desc']}",
                command=lambda k=key: self.set_emotion(k, f"Feeling {k}"),
            )
        self.menu.add_cascade(label="Emotions", menu=emo_menu)
        self.menu.add_separator()
        self.menu.add_command(label="Mute Sounds" if self.sound_enabled else "Enable Sounds", command=self._toggle_sound)
        self.menu.add_command(label="Sleep / Idle", command=lambda: self.set_emotion("idle", "Resting..."))
        self.menu.add_command(label="Quit", command=self.root.destroy)

    def _toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        self.show_speech("Sounds muted." if not self.sound_enabled else "Sounds enabled.")
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

    def show_speech(self, text: str, duration: float = 4.0):
        """Display a speech bubble above Victor's portrait."""
        self.speech_text = text[:90] + ("..." if len(text) > 90 else "")
        self.speech_expires = time.time() + duration
        if self.sound_enabled:
            play_celeste_chime(notes=3, interval=0.04)

    def show_input_bubble(self):
        """Show the quick chat text entry above Victor's head."""
        self.chat_entry.place(x=20, y=10, width=200, height=26)
        self.chat_entry.focus_set()
        self.input_active = True

    def _hide_input_bubble(self):
        self.chat_entry.delete(0, tk.END)
        self.chat_entry.place_forget()
        self.input_active = False

    def _send_chat(self, event):
        text = self.chat_entry.get().strip()
        self._hide_input_bubble()
        if not text:
            return

        self.set_emotion("thinking", "Thinking...")
        
        # Dispatch to backend in background thread
        def _send():
            try:
                data = json.dumps({"message": text}).encode("utf-8")
                req = url_request.Request(
                    "http://127.0.0.1:8000/api/chat",
                    data=data,
                    headers={"Content-Type": "application/json"},
                )
                with url_request.urlopen(req, timeout=15) as res:
                    body = json.loads(res.read().decode("utf-8"))
                    content = body.get("content", "")
                    emo = body.get("emotion", "happy")
                    self.root.after(0, lambda: self.set_emotion(emo, content))
            except Exception as e:
                self.root.after(0, lambda: self.set_emotion("concerned", "Could not reach server."))

        threading.Thread(target=_send, daemon=True).start()

    def _on_single_click(self, event):
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
            self.show_input_bubble()
        self._dragging = False

    def _on_double_click(self, event):
        self._open_workshop()

    def _open_workshop(self):
        webbrowser.open("http://127.0.0.1:8000")

    def _show_context_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

    def _ws_telemetry(self):
        """Polls server for emotion and telemetry updates."""
        while self.ws_running:
            try:
                with url_request.urlopen("http://127.0.0.1:8000/api/status", timeout=2) as res:
                    data = json.loads(res.read().decode("utf-8"))
                    new_emo = data.get("emotion")
                    if new_emo and new_emo != self.emotion and not self.input_active:
                        self.root.after(0, lambda e=new_emo: self.set_emotion(e))
            except Exception:
                pass
            time.sleep(1.5)

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
            self.canvas.create_oval(70, img_y, 170, img_y + 100, fill="#4A3F32", outline="#D4A574", width=2)
            self.canvas.create_text(120, img_y + 50, text=EMOTIONS.get(self.emotion, {}).get("emoji", "😐"), font=("Segoe UI", 24))

        # Render speech bubble if active
        if self.speech_text and time.time() < self.speech_expires:
            # Bubble rect
            self.canvas.create_rectangle(12, 10, 228, 52, fill="#181815", outline="#2A2924", width=1)
            # Arrow pointer pointing to Victor's head
            self.canvas.create_polygon(115, 52, 125, 52, 120, 58, fill="#181815", outline="#2A2924")
            # Text inside bubble
            self.canvas.create_text(
                120,
                30,
                text=self.speech_text,
                width=204,
                fill="#E8E4DE",
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
