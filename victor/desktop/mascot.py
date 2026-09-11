import json
import math
import sys
import threading
import time
import tkinter as tk
import urllib.request
import webbrowser


COLORS = {
    'B': "#3D3428", # Outline (Dark brown)
    'M': "#4A3F32", # Main Body (Warm brown)
    'L': "#5C5040", # Highlighted body (Lighter warm brown)
    'H': "#D4A574", # Bright highlight (Amber)
    'E': "#E8E4DE", # Eye whites
    'P': "#C8956C", # Pupil
    'T': "#010101", # Transparent
}

BASE_BODY = [
    "                                ",
    "                                ",
    "                                ",
    "                                ",
    "                                ",
    "                                ",
    "           BBBBBBBB             ",
    "         BBLLLLLLLLBB           ",
    "        BLLLLLLLLLLLLB          ",
    "       BLLMMMMMMMMMMLLB         ",
    "      BLLMMMMMMMMMMMMLLB        ",
    "      BLMMMMMMMMMMMMMMMLB       ",
    "     BLMMMMMMMMMMMMMMMMMLB      ",
    "     BLMMMMMMMMMMMMMMMMMLB      ",
    "     BLMMMMMMMMMMMMMMMMMLB      ",
    "     BLMMMMMMMMMMMMMMMMMLB      ",
    "     BLMMMMMMMMMMMMMMMMMLB      ",
    "     BLMMMMMMMMMMMMMMMMMLB      ",
    "     BLMMMMMMMMMMMMMMMMMLB      ",
    "     BLMMMMMMMMMMMMMMMMMLB      ",
    "     BLMMMMMMMMMMMMMMMMMLB      ",
    "      BLMMMMMMMMMMMMMMMLB       ",
    "      BLMMMMMMMMMMMMMMMLB       ",
    "       BLLMMMMMMMMMMMMLLB       ",
    "        BLLMMMMMMMMMMLLB        ",
    "         BBLLLLLLLLLLBB         ",
    "           BBBBBBBBBB           ",
    "        BBB          BBB        ",
    "       BMMB          BMMB       ",
    "       BBBB          BBBB       ",
    "                                ",
    "                                "
]

EYE_NORMAL = [
    " BBB ",
    "BEEEB",
    "BEEPB",
    "BEEEB",
    " BBB "
]

EYE_BLINK = [
    "     ",
    "     ",
    " BBB ",
    "     ",
    "     "
]

EYE_HAPPY = [
    "     ",
    " BBB ",
    "B   B",
    "     ",
    "     "
]

EYE_THINK = [
    " BBB ",
    "BPPPB",
    "BEEEB",
    "BEEEB",
    " BBB "
]

EYE_WIDE = [
    " BBB ",
    "BEEPB",
    "BEPEB",
    "BEEPB",
    " BBB "
]

EYE_DROOP = [
    " BBB ",
    " BPEB",
    " BEEB",
    " BBB ",
    "     "
]

EYE_SLEEP = [
    "     ",
    "     ",
    " BBB ",
    "     ",
    "     "
]

MOUTH_NORMAL = [" B "]
MOUTH_SMILE = [
    "B B",
    " B "
]
MOUTH_SAD = [
    " B ",
    "B B"
]
MOUTH_THINK = ["B  "]

EAR_PERK = [
    " B  ",
    "BMB ",
    "BMB ",
    " BB "
]


class MascotWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Victor Companion")

        # Window setup: borderless, always on top
        self.width = 160
        self.height = 160
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
        self.state = "idle"  # idle, listening, thinking, working, done, error, sleeping
        self.speech_text = ""
        self.speech_expires = 0
        self.anim_tick = 0
        self.drag_x = 0
        self.drag_y = 0
        self.input_active = False

        # Chat Entry Setup
        self.chat_entry = tk.Entry(
            self.root, 
            font=("Courier", 10), 
            bg="#201F1B", 
            fg="#E8E4DE", 
            insertbackground="#E8E4DE", 
            relief="flat"
        )
        self.chat_entry.bind("<Return>", self._send_chat)

        # Context Menu
        self.menu = tk.Menu(self.root, tearoff=0, bg="#201F1B", fg="#E8E4DE", activebackground="#4A3F32")
        self.menu.add_command(label="Talk...", command=self.show_input_bubble)
        self.menu.add_command(label="Open Workshop", command=self._open_workshop)
        self.menu.add_command(label="Memory", command=lambda: self.set_state("thinking", "Accessing memory..."))
        self.menu.add_separator()
        self.menu.add_command(label="Pause companion", command=lambda: self.set_state("sleeping"))
        self.menu.add_command(label="Settings", command=lambda: self.show_speech("Settings coming soon!"))
        self.menu.add_command(label="Quit", command=self.root.destroy)

        # Bindings
        self.canvas.bind("<Button-1>", self._on_single_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._end_drag)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<Button-3>", self._show_context_menu)

        self._dragging = False

        # WebSocket telemetry thread
        self.ws_running = True
        self.ws_thread = threading.Thread(target=self._ws_listener, daemon=True)
        self.ws_thread.start()

        # Start animation loop
        self._animate()

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
            # It was just a click
            self.show_input_bubble()
        self._dragging = False

    def _on_double_click(self, event):
        self._open_workshop()

    def _open_workshop(self):
        webbrowser.open("http://127.0.0.1:8000")

    def _show_context_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

    def show_input_bubble(self):
        self.chat_entry.place(x=20, y=10, width=120, height=24)
        self.chat_entry.focus_set()
        self.input_active = True

    def _send_chat(self, event):
        text = self.chat_entry.get().strip()
        self.chat_entry.delete(0, tk.END)
        self.chat_entry.place_forget()
        self.input_active = False
        
        if text:
            # Show what the user typed briefly
            self.set_state("listening", text)
            # In a real app, send to WebSocket here.

    def show_speech(self, text: str, duration: float = 4.0):
        self.speech_text = text[:80] + ("..." if len(text) > 80 else "")
        self.speech_expires = time.time() + duration

    def set_state(self, state: str, speech: str = ""):
        self.state = state
        if speech:
            self.show_speech(speech)

    def _place_pattern(self, grid, px, py, pattern):
        for y, row in enumerate(pattern):
            for x, char in enumerate(row):
                if char != ' ':
                    if 0 <= py + y < len(grid) and 0 <= px + x < len(grid[0]):
                        grid[py + y][px + x] = char

    def _draw_mascot(self):
        self.canvas.delete("all")
        t = self.anim_tick

        # Bobbing logic
        bob = 0
        if self.state in ["idle", "listening", "sleeping"]:
            # Breathing
            bob = 1 if (t % 40 < 20) else 0
        elif self.state == "working":
            # Bouncing
            bob = 2 if (t % 10 < 5) else 0

        # Create fresh grid
        grid = [list(row) for row in BASE_BODY]

        # Determine facial features based on state
        left_eye = EYE_NORMAL
        right_eye = EYE_NORMAL
        mouth = MOUTH_NORMAL
        
        blink = (t % 60 < 3) and self.state == "idle"

        if blink:
            left_eye = right_eye = EYE_BLINK
        elif self.state == "listening":
            self._place_pattern(grid, 6, 2, EAR_PERK)
        elif self.state == "thinking":
            left_eye = right_eye = EYE_THINK
            mouth = MOUTH_THINK
            if t % 20 < 10:
                self.canvas.create_text(130, 40, text="...", fill="#E8E4DE", font=("Courier", 12, "bold"))
        elif self.state == "working":
            left_eye = right_eye = EYE_WIDE
            mouth = MOUTH_NORMAL
        elif self.state == "done":
            left_eye = right_eye = EYE_HAPPY
            mouth = MOUTH_SMILE
        elif self.state == "error":
            left_eye = right_eye = EYE_DROOP
            mouth = MOUTH_SAD
        elif self.state == "sleeping":
            left_eye = right_eye = EYE_SLEEP
            if t % 30 < 15:
                self.canvas.create_text(130, 40, text="Zzz", fill="#D4A574", font=("Courier", 10, "bold"))

        # Apply facial features
        self._place_pattern(grid, 8, 12, left_eye)
        self._place_pattern(grid, 18, 12, right_eye)
        self._place_pattern(grid, 14, 18, mouth)

        # Render pixels
        pixel_size = 3
        offset_x = (self.width - (32 * pixel_size)) // 2
        offset_y = 50 + bob

        for y, row in enumerate(grid):
            for x, char in enumerate(row):
                if char != ' ' and char in COLORS:
                    color = COLORS[char]
                    px = offset_x + x * pixel_size
                    py = offset_y + y * pixel_size
                    self.canvas.create_rectangle(px, py, px + pixel_size, py + pixel_size, fill=color, outline=color, width=0)

        # Speech Bubble Rendering
        if self.speech_text and time.time() < self.speech_expires and not self.input_active:
            bx, by = self.width // 2, 25
            bw, bh = 140, 36
            # Background
            self.canvas.create_rectangle(
                bx - bw // 2, by - bh // 2, bx + bw // 2, by + bh // 2,
                fill="#201F1B", outline="#2A2924", width=2
            )
            # Pointer
            self.canvas.create_polygon(
                bx - 6, by + bh // 2, bx + 6, by + bh // 2, bx, by + bh // 2 + 6,
                fill="#201F1B", outline="#2A2924"
            )
            # Hide the outline overlapping line
            self.canvas.create_line(
                bx - 5, by + bh // 2, bx + 5, by + bh // 2,
                fill="#201F1B", width=2
            )
            # Text
            self.canvas.create_text(
                bx, by, text=self.speech_text, fill="#E8E4DE",
                font=("Courier", 8), width=130, justify="center"
            )

    def _animate(self):
        self.anim_tick += 1
        self._draw_mascot()
        self.root.after(50, self._animate)

    def _ws_listener(self):
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
