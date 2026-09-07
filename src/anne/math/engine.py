"""Safe, deterministic arithmetic for ANNE.

The engine uses Python's AST only as a parser and permits a tiny whitelist of
operators. It uses Decimal so basic finance/engineering arithmetic does not
silently inherit binary floating-point surprises.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from decimal import Decimal, getcontext

getcontext().prec = 50


@dataclass(frozen=True)
class Calculation:
    expression: str
    value: Decimal
    method: str
    assumptions: tuple[str, ...] = ()


class MathEngine:
    """Evaluate bounded arithmetic without an LLM."""

    _binary = {
        ast.Add: lambda a, b: a + b,
        ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b,
        ast.Pow: lambda a, b: a ** b,
        ast.Mod: lambda a, b: a % b,
    }
    _unary = {ast.UAdd: lambda a: a, ast.USub: lambda a: -a}

    def _eval(self, node: ast.AST) -> Decimal:
        if isinstance(node, ast.Expression):
            return self._eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return Decimal(str(node.value))
        if isinstance(node, ast.UnaryOp) and type(node.op) in self._unary:
            return self._unary[type(node.op)](self._eval(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in self._binary:
            left, right = self._eval(node.left), self._eval(node.right)
            if isinstance(node.op, ast.Div) and right == 0:
                raise ZeroDivisionError("division by zero")
            return self._binary[type(node.op)](left, right)
        raise ValueError("unsupported mathematical expression")

    def calculate(self, expression: str) -> Calculation:
        expression = expression.strip().replace("×", "*").replace("÷", "/")
        if not expression:
            raise ValueError("expression is required")
        tree = ast.parse(expression, mode="eval")
        value = self._eval(tree)
        return Calculation(expression, value, "deterministic_decimal_ast")

    def calculate_words(self, left: str, operator: str, right: str) -> Calculation:
        operators = {"artı": "+", "eksi": "-", "çarpı": "*", "bölü": "/"}
        op = operators.get(operator.lower())
        if op is None:
            raise ValueError(f"unsupported operator: {operator}")
        return self.calculate(f"{left} {op} {right}")


__all__ = ["Calculation", "MathEngine"]
