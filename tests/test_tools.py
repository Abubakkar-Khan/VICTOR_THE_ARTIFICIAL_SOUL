"""Unit tests for Victor tools and tool registry."""

import pytest
from dexter.core.config import SecurityConfig
from dexter.tools.base import PermissionLevel
from dexter.tools.calculator import CalculatorTool
from dexter.tools.filesystem import FilesystemTool
from dexter.tools.registry import ToolRegistry
from dexter.tools.shell import ShellTool


@pytest.mark.asyncio
async def test_calculator_basic():
    tool = CalculatorTool()
    res = await tool.execute(expression="2 + 3 * 4")
    assert res.success is True
    assert res.output["result"] == 14


@pytest.mark.asyncio
async def test_calculator_functions():
    tool = CalculatorTool()
    res = await tool.execute(expression="sqrt(144) + sin(0)")
    assert res.success is True
    assert res.output["result"] == 12.0


@pytest.mark.asyncio
async def test_calculator_power_protection():
    tool = CalculatorTool()
    res = await tool.execute(expression="99999 ** 99999")
    assert res.success is False
    assert "Exponent too large" in str(res.output)


@pytest.mark.asyncio
async def test_tool_registry_permissions():
    security = SecurityConfig(allow_shell=False)
    registry = ToolRegistry(security_config=security)

    calc = CalculatorTool()
    shell = ShellTool()

    registry.register(calc)
    registry.register(shell)

    # Calculator is SAFE -> allowed
    calc_res = await registry.execute_tool("calculator", expression="10 / 2")
    assert calc_res.success is True
    assert calc_res.output["result"] == 5.0

    # Shell is DANGEROUS -> rejected when allow_shell=False
    shell_res = await registry.execute_tool("shell", command="echo test")
    assert shell_res.success is False
    assert "Permission denied" in shell_res.output


@pytest.mark.asyncio
async def test_filesystem_tool_boundary(tmp_path):
    # Create test file inside allowed root
    test_file = tmp_path / "hello.txt"
    test_file.write_text("Victor artificial mind test line 1\nLine 2\n", encoding="utf-8")

    tool = FilesystemTool(allowed_roots=[str(tmp_path)])
    res = await tool.execute(path=str(test_file))
    assert res.success is True
    assert "Victor artificial mind test line 1" in res.output["content"]
    assert res.output["total_lines"] == 2


@pytest.mark.asyncio
async def test_youtube_tool():
    from dexter.tools.youtube import YouTubeTool
    tool = YouTubeTool()
    res = await tool.execute(query="compiler construction beginner")
    assert res.success is True
    assert res.output["count"] >= 1
    assert "videos" in res.output
    assert len(res.output["videos"]) > 0


@pytest.mark.asyncio
async def test_applications_tool_list():
    from dexter.tools.applications import ApplicationTool
    tool = ApplicationTool()
    res = await tool.execute(action="list")
    assert res.success is True
    assert "applications" in res.output
    names = [a["name"] for a in res.output["applications"]]
    assert "notepad" in names or "terminal" in names or "chrome" in names


def test_applications_tool_resolve_binary():
    import sys
    from dexter.tools.applications import ApplicationTool
    tool = ApplicationTool()
    if sys.platform == "win32":
        # VS Code, Notepad, Explorer, Calculator should resolve on Windows
        assert tool._resolve_binary("notepad") is not None
        assert tool._resolve_binary("explorer") is not None
        assert tool._resolve_binary("vs code") is not None
        assert tool._resolve_binary("visual studio code") is not None
        assert tool._resolve_binary("code") is not None
        # Format display check
        from dexter.tools.base import ToolResult
        dummy_res = ToolResult(
            tool_name="applications",
            success=True,
            output={"action": "open", "application": "vs code", "status": "launched"}
        )
        msg = tool.format_display(dummy_res)
        assert "VS Code is now open" in msg



@pytest.mark.asyncio
async def test_computer_tool_info():
    from dexter.tools.computer import ComputerTool
    tool = ComputerTool()
    res = await tool.execute(action="screen_info")
    assert res.success is True
    assert res.output["screen_width"] > 0
    assert res.output["screen_height"] > 0


@pytest.mark.asyncio
async def test_notification_tool():
    from dexter.tools.notifications import NotificationTool
    tool = NotificationTool()
    res = await tool.execute(message="Unit test notification", title="Victor")
    assert res.success is True
    assert res.output["status"] == "delivered"


@pytest.mark.asyncio
async def test_keyboard_tool():
    from dexter.tools.keyboard import KeyboardTool
    tool = KeyboardTool()
    # Test unknown key
    err_res = await tool.execute(action="press_key", key="nonexistent_key_xyz")
    assert err_res.success is True
    assert err_res.output["status"] == "error"

    # Test format_display
    assert "Pressed key" in tool.format_display({"status": "success", "action": "press_key", "key": "enter"})
    assert "Typed" in tool.format_display({"status": "success", "action": "type_text", "typed": "hello"})


@pytest.mark.asyncio
async def test_window_manager_tool():
    from dexter.tools.window_manager import WindowManagerTool
    tool = WindowManagerTool()
    res = await tool.execute(action="list_windows")
    assert res.success is True
    assert "windows" in res.output
    assert isinstance(res.output["windows"], list)

    # Missing title returns error status
    focus_res = await tool.execute(action="focus_window", title="")
    assert focus_res.output["status"] == "error"


