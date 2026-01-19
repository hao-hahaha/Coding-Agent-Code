# sandbox.py (pseudo-code)
import subprocess


def run_in_docker(image: str, repo_dir: str, command: str) -> tuple[int, str]:
    """Run a command inside a Docker container mounted with the repo_dir."""
    cmd = ["docker", "run", "--rm", "-v", f"{repo_dir}:/app", "-w", "/app", image] + command.split()
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr
