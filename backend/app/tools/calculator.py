import ast
import operator
from typing import Any

from app.tools.base import Tool, ToolResult

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


class CalculatorTool(Tool):
    name = "calculator"
    description = "Evaluate a safe arithmetic expression such as '(12 * 7) / 3'. No variables or functions."
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The arithmetic expression to evaluate.",
            }
        },
        "required": ["expression"],
    }

    async def run(self, arguments: dict[str, Any]) -> ToolResult:
        expression = arguments["expression"]
        if len(expression) > 200:
            return ToolResult("Expression is too long.", success=False)
        try:
            value = _evaluate(expression)
        except (ValueError, ZeroDivisionError, OverflowError, SyntaxError):
            return ToolResult("The expression could not be evaluated safely.", success=False)
        return ToolResult(f"{expression} = {value}")


def _evaluate(expression: str) -> float | int:
    tree = ast.parse(expression, mode="eval")
    return _evaluate_node(tree.body)


def _evaluate_node(node: ast.AST) -> float | int:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)
        return _BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_evaluate_node(node.operand))
    raise ValueError("Unsupported expression node")
