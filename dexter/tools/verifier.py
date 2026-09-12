"""Verification Engine and Win32 inspection helpers for Victor.

This module provides reusable primitives to verify that actions requested by the user
have actually taken effect on the visible Windows desktop or filesystem before reporting
success. Tool execution != action success.
"""

import asyncio
import ctypes
from ctypes import wintypes
from enum import Enum
import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class ActionResultStatus(str, Enum):
    """Explicit lifecycle states for tool actions."""
    REQUESTED = "requested"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    EXECUTED_UNVERIFIED = "executed_unverified"
    FAILED = "failed"
    TIMEOUT = "timeout"


# Win32 Constants
SW_HIDE = 0
SW_SHOWNORMAL = 1
SW_SHOWMINIMIZED = 2
SW_MAXIMIZE = 3
SW_SHOWNOACTIVATE = 4
SW_SHOW = 5
SW_MINIMIZE = 6
SW_SHOWMINNOACTIVE = 7
SW_SHOWNA = 8
SW_RESTORE = 9
WM_CLOSE = 0x0010
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

if sys.platform == "win32":
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
else:
    user32 = None
    kernel32 = None


# ── Generic Polling Helpers ─────────────────────────────────────────

def wait_for_condition(
    predicate: Callable[[], Any],
    timeout: float = 5.0,
    poll_interval: float = 0.25,
    initial_wait: float = 0.25,
) -> Tuple[bool, Any]:
    """Poll a predicate synchronously until it returns truthy or timeout expires."""
    if initial_wait > 0:
        time.sleep(initial_wait)

    start = time.time()
    res = predicate()
    if res:
        return True, res

    while (time.time() - start) < timeout:
        time.sleep(poll_interval)
        res = predicate()
        if res:
            return True, res

    return False, None


async def wait_for_condition_async(
    predicate: Callable[[], Any],
    timeout: float = 5.0,
    poll_interval: float = 0.25,
    initial_wait: float = 0.25,
) -> Tuple[bool, Any]:
    """Poll a predicate asynchronously until it returns truthy or timeout expires."""
    if initial_wait > 0:
        await asyncio.sleep(initial_wait)

    start = time.time()
    res = predicate()
    if asyncio.iscoroutine(res):
        res = await res
    if res:
        return True, res

    while (time.time() - start) < timeout:
        await asyncio.sleep(poll_interval)
        res = predicate()
        if asyncio.iscoroutine(res):
            res = await res
        if res:
            return True, res

    return False, None


# ── Win32 Window Inspection Helpers ─────────────────────────────────

def get_window_title(hwnd: int) -> str:
    """Get the window title for a given HWND."""
    if not user32 or not hwnd:
        return ""
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def is_window_visible(hwnd: int) -> bool:
    """Return True if the window is visible on screen."""
    if not user32 or not hwnd:
        return False
    return bool(user32.IsWindowVisible(hwnd))


def is_window_foreground(hwnd: int) -> bool:
    """Return True if the specified window is the foreground window."""
    if not user32 or not hwnd:
        return False
    fg = user32.GetForegroundWindow()
    return bool(fg and int(fg) == int(hwnd))


def is_window_minimized(hwnd: int) -> bool:
    """Return True if the window is currently minimized."""
    if not user32 or not hwnd:
        return False
    return bool(user32.IsIconic(hwnd))


def is_window_maximized(hwnd: int) -> bool:
    """Return True if the window is currently maximized."""
    if not user32 or not hwnd:
        return False
    return bool(user32.IsZoomed(hwnd))


def get_window_process_id(hwnd: int) -> Optional[int]:
    """Return the process ID (PID) that owns the window."""
    if not user32 or not hwnd:
        return None
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value if pid.value else None


def get_window_process_name(hwnd: int) -> Optional[str]:
    """Return the executable image name (e.g. 'chrome.exe', 'notepad.exe') for the window."""
    pid = get_window_process_id(hwnd)
    if not pid or not kernel32:
        return None

    h_proc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h_proc:
        return None

    try:
        buf = ctypes.create_unicode_buffer(1024)
        size = wintypes.DWORD(len(buf))
        if kernel32.QueryFullProcessImageNameW(h_proc, 0, buf, ctypes.byref(size)):
            return os.path.basename(buf.value).lower()
    finally:
        kernel32.CloseHandle(h_proc)

    return None


