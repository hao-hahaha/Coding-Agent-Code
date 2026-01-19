# SPDX-License-Identifier: Apache-2.0
import ast
import unittest


# Copy of the safe eval logic from the deployment script


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Pow):
            return left**right
        raise ValueError("Unsupported operator")
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval_node(node.operand)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    raise ValueError("Unsupported expression")


def safe_eval(expression: str) -> float:
    tree = ast.parse(expression, mode="eval")
    allowed = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Constant,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.USub,
        ast.Load,
    )
    for n in ast.walk(tree):
        if not isinstance(n, allowed):
            raise ValueError("Unsupported expression")
    return _eval_node(tree.body)


class TestSafeEval(unittest.TestCase):
    def test_valid_expression(self) -> None:
        self.assertEqual(safe_eval("2 + 3 * 4 - 5"), 9)

    def test_reject_call(self) -> None:
        with self.assertRaises(ValueError):
            safe_eval("__import__('os').system('echo hi')")

    def test_reject_attribute(self) -> None:
        with self.assertRaises(ValueError):
            safe_eval("1 .__class__")

    def test_reject_subscript(self) -> None:
        with self.assertRaises(ValueError):
            safe_eval("[1, 2][0]")


if __name__ == "__main__":
    unittest.main()
