import unittest

from alpha_factory_v1.demos import validate_demos


class TestValidateDemos(unittest.TestCase):
    def test_all_demos_have_readme(self):
        self.assertEqual(validate_demos.main(), 0)


if __name__ == "__main__":
    unittest.main()
