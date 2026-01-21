import asyncio
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents import safety_agent
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config, messaging


class DummyBus:
    def __init__(self, settings: config.Settings) -> None:
        self.settings = settings
        self.published: list[tuple[str, messaging.Envelope]] = []

    def publish(self, topic: str, env: messaging.Envelope) -> None:
        self.published.append((topic, env))

    def subscribe(self, _t: str, _h) -> None:  # pragma: no cover - dummy
        pass


class DummyLedger:
    def __init__(self) -> None:
        self.logged: list[messaging.Envelope] = []

    def log(self, env: messaging.Envelope) -> None:  # type: ignore[override]
        self.logged.append(env)

    def start_merkle_task(self, *_a, **_kw) -> None:  # pragma: no cover - dummy
        pass

    async def stop_merkle_task(self) -> None:  # pragma: no cover - interface
        pass

    def close(self) -> None:  # pragma: no cover - dummy
        pass


def _make_agent() -> safety_agent.SafetyGuardianAgent:
    cfg = config.Settings(bus_port=0)
    bus = DummyBus(cfg)
    led = DummyLedger()
    return safety_agent.SafetyGuardianAgent(bus, led)


def test_blocks_insider_message() -> None:
    agent = _make_agent()
    env = messaging.Envelope(
        sender="market",
        recipient="safety",
        payload={"analysis": "buy AAPL tomorrow"},
        ts=0.0,
    )
    asyncio.run(agent.handle(env))
    assert agent.bus.published[-1][1].payload["status"] == "blocked"


def test_allows_normal_message() -> None:
    agent = _make_agent()
    env = messaging.Envelope(
        sender="market",
        recipient="safety",
        payload={"analysis": "hold position"},
        ts=0.0,
    )
    asyncio.run(agent.handle(env))
    assert agent.bus.published[-1][1].payload["status"] == "ok"
