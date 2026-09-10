"""Unit tests for Victor tools and tool registry."""

import pytest
from victor.core.config import SecurityConfig
from victor.tools.base import PermissionLevel
from victor.tools.calculator import CalculatorTool
from victor.tools.filesystem import FilesystemTool
from victor.tools.registry import ToolRegistry
from victor.tools.shell import ShellTool


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
