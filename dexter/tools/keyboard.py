import ctypes
from ctypes import wintypes
import time
from typing import Any
from dexter.tools.base import BaseTool, PermissionLevel

INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP       = 0x0002
KEYEVENTF_UNICODE     = 0x0004
KEYEVENTF_SCANCODE    = 0x0008

class KEYBDINPUT(ctypes.Structure):
    _fields_ = (("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)))

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = (("ki", KEYBDINPUT),
                    ("mi", ctypes.c_byte * 28),
                    ("hi", ctypes.c_byte * 28))
    _anonymous_ = ("_input",)
    _fields_ = (("type", wintypes.DWORD),
                ("_input", _INPUT))

VK_MAP = {
    'backspace': 0x08, 'tab': 0x09, 'clear': 0x0C, 'enter': 0x0D,
    'shift': 0x10, 'ctrl': 0x11, 'alt': 0x12, 'pause': 0x13,
    'capslock': 0x14, 'escape': 0x1B, 'space': 0x20, 'pageup': 0x21,
    'pagedown': 0x22, 'end': 0x23, 'home': 0x24, 'left': 0x25,
    'up': 0x26, 'right': 0x27, 'down': 0x28, 'select': 0x29,
    'print': 0x2A, 'execute': 0x2B, 'printscreen': 0x2C, 'insert': 0x2D,
    'delete': 0x2E, 'help': 0x2F, 'win': 0x5B, 'rightwin': 0x5C,
    'apps': 0x5D, 'sleep': 0x5F, 'numpad0': 0x60, 'numpad1': 0x61,
    'numpad2': 0x62, 'numpad3': 0x63, 'numpad4': 0x64, 'numpad5': 0x65,
    'numpad6': 0x66, 'numpad7': 0x67, 'numpad8': 0x68, 'numpad9': 0x69,
    'multiply': 0x6A, 'add': 0x6B, 'separator': 0x6C, 'subtract': 0x6D,
    'decimal': 0x6E, 'divide': 0x6F, 'f1': 0x70, 'f2': 0x71,
    'f3': 0x72, 'f4': 0x73, 'f5': 0x74, 'f6': 0x75,
    'f7': 0x76, 'f8': 0x77, 'f9': 0x78, 'f10': 0x79,
    'f11': 0x7A, 'f12': 0x7B, 'numlock': 0x90, 'scrolllock': 0x91,
    'volumemute': 0xAD, 'volumedown': 0xAE, 'volumeup': 0xAF,
    'nexttrack': 0xB0, 'prevtrack': 0xB1, 'stopmedia': 0xB2, 'playpause': 0xB3,
}

for c in range(0x41, 0x5A + 1):
    VK_MAP[chr(c).lower()] = c
for c in range(0x30, 0x39 + 1):
    VK_MAP[chr(c)] = c

def _send_input(*inputs):
    nInputs = len(inputs)
    lpInput = (INPUT * nInputs)(*inputs)
    cbSize = ctypes.sizeof(INPUT)
    return ctypes.windll.user32.SendInput(nInputs, ctypes.byref(lpInput), cbSize)

def _create_keyboard_input(vk, scan, flags):
    x = INPUT()
    x.type = INPUT_KEYBOARD
    x.ki = KEYBDINPUT(wVk=vk, wScan=scan, dwFlags=flags, time=0, dwExtraInfo=None)
    return x

class KeyboardTool(BaseTool):
    name = "keyboard"
    description = "Keyboard simulation tool using SendInput for typing, pressing keys, and hotkeys."
    permission = PermissionLevel.CONTROLLED
    slash_command = "/type"
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["type_text", "press_key", "hotkey"],
                "description": "Action to perform."
            },
            "text": {
                "type": "string",
                "description": "Text to type (for type_text)."
            },
            "key": {
                "type": "string",
                "description": "Key to press (for press_key)."
            },
            "keys": {
                "type": "string",
                "description": "Keys for hotkey combo (for hotkey)."
            }
        },
        "required": ["action"]
    }

    def intent_patterns(self) -> list[dict]:
        return [
            {"pattern": r'^type\s+(.+)$', "extract": lambda m: {"action": "type_text", "text": m.group(1).strip()}},
            {"pattern": r'^press\s+([^\+]+)$', "extract": lambda m: {"action": "press_key", "key": m.group(1).strip()}},
            {"pattern": r'^hotkey\s+(.+)$', "extract": lambda m: {"action": "hotkey", "keys": m.group(1).strip()}},
            {"pattern": r'^press\s+(.+\+.+)$', "extract": lambda m: {"action": "hotkey", "keys": m.group(1).strip()}},
        ]

    async def run(self, **kwargs) -> Any:
        action = kwargs.get("action")
        if action == "type_text":
            text = kwargs.get("text", "")
            for char in text:
                scan = ord(char)
                down = _create_keyboard_input(0, scan, KEYEVENTF_UNICODE)
                up = _create_keyboard_input(0, scan, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP)
                _send_input(down, up)
                time.sleep(0.01)
            return {"status": "success", "action": "type_text", "typed": text}
            
        elif action == "press_key":
            key = kwargs.get("key", "").lower().strip()
            vk = VK_MAP.get(key)
            if vk is None:
                return {"status": "error", "message": f"Unknown key: {key}"}
            down = _create_keyboard_input(vk, 0, 0)
            up = _create_keyboard_input(vk, 0, KEYEVENTF_KEYUP)
            _send_input(down, up)
            return {"status": "success", "action": "press_key", "key": key}
            
        elif action == "hotkey":
            keys_str = kwargs.get("keys", "").lower().strip()
            parts = [p.strip() for p in keys_str.split('+')]
            vks = []
            for p in parts:
                vk = VK_MAP.get(p)
                if vk is None:
                    return {"status": "error", "message": f"Unknown key in hotkey: {p}"}
                vks.append(vk)
                
            inputs = []
            for vk in vks:
                inputs.append(_create_keyboard_input(vk, 0, 0))
            for vk in reversed(vks):
                inputs.append(_create_keyboard_input(vk, 0, KEYEVENTF_KEYUP))
                
            _send_input(*inputs)
            return {"status": "success", "action": "hotkey", "keys": keys_str}
            
        return {"status": "error", "message": "Invalid action"}

    def format_display(self, result: Any) -> str:
        out = result.output if hasattr(result, "output") else result
        if isinstance(out, dict):
            status = out.get('status')
            if status == 'error':
                return f"Keyboard Error: {out.get('message')}"
            action = out.get('action')
            if action == 'type_text':
                return f"Typed: \"{out.get('typed')}\""
            elif action == 'press_key':
                return f"Pressed key [{out.get('key')}]."
            elif action == 'hotkey':
                return f"Executed hotkey [{out.get('keys')}]."
        return str(out)
