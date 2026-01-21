import subprocess
import shutil
from pathlib import Path

import pytest

BROWSER_DIR = Path("alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1")

@pytest.mark.skipif(not shutil.which("npm"), reason="npm not available")
def test_pdf_copied_after_build(tmp_path: Path) -> None:
    dist = BROWSER_DIR / "dist"
    pdf = dist / "insight_browser_quickstart.pdf"
    if pdf.exists():
        pdf.unlink()
    result = subprocess.run([
        "npm",
        "run",
        "build",
    ], cwd=BROWSER_DIR, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert pdf.exists(), "insight_browser_quickstart.pdf missing in dist"

