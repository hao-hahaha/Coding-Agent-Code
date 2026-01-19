import json
import logging
import random
import re
from typing import Any, Dict, List


_JSON_RE = re.compile(r"\{.*?\}", re.DOTALL)


def _extract_json(text: str) -> Dict[str, Any]:
    """Return the first JSON object found inside *text*."""
    match = _JSON_RE.search(text)
    if not match:
        raise ValueError("no JSON object found")
    return json.loads(match.group(0))

from .agent_base import AgentBase


class PlannerAgent(AgentBase):
    """LLM‑driven scheduler deciding which domain agent runs next.

    The planner queries an LLM for JSON instructions and gracefully falls back
    to heuristics when the response is malformed.  Every dispatch is persisted
    to :class:`~backend.memory.Memory` for auditability.  The chosen agent is
    executed asynchronously via its :py:meth:`run_cycle` method.
    """

    def __init__(self, *args, domain_agents, **kwargs):
        super().__init__(*args, **kwargs)
        self.domain_agents = list(domain_agents)
        self.log = logging.getLogger("PlannerAgent")

    # ──────────────────────────────────────────
    # Planner loop
    # ──────────────────────────────────────────
    def observe(self) -> List[Dict[str, Any]]:
        # No external observations yet (could ingest metrics later)
        return []

    def think(self, _obs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        agent_names = [a.name for a in self.domain_agents]
        prompt = (
            "You are the Planner.\n"
            f"Available agents: {', '.join(agent_names)}.\n"
            "Decide which agent to trigger next and why. "
            'Respond in JSON: {"agent":"<name>","reason":"<short explanation>"}'
        )

        # Ask the LLM; handle any backend / JSON issues gracefully
        try:
            resp = self.model.complete(prompt)
            data = _extract_json(resp)
            if data.get("agent") not in agent_names:
                raise ValueError("unknown agent")
        except Exception as err:  # pragma: no cover - planner safety net
            self.log.warning("Planner fallback due to %s", err)
            data = {
                "agent": random.choice(agent_names),
                "reason": "fallback (no LLM or invalid response)",
            }

        return [data]

    async def act(self, tasks: List[Dict[str, Any]]) -> None:
        """Execute the next agent's cycle based on *tasks*."""
        target_name = tasks[0]["agent"]
        target = next((a for a in self.domain_agents if a.name == target_name), None)
        if not target:
            self.log.warning("Planner chose unknown agent %s", target_name)
            return

        # Log the dispatch for auditability
        self.memory.write(self.name, "dispatch", tasks[0])

        # Run the selected agent's cycle
        await target.run_cycle()