def find_all_windows(only_visible: bool = True) -> List[Dict[str, Any]]:
    """Enumerate all top-level windows on the desktop."""
    if not user32:
        return []

    windows = []
    raw_fg = user32.GetForegroundWindow() if user32 else 0
    fg_hwnd = int(raw_fg) if raw_fg else 0

    def enum_proc(hwnd, lparam):
        if not only_visible or is_window_visible(hwnd):
            title = get_window_title(hwnd)
            if title or not only_visible:
                proc_name = get_window_process_name(hwnd)
                pid = get_window_process_id(hwnd)
                windows.append({
                    "hwnd": int(hwnd),
                    "title": title,
                    "process_name": proc_name or "",
                    "pid": pid,
                    "visible": is_window_visible(hwnd),
                    "is_foreground": (int(hwnd) == fg_hwnd),
                    "minimized": is_window_minimized(hwnd),
                    "maximized": is_window_maximized(hwnd),
                })
        return True

    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(EnumWindowsProc(enum_proc), 0)
    return windows


def find_visible_windows_for_process(process_hint: str) -> List[Dict[str, Any]]:
    """Find visible top-level windows matching a process name or app name hint."""
    hint = process_hint.lower().strip()
    if hint.endswith(".exe"):
        hint = hint[:-4]

    windows = find_all_windows(only_visible=True)
    matches = []
    for w in windows:
        p_name = w["process_name"].lower()
        title = w["title"].lower()
        if (hint in p_name) or (hint in title):
            matches.append(w)
    return matches


def find_window_by_title(title_query: str) -> Optional[Dict[str, Any]]:
    """Find a window by exact, startswith, or substring title match."""
    query = title_query.lower().strip()
    if not query:
        return None

    windows = find_all_windows(only_visible=True)

    # 1. Exact match
    for w in windows:
        if w["title"].lower() == query:
            return w

    # 2. Starts with
    for w in windows:
        if w["title"].lower().startswith(query):
            return w

    # 3. Contains
    for w in windows:
        if query in w["title"].lower():
            return w

    return None


def bring_window_to_foreground(hwnd: int) -> bool:
    """Bring the target window cleanly into the foreground."""
    if not user32 or not hwnd:
        return False

    try:
        user32.AllowSetForegroundWindow(-1)
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.08)
        return is_window_foreground(hwnd)
    except Exception:
        return False


def wait_for_window_close(hwnd: int, timeout: float = 3.0) -> bool:
    """Wait until a window handle is closed or destroyed."""
    if not user32 or not hwnd:
        return True

    def check_gone():
        if not user32.IsWindow(hwnd):
            return True
        if not user32.IsWindowVisible(hwnd):
            return True
        return False

    success, _ = wait_for_condition(check_gone, timeout=timeout, poll_interval=0.2, initial_wait=0.15)
    return success


# ── High-Level Action Verifiers ─────────────────────────────────────

