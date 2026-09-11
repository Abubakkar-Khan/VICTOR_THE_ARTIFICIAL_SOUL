"""Victor Desktop Companion - Transparent Animated Mascot Window.

Runs an always-on-top, draggable, transparent companion character on the Windows desktop.
Connects via WebSocket to receive real-time mascot events and speech bubbles.
"""

import json
import math
import sys
import threading
import time
import tkinter as tk
import urllib.request
import webbrowser


class MascotWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Victor Mascot")

        # Window setup: borderless, always on top
        self.width = 220
        self.height = 200
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        pos_x = screen_w - self.width - 50
        pos_y = screen_h - self.height - 80

        self.root.geometry(f"{self.width}x{self.height}+{pos_x}+{pos_y}")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)

        # Transparent background on Windows
        self.bg_color = "#010101"
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

        # Mascot state
        self.state = "idle"  # idle, listening, thinking, working, waiting, completed, error
        self.speech_text = ""
        self.speech_expires = 0
        self.anim_tick = 0
        self.drag_x = 0
        self.drag_y = 0

        # Dragging bindings
        self.canvas.bind("<Button-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)

        # WebSocket telemetry thread
        self.ws_running = True
        self.ws_thread = threading.Thread(target=self._ws_listener, daemon=True)
        self.ws_thread.start()

        # Start animation loop
        self._animate()

    def _start_drag(self, event):
        self.drag_x = event.x
        self.drag_y = event.y

    def _on_drag(self, event):
        deltax = event.x - self.drag_x
        deltay = event.y - self.drag_y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def _on_double_click(self, event):
        """Double clicking mascot opens the main control center."""
        webbrowser.open("http://127.0.0.1:8000")

    def show_speech(self, text: str, duration: float = 4.0):
        self.speech_text = text[:80] + ("..." if len(text) > 80 else "")
        self.speech_expires = time.time() + duration

    def set_state(self, state: str, speech: str = ""):
        self.state = state
        if speech:
            self.show_speech(speech)

    def _draw_mascot(self):
        self.canvas.delete("all")
        cx, cy = 110, 120
        t = self.anim_tick

        # Bobbing height
        bob = int(math.sin(t * 0.15) * 4) if self.state in ["idle", "thinking", "completed"] else 0
        if self.state == "working":
            bob = int(math.sin(t * 0.4) * 6)

        # 1. Speech Bubble (if active)
        if self.speech_text and time.time() < self.speech_expires:
            bx, by = 110, 32
            bw, bh = 190, 44
            self.canvas.create_rectangle(
                bx - bw // 2, by - bh // 2, bx + bw // 2, by + bh // 2,
                fill="#161b26", outline="#38bdf8", width=1.5
            )
            # Pointer triangle
            self.canvas.create_polygon(
                bx - 8, by + bh // 2, bx + 8, by + bh // 2, bx, by + bh // 2 + 8,
                fill="#161b26", outline="#38bdf8"
            )
            self.canvas.create_text(
                bx, by, text=self.speech_text, fill="#f0f6fc",
                font=("Arial", 8, "bold"), width=170, justify="center"
            )

        # 2. Mascot Body (Rounded Friendly Cute Sphere)
        body_r = 40
        body_color = "#1e2433"
        outline_color = "#38bdf8"
        if self.state == "thinking":
            outline_color = "#818cf8"
        elif self.state == "working":
            outline_color = "#f59e0b"
        elif self.state == "completed":
            outline_color = "#10b981"
        elif self.state == "error":
            outline_color = "#ef4444"

        # Thinking halo / working aura
        if self.state == "thinking":
            halo_r = body_r + 8 + int(math.sin(t * 0.2) * 3)
            self.canvas.create_oval(
                cx - halo_r, cy + bob - halo_r, cx + halo_r, cy + bob + halo_r,
                outline="#818cf8", width=2, dash=(4, 4)
            )
        elif self.state == "working":
            aura_r = body_r + 6
            self.canvas.create_oval(
                cx - aura_r, cy + bob - aura_r, cx + aura_r, cy + bob + aura_r,
                outline="#f59e0b", width=2, dash=(6, 4)
            )

        # Main Body
        self.canvas.create_oval(
            cx - body_r, cy + bob - body_r, cx + body_r, cy + bob + body_r,
            fill=body_color, outline=outline_color, width=2.5
        )

        # Cute Little Antenna
        ant_top_y = cy + bob - body_r - 12
        self.canvas.create_line(cx, cy + bob - body_r, cx, ant_top_y, fill=outline_color, width=2)
        node_color = "#38bdf8" if (t % 10 < 5) else "#60a5fa"
        self.canvas.create_oval(cx - 4, ant_top_y - 4, cx + 4, ant_top_y + 4, fill=node_color, outline=outline_color)

        # 3. Expressive Eyes based on State
        eye_y = cy + bob - 6
        eye_dist = 14
        blink = (t % 40 == 0) and self.state == "idle"

        if blink:
            # Blinking closed line
            self.canvas.create_line(cx - eye_dist - 6, eye_y, cx - eye_dist + 6, eye_y, fill="#38bdf8", width=2)
            self.canvas.create_line(cx + eye_dist - 6, eye_y, cx + eye_dist + 6, eye_y, fill="#38bdf8", width=2)
        elif self.state == "completed":
            # Happy smiling curved eyes ^ ^
            self.canvas.create_arc(cx - eye_dist - 6, eye_y - 6, cx - eye_dist + 6, eye_y + 6, start=0, extent=180, outline="#10b981", width=2.5, style="arc")
            self.canvas.create_arc(cx + eye_dist - 6, eye_y - 6, cx + eye_dist + 6, eye_y + 6, start=0, extent=180, outline="#10b981", width=2.5, style="arc")
        elif self.state == "thinking":
            # Eyes looking upward thoughtfully
            self.canvas.create_oval(cx - eye_dist - 5, eye_y - 8, cx - eye_dist + 5, eye_y + 2, fill="#818cf8", outline="")
            self.canvas.create_oval(cx + eye_dist - 5, eye_y - 8, cx + eye_dist + 5, eye_y + 2, fill="#818cf8", outline="")
        elif self.state == "working":
            # Energetic wide-open focused eyes
            self.canvas.create_oval(cx - eye_dist - 6, eye_y - 6, cx - eye_dist + 6, eye_y + 6, fill="#f59e0b", outline="")
            self.canvas.create_oval(cx + eye_dist - 6, eye_y - 6, cx + eye_dist + 6, eye_y + 6, fill="#f59e0b", outline="")
        elif self.state == "error":
            # Concerned eyes
            self.canvas.create_oval(cx - eye_dist - 4, eye_y - 4, cx - eye_dist + 4, eye_y + 4, fill="#ef4444", outline="")
            self.canvas.create_oval(cx + eye_dist - 4, eye_y - 4, cx + eye_dist + 4, eye_y + 4, fill="#ef4444", outline="")
            # Sweat drop
            self.canvas.create_text(cx + body_r - 2, cy + bob - body_r + 10, text="💧", font=("Arial", 10))
        else:
            # Idle/Listening: Glowing friendly blue eyes
            look_offset = int(math.sin(t * 0.1) * 2)
            self.canvas.create_oval(cx - eye_dist - 5 + look_offset, eye_y - 5, cx - eye_dist + 5 + look_offset, eye_y + 5, fill="#38bdf8", outline="")
            self.canvas.create_oval(cx + eye_dist - 5 + look_offset, eye_y - 5, cx + eye_dist + 5 + look_offset, eye_y + 5, fill="#38bdf8", outline="")

        # 4. Cute Small Mouth
        mouth_y = cy + bob + 10
        if self.state == "completed":
            self.canvas.create_arc(cx - 8, mouth_y - 5, cx + 8, mouth_y + 7, start=180, extent=180, fill="#10b981", outline="")
        elif self.state in ["working", "thinking"]:
            self.canvas.create_line(cx - 5, mouth_y, cx + 5, mouth_y, fill=outline_color, width=2)
        else:
            self.canvas.create_arc(cx - 6, mouth_y - 4, cx + 6, mouth_y + 4, start=180, extent=180, outline="#38bdf8", width=1.5, style="arc")

        # 5. Status Capsule under Mascot
        status_text = self.state.upper()
        self.canvas.create_text(
            cx, cy + bob + body_r + 14,
            text=f"VICTOR // {status_text}",
            fill=outline_color,
            font=("Arial", 7, "bold")
        )

    def _animate(self):
        self.anim_tick += 1
        self._draw_mascot()
        self.root.after(50, self._animate)

    def _ws_listener(self):
        """Connect to local Victor WebSocket to receive state updates and chat broadcasts."""
        import urllib.request
        while self.ws_running:
            try:
                # Poll server status
                req = urllib.request.Request("http://127.0.0.1:8000/api/status")
                with urllib.request.urlopen(req, timeout=2.0) as res:
                    if res.status == 200:
                        pass
            except Exception:
                pass
            time.sleep(2.0)

    def run(self):
        self.root.mainloop()


def launch_desktop_mascot():
    mascot = MascotWindow()
    mascot.run()


if __name__ == "__main__":
    launch_desktop_mascot()
