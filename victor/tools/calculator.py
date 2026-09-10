"""Safe Mathematical Calculator Tool for Victor."""

import ast
import math
import operator
from typing import Any, Dict
from victor.tools.base import BaseTool, PermissionLevel


class SafeCalculator:
    """Evaluates mathematical expressions safely using the Python AST."""

    _OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    _FUNCTIONS = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "abs": abs,
        "round": round,
        "floor": math.floor,
        "ceil": math.ceil,
        "pi": math.pi,
        "e": math.e,
    }

    @classmethod
    def evaluate(cls, expression: str) -> float:
        tree = ast.parse(expression, mode="eval")
        return cls._eval_node(tree.body)

    @classmethod
    def _eval_node(cls, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Unsupported constant type: {type(node.value)}")

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type in cls._OPERATORS:
                left = cls._eval_node(node.left)
                right = cls._eval_node(node.right)
                # prevent huge exponents that can hang CPU
                if op_type is ast.Pow and (right > 10000 or left > 10000):
                    raise ValueError("Exponent too large for safe evaluation.")
                return cls._OPERATORS[op_type](left, right)
            raise ValueError(f"Unsupported operator: {op_type}")

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type in cls._OPERATORS:
                operand = cls._eval_node(node.operand)
                return cls._OPERATORS[op_type](operand)
            raise ValueError(f"Unsupported unary operator: {op_type}")

        if isinstance(node, ast.Name):
            if node.id in cls._FUNCTIONS and isinstance(cls._FUNCTIONS[node.id], (int, float)):
                return cls._FUNCTIONS[node.id]
            raise ValueError(f"Unknown variable or constant: {node.id}")

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in cls._FUNCTIONS:
                func = cls._FUNCTIONS[node.func.id]
                args = [cls._eval_node(arg) for arg in node.args]
                return func(*args)
            raise ValueError(f"Unsupported function call in math expression: {getattr(node.func, 'id', 'unknown')}")

        raise ValueError(f"Unsupported expression element: {type(node).__name__}")


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Compute mathematical expressions safely (supports arithmetic, power, sqrt, sin, cos, log, etc.)."
    permission = PermissionLevel.SAFE
    slash_command = "/calc"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate, e.g. 'sqrt(144) + 15 * 2' or '2 ** 10'."
            }
        },
        "required": ["expression"]
    }

    async def run(self, expression: str = "", **kwargs: Any) -> Dict[str, Any]:
        expr = expression.strip()
        if not expr:
            raise ValueError("No expression provided to calculate.")
        
        # Support basic caret notation for exponent
        clean_expr = expr.replace("^", "**")
        result = SafeCalculator.evaluate(clean_expr)
        return {
            "expression": expr,
            "result": result,
            "formatted": f"{expr} = {result}"
        }
