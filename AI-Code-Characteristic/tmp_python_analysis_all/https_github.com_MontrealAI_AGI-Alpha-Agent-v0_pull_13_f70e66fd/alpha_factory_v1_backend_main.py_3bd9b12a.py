from .orchestrator import Orchestrator

def main() -> None:
    """Run the Alpha‑Factory orchestrator indefinitely."""
    orch = Orchestrator()
    orch.run_forever()


if __name__ == "__main__":
    main()
