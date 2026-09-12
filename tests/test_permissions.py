"""Unit tests for Victor Permission Manager."""

import pytest
from dexter.permissions.manager import (
    PermissionDecision,
    PermissionLevel,
    PermissionManager,
)


def test_permission_classification():
    pm = PermissionManager()
    assert pm.get_action_level("web_search") == PermissionLevel.SAFE
    assert pm.get_action_level("youtube.search") == PermissionLevel.SAFE
    assert pm.get_action_level("filesystem.read") == PermissionLevel.SAFE
    assert pm.get_action_level("filesystem.write") == PermissionLevel.REQUIRES_CONFIRMATION
    assert pm.get_action_level("computer.click") == PermissionLevel.REQUIRES_CONFIRMATION
    assert pm.get_action_level("shell.execute") == PermissionLevel.RESTRICTED


def test_permission_request_resolution():
    pm = PermissionManager()
    req = pm.create_request("computer.click", "Screen (500, 300)")
    assert req.status == "pending"

    pending = pm.get_pending_requests()
    assert len(pending) == 1
    assert pending[0]["id"] == req.id

    # Resolve with allow_once
    resolved = pm.resolve_request(req.id, PermissionDecision.ALLOW_ONCE)
    assert resolved is not None
    assert resolved.status == "allowed"
    assert len(pm.get_pending_requests()) == 0


def test_permission_always_allow():
    pm = PermissionManager()
    req = pm.create_request("filesystem.write", "output.txt")
    pm.resolve_request(req.id, PermissionDecision.ALWAYS_ALLOW)

    # Now filesystem.write should be considered permitted
    assert pm.is_action_permitted("filesystem.write") is True
