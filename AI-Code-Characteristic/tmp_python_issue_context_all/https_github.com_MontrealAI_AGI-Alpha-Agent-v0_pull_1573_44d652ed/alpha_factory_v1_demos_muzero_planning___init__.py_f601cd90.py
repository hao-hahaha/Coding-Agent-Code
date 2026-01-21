"""MiniMu demo package for MuZero Planning."""

try:
    from .agent_muzero_entrypoint import launch_dashboard
except ImportError:  # pragma: no cover - optional deps may be missing

    def launch_dashboard() -> None:  # type: ignore[return-type]
        """Placeholder when optional dependencies are absent."""
        raise RuntimeError("gradio and other optional packages are required for the MuZero demo")


__all__ = ["launch_dashboard"]
