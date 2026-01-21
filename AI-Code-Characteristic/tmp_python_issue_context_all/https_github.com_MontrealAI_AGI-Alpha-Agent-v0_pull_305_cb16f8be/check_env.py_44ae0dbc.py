import importlib.util
import subprocess
import os
import sys

REQUIRED = [
    "pytest",
    "prometheus_client",
]

def main() -> int:
    missing: list[str] = []
    for pkg in REQUIRED:
        if importlib.util.find_spec(pkg) is None:
            missing.append(pkg)
    if missing:
        print("WARNING: Missing packages:", ", ".join(missing))
        wheelhouse = os.getenv("WHEELHOUSE")
        auto = os.getenv("AUTO_INSTALL_MISSING") == "1"
        if auto:
            cmd = [sys.executable, "-m", "pip", "install"]
            if wheelhouse:
                cmd += ["--no-index", "--find-links", wheelhouse]
            cmd += missing
            print("Attempting automatic install:", " ".join(cmd))
            subprocess.call(cmd)
        else:
            hint = "pip install " + " ".join(missing)
            if wheelhouse:
                hint = f"pip install --no-index --find-links {wheelhouse} " + " ".join(missing)
            print("Some features may be degraded. Install with:", hint)
    else:
        print("Environment OK")
    return 0

if __name__ == '__main__':
    sys.exit(main())