class ActionVerifier:
    """Unified verification executor for desktop actions."""

    @staticmethod
    async def verify_app_launch(
        app_name: str,
        canonical: str = "",
        process_hints: Optional[List[str]] = None,
        timeout: float = 5.0,
    ) -> Dict[str, Any]:
        """Verify that an application launch actually resulted in a visible, usable desktop window."""
        if sys.platform != "win32":
            return {
                "success": True,
                "status": ActionResultStatus.EXECUTED_UNVERIFIED.value,
                "message": f"Launch command sent for {app_name} (platform verification not available).",
                "verification": {"platform": sys.platform}
            }

        hints = [app_name.lower()]
        if canonical:
            hints.append(canonical.lower())
        if process_hints:
            hints.extend([p.lower() for p in process_hints])
        cleaned_hints = []
        for h in hints:
            cleaned = h[:-4] if h.endswith(".exe") else h
            if cleaned and cleaned not in cleaned_hints:
                cleaned_hints.append(cleaned)

        def check_window_appeared() -> Optional[Dict[str, Any]]:
            for hint in cleaned_hints:
                matches = find_visible_windows_for_process(hint)
                viable = [w for w in matches if w["title"]]
                if viable:
                    for w in viable:
                        if w["is_foreground"]:
                            return w
                    return viable[0]
            return None

        success, win_info = await wait_for_condition_async(
            check_window_appeared,
            timeout=timeout,
            poll_interval=0.25,
            initial_wait=0.3,
        )

        if success and win_info:
            hwnd = win_info["hwnd"]
            bring_window_to_foreground(hwnd)
            is_fg = is_window_foreground(hwnd)
            title = win_info.get("title", app_name)

            return {
                "success": True,
                "status": ActionResultStatus.VERIFIED.value,
                "message": f"{app_name.capitalize()} is open and visible.",
                "verification": {
                    "hwnd": hwnd,
                    "title": title,
                    "process": win_info.get("process_name", ""),
                    "visible": True,
                    "foreground": is_fg,
                }
            }
        else:
            return {
                "success": False,
                "status": ActionResultStatus.TIMEOUT.value,
                "message": f"I couldn't open {app_name}. Windows did not produce a visible window within {int(timeout)} seconds.",
                "verification": {
                    "hints": cleaned_hints,
                    "timeout_seconds": timeout,
                    "window_found": False,
                }
            }

    @staticmethod
    async def verify_app_close(
        app_name: str,
        target_hwnds: List[int],
        timeout: float = 3.5,
    ) -> Dict[str, Any]:
        """Verify that target window handles actually closed and disappeared."""
        if not target_hwnds:
            return {
                "success": False,
                "status": ActionResultStatus.FAILED.value,
                "message": f"No open windows matching '{app_name}' were found to close.",
                "verification": {"target_hwnds": []}
            }

        def check_all_closed():
            for hwnd in target_hwnds:
                if user32 and user32.IsWindow(hwnd) and user32.IsWindowVisible(hwnd):
                    return False
            return True

        closed, _ = await wait_for_condition_async(
            check_all_closed,
            timeout=timeout,
            poll_interval=0.2,
            initial_wait=0.2,
        )

        if closed:
            return {
                "success": True,
                "status": ActionResultStatus.VERIFIED.value,
                "message": f"{app_name.capitalize()} closed.",
                "verification": {"closed_windows": len(target_hwnds)}
            }
        else:
            return {
                "success": False,
                "status": ActionResultStatus.FAILED.value,
                "message": f"{app_name.capitalize()} is still open. Windows did not close the application window.",
                "verification": {"remaining_windows": len(target_hwnds)}
            }

    @staticmethod
    async def verify_window_focus(hwnd: int, title: str, timeout: float = 2.0) -> Dict[str, Any]:
        """Verify that a window gained foreground focus."""
        bring_window_to_foreground(hwnd)

        def check_fg():
            return is_window_foreground(hwnd)

        focused, _ = await wait_for_condition_async(check_fg, timeout=timeout, poll_interval=0.1, initial_wait=0.05)

        if focused:
            return {
                "success": True,
                "status": ActionResultStatus.VERIFIED.value,
                "message": f"Switched to {title}.",
                "verification": {"hwnd": hwnd, "foreground": True}
            }
        else:
            return {
                "success": True,
                "status": ActionResultStatus.EXECUTED_UNVERIFIED.value,
                "message": f"Sent focus command to {title}, but foreground focus could not be confirmed.",
                "verification": {"hwnd": hwnd, "foreground": False}
            }

    @staticmethod
    async def verify_window_minimize(hwnd: int, title: str, timeout: float = 2.0) -> Dict[str, Any]:
        """Verify that a window is minimized."""
        if user32:
            user32.ShowWindow(hwnd, SW_MINIMIZE)

        def check_min():
            return is_window_minimized(hwnd)

        minimized, _ = await wait_for_condition_async(check_min, timeout=timeout, poll_interval=0.1, initial_wait=0.05)

        if minimized:
            return {
                "success": True,
                "status": ActionResultStatus.VERIFIED.value,
                "message": f"Minimized {title}.",
                "verification": {"hwnd": hwnd, "minimized": True}
            }
        else:
            return {
                "success": False,
                "status": ActionResultStatus.FAILED.value,
                "message": f"Could not minimize {title}.",
                "verification": {"hwnd": hwnd, "minimized": False}
            }

    @staticmethod
    async def verify_window_maximize(hwnd: int, title: str, timeout: float = 2.0) -> Dict[str, Any]:
        """Verify that a window is maximized."""
        if user32:
            user32.ShowWindow(hwnd, SW_MAXIMIZE)

        def check_max():
            return is_window_maximized(hwnd)

        maximized, _ = await wait_for_condition_async(check_max, timeout=timeout, poll_interval=0.1, initial_wait=0.05)

        if maximized:
            return {
                "success": True,
                "status": ActionResultStatus.VERIFIED.value,
                "message": f"Maximized {title}.",
                "verification": {"hwnd": hwnd, "maximized": True}
            }
        else:
            return {
                "success": False,
                "status": ActionResultStatus.FAILED.value,
                "message": f"Could not maximize {title}.",
                "verification": {"hwnd": hwnd, "maximized": False}
            }
