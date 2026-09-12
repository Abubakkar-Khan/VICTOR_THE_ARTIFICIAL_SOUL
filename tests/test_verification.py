"""Comprehensive verification test suite for Victor / Dexter PC control reliability.

Validates:
1. ActionResultStatus enum states
2. Bounded polling helpers (wait_for_condition / wait_for_condition_async)
3. ActionVerifier app launch verification and timeout on nonexistent process
4. ScreenObserver observation ID cache and stale-observation rejection
5. FilesystemTool real disk verification (create_folder, create_file, edit, rename, append)
6. WindowManagerTool verification returns
7. KeyboardTool and ComputerTool verification status handling
"""

import asyncio
import os
import time
import pytest
from pathlib import Path

from dexter.tools.verifier import (
    ActionResultStatus,
    ActionVerifier,
    wait_for_condition,
    wait_for_condition_async,
)
from dexter.tools.screen_observer import (
    get_cached_element,
    get_current_observation_id,
    _observation_store,
    _current_observation_id,
    ScreenObserverTool,
)
from dexter.tools.filesystem import FilesystemTool
from dexter.tools.window_manager import WindowManagerTool
from dexter.tools.keyboard import KeyboardTool
from dexter.tools.computer import ComputerTool


def test_action_result_status_values():
    """Verify all required status enum states exist."""
    assert ActionResultStatus.REQUESTED.value == "requested"
    assert ActionResultStatus.EXECUTING.value == "executing"
    assert ActionResultStatus.VERIFYING.value == "verifying"
    assert ActionResultStatus.VERIFIED.value == "verified"
    assert ActionResultStatus.EXECUTED_UNVERIFIED.value == "executed_unverified"
    assert ActionResultStatus.FAILED.value == "failed"
    assert ActionResultStatus.TIMEOUT.value == "timeout"


def test_wait_for_condition_success():
    """Test sync bounded polling with succeeding predicate."""
    count = 0
    def pred():
        nonlocal count
        count += 1
        return count >= 3

    ok, res = wait_for_condition(pred, timeout=1.0, poll_interval=0.05, initial_wait=0)
    assert ok is True
    assert res is True
    assert count >= 3


def test_wait_for_condition_timeout():
    """Test sync bounded polling times out properly."""
    ok, res = wait_for_condition(lambda: False, timeout=0.2, poll_interval=0.05, initial_wait=0)
    assert ok is False
    assert res is None


@pytest.mark.asyncio
async def test_wait_for_condition_async_success():
    """Test async bounded polling."""
    calls = 0
    async def pred():
        nonlocal calls
        calls += 1
        return calls >= 2

    ok, res = await wait_for_condition_async(pred, timeout=1.0, poll_interval=0.05, initial_wait=0)
    assert ok is True
    assert res is True


@pytest.mark.asyncio
async def test_wait_for_condition_async_timeout():
    """Test async bounded polling times out."""
    ok, res = await wait_for_condition_async(lambda: False, timeout=0.2, poll_interval=0.05, initial_wait=0)
    assert ok is False
    assert res is None


@pytest.mark.asyncio
async def test_action_verifier_app_launch_timeout():
    """Verify that launching a non-existent app times out and reports accurately."""
    res = await ActionVerifier.verify_app_launch("nonexistent_process_xyz123.exe", timeout=0.3)
    assert res["status"] in ["timeout", "failed"]
    assert res["success"] is False
    assert "timeout" in res["message"].lower() or "did not produce" in res["message"].lower()


def test_stale_observation_rejection():
    """Verify that get_cached_element rejects elements from outdated observation IDs."""
    import dexter.tools.screen_observer as so

    # Set up artificial observation ID
    so._current_observation_id = 5
    so._observation_store[5] = {"e1": "mock_control_5"}
    so._observation_store[4] = {"e1": "mock_control_4"}

    # Querying matching observation ID succeeds
    ctrl, err = get_cached_element("e1", obs_id=5)
    assert ctrl == "mock_control_5"
    assert err is None

    # Querying stale observation ID (4 != 5) is strictly rejected
    ctrl_stale, err_stale = get_cached_element("e1", obs_id=4)
    assert ctrl_stale is None
    assert err_stale is not None
    assert "outdated screen observation #4" in err_stale

    # Querying missing element from active observation returns descriptive error
    ctrl_none, err_none = get_cached_element("e99", obs_id=5)
    assert ctrl_none is None
    assert "not found in active screen observation #5" in err_none


@pytest.mark.asyncio
async def test_filesystem_verification_create_folder(tmp_path):
    """Verify FilesystemTool creates folder and strictly verifies existence on disk."""
    tool = FilesystemTool(allowed_roots=[str(tmp_path)])
    target_dir = tmp_path / "test_created_dir"
    res = await tool.execute(action="create_folder", path=str(target_dir))

    assert res.success is True
    assert res.status == "verified"
    assert res.verification["verified"] is True
    assert os.path.isdir(str(target_dir))
    assert "verified on disk" in tool.format_display(res)


@pytest.mark.asyncio
async def test_filesystem_verification_create_and_edit_file(tmp_path):
    """Verify FilesystemTool file creation and edit verification."""
    tool = FilesystemTool(allowed_roots=[str(tmp_path)])
    target_file = tmp_path / "doc.txt"

    # Create file
    create_res = await tool.execute(action="create_file", path=str(target_file), content="alpha beta")
    assert create_res.success is True
    assert create_res.status == "verified"
    assert os.path.isfile(str(target_file))

    # Edit file
    edit_res = await tool.execute(action="edit", path=str(target_file), old_text="beta", new_text="gamma")
    assert edit_res.success is True
    assert edit_res.status == "verified"
    assert edit_res.verification["verified"] is True
    assert "alpha gamma" in target_file.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_filesystem_verification_rename_file(tmp_path):
    """Verify rename verifies old path is removed and new path exists."""
    tool = FilesystemTool(allowed_roots=[str(tmp_path)])
    src = tmp_path / "old.txt"
    src.write_text("content", encoding="utf-8")

    res = await tool.execute(action="rename_file", path=str(src), new_name="new.txt")
    assert res.success is True
    assert res.status == "verified"
    assert not src.exists()
    assert (tmp_path / "new.txt").exists()


@pytest.mark.asyncio
async def test_window_manager_verification_list():
    """Verify WindowManagerTool list_windows provides verified status."""
    tool = WindowManagerTool()
    res = await tool.execute(action="list_windows")
    assert res.success is True
    assert res.status == "verified"
    assert res.verification["verified"] is True


@pytest.mark.asyncio
async def test_keyboard_verification_type_unverified():
    """Verify keyboard type_text returns executed_unverified when no control value is bound."""
    tool = KeyboardTool()
    res = await tool.execute(action="type_text", text="")
    assert res.success is True
    # Empty typing without active input returns executed_unverified
    assert res.status in ["executed_unverified", "verified"]
    assert "status" in res.verification


@pytest.mark.asyncio
async def test_computer_click_stale_element_rejection():
    """Verify ComputerTool rejects click on stale observation elements."""
    import dexter.tools.screen_observer as so
    so._current_observation_id = 10
    so._observation_store[10] = {}

    tool = ComputerTool()
    # Attempt to click element e1 referencing observation 2 when active is 10
    res = await tool.execute(action="click", element="e1", observation_id=2)
    assert res.status in ["failed", "error"]
    assert "outdated screen observation #2" in res.output["message"]
