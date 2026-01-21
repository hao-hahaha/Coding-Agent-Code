import unittest
from unittest.mock import patch

import alpha_factory_v1.backend.risk_management as rm


class TestRiskManagementCache(unittest.TestCase):
    def test_save_equity_cache_logs_error(self) -> None:
        with patch("pathlib.Path.write_text", side_effect=IOError("boom")) as mock_write:
            with patch.object(rm._LOG, "debug") as mock_log:
                rm._save_equity_cache([1.0, 2.0])
                mock_log.assert_called()
            mock_write.assert_called()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
