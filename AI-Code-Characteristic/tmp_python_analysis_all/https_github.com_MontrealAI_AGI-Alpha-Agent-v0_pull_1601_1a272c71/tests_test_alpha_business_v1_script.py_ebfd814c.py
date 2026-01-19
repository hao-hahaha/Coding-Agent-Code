# SPDX-License-Identifier: Apache-2.0
import os
import py_compile
import unittest
from pathlib import Path

class TestAlphaBusinessV1Script(unittest.TestCase):
    def test_script_compiles(self) -> None:
        path = Path('alpha_factory_v1/demos/alpha_agi_business_v1/alpha_agi_business_v1.py')
        py_compile.compile(path, doraise=True)

    def test_launcher_compiles(self) -> None:
        path = Path('alpha_factory_v1/demos/alpha_agi_business_v1/run_business_v1_local.py')
        py_compile.compile(path, doraise=True)

    def test_helper_compiles(self) -> None:
        """Ensure the one-click helper launcher compiles."""
        path = Path('alpha_factory_v1/demos/alpha_agi_business_v1/start_alpha_business.py')
        py_compile.compile(path, doraise=True)

    def test_runtime_port_env(self) -> None:
        """--runtime-port propagates AGENTS_RUNTIME_PORT."""
        from unittest.mock import patch

        mod = __import__(
            'alpha_factory_v1.demos.alpha_agi_business_v1.run_business_v1_local',
            fromlist=['main']
        )

        captured = {}

        def fake_start_bridge(host: str, runtime_port: int) -> None:  # type: ignore
            captured['env'] = os.getenv('AGENTS_RUNTIME_PORT')
            captured['port'] = runtime_port

        with patch.object(mod, '_start_bridge', fake_start_bridge), \
             patch.object(mod, 'check_env'):  # type: ignore
            with patch('alpha_factory_v1.demos.alpha_agi_business_v1.alpha_agi_business_v1.main'):
                mod.main(['--bridge', '--runtime-port', '7001'])

        self.assertEqual(captured['port'], 7001)
        self.assertEqual(captured['env'], '7001')

if __name__ == '__main__':
    unittest.main()
