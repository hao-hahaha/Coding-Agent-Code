# SPDX-License-Identifier: Apache-2.0
import unittest
import random

from src.simulation import SelfRewriteOperator


class TestSelfRewriteOperator(unittest.TestCase):
    def test_self_rewrite_happy_path(self) -> None:
        rng = random.Random(42)
        op = SelfRewriteOperator(steps=2, rng=rng)
        text = "improve quick test"
        result = op(text)
        self.assertEqual(result, "enhance quick trial")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
