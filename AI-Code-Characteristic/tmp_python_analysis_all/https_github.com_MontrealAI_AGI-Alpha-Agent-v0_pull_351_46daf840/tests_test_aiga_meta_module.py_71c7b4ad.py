import subprocess
import sys
import unittest

class TestAigaMetaModule(unittest.TestCase):
    def test_module_entrypoint(self) -> None:
        result = subprocess.run([
            sys.executable, '-m', 'alpha_factory_v1.demos.aiga_meta_evolution', '--help'
        ], capture_output=True, text=True, check=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage:', result.stdout.lower())

if __name__ == '__main__':
    unittest.main()