@pytest.mark.asyncio
async def test_screen_observer_tool():
    from dexter.tools.screen_observer import ScreenObserverTool
    tool = ScreenObserverTool()
    res = await tool.execute(action="observe_screen")
    assert res.success is True
    assert "tree" in res.output


@pytest.mark.asyncio
async def test_filesystem_search_and_list(tmp_path):
    from dexter.tools.filesystem import FilesystemTool
    (tmp_path / "test_doc1.txt").write_text("hello", encoding="utf-8")
    (tmp_path / "test_doc2.log").write_text("world", encoding="utf-8")
    sub = tmp_path / "subdir"
    sub.mkdir()

    tool = FilesystemTool(allowed_roots=[str(tmp_path)])
    
    # Test list_directory
    list_res = await tool.execute(action="list", path=str(tmp_path))
    assert list_res.success is True
    names = [c["name"] for c in list_res.output["contents"]]
    assert "test_doc1.txt" in names
    assert "subdir" in names

    # Test search_files
    search_res = await tool.execute(action="search", query="*.txt", locations=[str(tmp_path)])
    assert search_res.success is True
    assert len(search_res.output["results"]) >= 1
    assert "test_doc1.txt" in search_res.output["results"][0]["path"]


@pytest.mark.asyncio
async def test_tool_router_pc_intents():
    from dexter.tools.factory import create_tool_registry
    from dexter.tools.router import ToolRouter
    
    registry = create_tool_registry()
    router = ToolRouter(registry)

    # Test window manager routing
    w_match = router.route("list windows")
    assert w_match is not None
    assert w_match[0] == "window_manager"
    assert w_match[1]["action"] == "list_windows"

    # Test keyboard routing
    k_match = router.route("type hello world")
    assert k_match is not None
    assert k_match[0] == "keyboard"
    assert k_match[1]["action"] == "type_text"
    assert k_match[1]["text"] == "hello world"

    # Test screen observer routing
    s_match = router.route("observe screen")
    assert s_match is not None
    assert s_match[0] == "screen_observer"
    assert s_match[1]["action"] == "observe_screen"

    # Test application routing
    app_match = router.route("open vs code")
    assert app_match is not None
    assert app_match[0] == "applications"
    assert app_match[1]["action"] == "open"
    assert app_match[1]["app_name"] == "vs code"

    exp_match = router.route("open file explorer")
    assert exp_match is not None
    assert exp_match[0] == "applications"
    assert exp_match[1]["action"] == "open"
    assert exp_match[1]["app_name"] == "file explorer"

    # Test search file routing
    f_match = router.route("search for files named report.pdf")
    assert f_match is not None
    assert f_match[0] == "filesystem"
    assert f_match[1]["action"] == "search"
    assert f_match[1]["query"] == "report.pdf"


@pytest.mark.asyncio
async def test_exec_tool_echo():
    from dexter.tools.shell import ExecTool
    tool = ExecTool()
    res = await tool.execute(command="echo OpenClaw-Test")
    assert res.success is True
    assert "OpenClaw-Test" in res.output["stdout"]
    assert res.output["exit_code"] == 0
    formatted = tool.format_display(res)
    assert "OpenClaw-Test" in formatted


@pytest.mark.asyncio
async def test_process_tool_list():
    from dexter.tools.process import ProcessTool
    tool = ProcessTool()
    res = await tool.execute(action="list")
    assert res.success is True
    assert res.output["action"] == "list"
    assert "processes" in res.output
    assert isinstance(res.output["processes"], list)


@pytest.mark.asyncio
async def test_process_tool_status():
    from dexter.tools.process import ProcessTool
    tool = ProcessTool()
    res = await tool.execute(action="status", target="nonexistent_process_xyz_12345")
    assert res.success is True
    assert res.output["running"] is False


@pytest.mark.asyncio
async def test_filesystem_tool_edit_and_append(tmp_path):
    from dexter.tools.filesystem import FilesystemTool
    f = tmp_path / "sample.txt"
    f.write_text("line one\nreplace_me_target\nline three\n", encoding="utf-8")

    tool = FilesystemTool(allowed_roots=[str(tmp_path)])

    # Test edit (find-and-replace)
    edit_res = await tool.execute(
        action="edit",
        path=str(f),
        old_text="replace_me_target",
        new_text="replaced_success"
    )
    assert edit_res.success is True
    assert edit_res.output["status"] == "edited"
    assert edit_res.output["replacements"] == 1
    assert "replaced_success" in f.read_text(encoding="utf-8")

    # Test append
    append_res = await tool.execute(
        action="append",
        path=str(f),
        content="appended_line_four\n"
    )
    assert append_res.success is True
    assert append_res.output["status"] == "appended"
    assert "appended_line_four" in f.read_text(encoding="utf-8")


def test_skill_manager_discovery(tmp_path):
    from dexter.skills.manager import SkillManager
    # Setup mock workspace skill
    skill_dir = tmp_path / "skills" / "test-skill"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        "---\n"
        "name: test-automation\n"
        "description: Automated testing skill for OpenClaw.\n"
        "---\n"
        "Step 1: Run pytest\n"
        "Step 2: Check coverage\n",
        encoding="utf-8"
    )

    manager = SkillManager(workspace_dir=str(tmp_path))
    skills = manager.list_skills()
    assert len(skills) >= 1
    skill = manager.get_skill("test-automation")
    assert skill is not None
    assert skill.name == "test-automation"
    assert "Automated testing" in skill.description
    assert "Step 1: Run pytest" in skill.instructions

    prompt = manager.get_prompt_injection()
    assert "Active Skills" in prompt
    assert "test-automation" in prompt


