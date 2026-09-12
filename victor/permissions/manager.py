"""Permission management and human-in-the-loop confirmation subsystem for Victor."""

import enum
import uuid
import time
from typing import Any, Dict, List, Optional


class PermissionLevel(str, enum.Enum):
    SAFE = "safe"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    RESTRICTED = "restricted"


class PermissionDecision(str, enum.Enum):
    ALLOW_ONCE = "allow_once"
    ALWAYS_ALLOW = "always_allow"
    DENY = "deny"


class PermissionRequest:
    """Represents a pending permission prompt for a sensitive action."""

    def __init__(
        self,
        action: str,
        target: str,
        details: Optional[Dict[str, Any]] = None,
        level: PermissionLevel = PermissionLevel.REQUIRES_CONFIRMATION,
    ):
        self.id = str(uuid.uuid4())[:8]
        self.action = action
        self.target = target
        self.details = details or {}
        self.level = level
        self.created_at = time.time()
        self.status = "pending"  # pending, allowed, denied
        self.decision: Optional[PermissionDecision] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "action": self.action,
            "target": self.target,
            "details": self.details,
            "level": self.level.value,
            "created_at": self.created_at,
            "status": self.status,
            "decision": self.decision.value if self.decision else None,
        }


class PermissionManager:
    """Classifies actions and manages human confirmation approvals."""

    # Categorization of standard agent actions
    ACTION_POLICIES: Dict[str, PermissionLevel] = {
        "web_search": PermissionLevel.SAFE,
        "browser.read": PermissionLevel.SAFE,
        "youtube.search": PermissionLevel.SAFE,
        "calculator": PermissionLevel.SAFE,
        "filesystem.read": PermissionLevel.SAFE,
        "filesystem.list": PermissionLevel.SAFE,
        "applications.list": PermissionLevel.SAFE,
        "applications.open": PermissionLevel.SAFE,
        "notifications.send": PermissionLevel.SAFE,
        "web_fetch": PermissionLevel.SAFE,
        "process.list": PermissionLevel.SAFE,
        "process.status": PermissionLevel.SAFE,

        # Requires confirmation
        "filesystem.write": PermissionLevel.REQUIRES_CONFIRMATION,
        "filesystem.delete": PermissionLevel.REQUIRES_CONFIRMATION,
        "filesystem.edit": PermissionLevel.REQUIRES_CONFIRMATION,
        "filesystem.append": PermissionLevel.REQUIRES_CONFIRMATION,
        "process.kill": PermissionLevel.REQUIRES_CONFIRMATION,
        "computer.click": PermissionLevel.REQUIRES_CONFIRMATION,
        "computer.type": PermissionLevel.REQUIRES_CONFIRMATION,
        "computer.hotkey": PermissionLevel.REQUIRES_CONFIRMATION,
        "computer.scroll": PermissionLevel.REQUIRES_CONFIRMATION,
        "keyboard.type_text": PermissionLevel.REQUIRES_CONFIRMATION,
        "keyboard.press_key": PermissionLevel.REQUIRES_CONFIRMATION,
        "keyboard.hotkey": PermissionLevel.REQUIRES_CONFIRMATION,
        "window_manager.list_windows": PermissionLevel.SAFE,
        "window_manager.focus_window": PermissionLevel.SAFE,
        "window_manager.minimize": PermissionLevel.SAFE,
        "window_manager.maximize": PermissionLevel.SAFE,
        "window_manager.close_window": PermissionLevel.REQUIRES_CONFIRMATION,
        "screen_observer.observe_screen": PermissionLevel.SAFE,
        "screen_observer.find_element": PermissionLevel.SAFE,
        "screen_observer.take_screenshot": PermissionLevel.SAFE,
        "filesystem.search_files": PermissionLevel.SAFE,
        "filesystem.list_directory": PermissionLevel.SAFE,
        "filesystem.open_file": PermissionLevel.SAFE,
        "filesystem.create_folder": PermissionLevel.REQUIRES_CONFIRMATION,
        "applications.close": PermissionLevel.REQUIRES_CONFIRMATION,

        # Controlled / Restricted
        "exec.execute": PermissionLevel.RESTRICTED,
        "shell.execute": PermissionLevel.RESTRICTED,
        "system.shutdown": PermissionLevel.RESTRICTED,
    }

    def __init__(self):
        self.pending_requests: Dict[str, PermissionRequest] = {}
        self.always_allowed_actions: set[str] = set()

    def get_action_level(self, action: str) -> PermissionLevel:
        """Return the security level for a specific capability."""
        if action in self.always_allowed_actions:
            return PermissionLevel.SAFE
        return self.ACTION_POLICIES.get(action, PermissionLevel.REQUIRES_CONFIRMATION)

    def create_request(self, action: str, target: str, details: Optional[Dict[str, Any]] = None) -> PermissionRequest:
        """Register a new human confirmation request."""
        level = self.get_action_level(action)
        req = PermissionRequest(action=action, target=target, details=details, level=level)
        self.pending_requests[req.id] = req
        return req

    def resolve_request(self, request_id: str, decision: PermissionDecision) -> Optional[PermissionRequest]:
        """Resolve a pending permission prompt."""
        req = self.pending_requests.get(request_id)
        if not req:
            return None

        req.decision = decision
        if decision == PermissionDecision.ALLOW_ONCE:
            req.status = "allowed"
        elif decision == PermissionDecision.ALWAYS_ALLOW:
            req.status = "allowed"
            self.always_allowed_actions.add(req.action)
        else:
            req.status = "denied"

        return req

    def get_pending_requests(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self.pending_requests.values() if r.status == "pending"]

    def is_action_permitted(self, action: str) -> bool:
        """Check if an action is pre-authorized or safe without prompting."""
        level = self.get_action_level(action)
        return level == PermissionLevel.SAFE or action in self.always_allowed_actions
