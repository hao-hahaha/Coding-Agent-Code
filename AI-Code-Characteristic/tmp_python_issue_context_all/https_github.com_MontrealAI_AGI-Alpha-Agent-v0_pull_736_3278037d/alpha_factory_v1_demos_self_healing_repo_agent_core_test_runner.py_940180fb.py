# test_runner.py
import subprocess
import os


class BaseTestRunner:
    def __init__(self, repo_dir: str) -> None:
        self.repo_dir = repo_dir

    def run_tests(self) -> tuple[bool, str]:
        """Run tests and return (success, output)."""
        raise NotImplementedError

    def extract_failure_log(self, full_output: str) -> str:
        """Extract the relevant failure section from output (e.g., last traceback)."""
        # Default implementation: return last 50 lines if failure
        lines = full_output.strip().splitlines()
        return "\n".join(lines[-50:])  # last 50 lines as guess


class PytestRunner(BaseTestRunner):
    def run_tests(self) -> tuple[bool, str]:
        try:
            # Run pytest, capturing output
            result = subprocess.run(
                ["pytest", "-q", "--color=no"],  # quiet, no color codes
                cwd=self.repo_dir,
                check=True,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return (True, result.stdout + result.stderr)
        except subprocess.CalledProcessError as e:
            # Non-zero exit indicates test failures (or errors)
            output = e.stdout + e.stderr
            return (False, output)
        except subprocess.TimeoutExpired:
            return (False, "Test run timed out.")


def get_default_runner(repo_dir: str) -> BaseTestRunner:
    """Determine the appropriate test runner based on project files (pytest, npm, etc.)"""
    # Simple heuristic: if pytest available, use PytestRunner.
    # Could be extended to detect package.json for npm, pom.xml for Maven, etc.
    if os.path.exists(os.path.join(repo_dir, "pytest.ini")) or os.path.exists(os.path.join(repo_dir, "pyproject.toml")):
        return PytestRunner(repo_dir)
    # Future: other runner detections...
    return PytestRunner(repo_dir)
