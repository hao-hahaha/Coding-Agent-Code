# alpha_factory_v1/demos/macro_sentinel/agent_macro_entrypoint.py
# © 2025 MONTREAL.AI Apache-2.0 License
"""
Macro-Sentinel entry-point
══════════════════════════
An Agentic pipeline that
1. ingests macro telemetry (offline CSV or live APIs),
2. Monte-Carlo-prices equity risk,
3. sizes a hedge,
4. explains its reasoning in prose.

OpenAI key present  → GPT-4o  
No key             → Mixtral via Ollama (offline)

Deploy via Docker (run_macro_demo.sh) or directly:
    python agent_macro_entrypoint.py
"""

from __future__ import annotations
import os, json, asyncio, contextlib
import pandas as pd, gradio as gr
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import uvicorn
from openai_agents import Agent, OpenAIAgent, Tool
from data_feeds import stream_macro_events
from simulation_core import MonteCarloSimulator

# ─────────────────────────── LLM bridge ─────────────────────────────
LLM = OpenAIAgent(
    model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
    api_key=os.getenv("OPENAI_API_KEY") or None,
    base_url=("http://ollama:11434/v1" if not os.getenv("OPENAI_API_KEY") else None),
    temperature=float(os.getenv("TEMPERATURE", 0.15))
)

# ─────────────────────────── Globals ────────────────────────────────
PORTFOLIO_USD = float(os.getenv("DEFAULT_PORTFOLIO_USD", "2000000"))
LIVE_FEED     = bool(int(os.getenv("LIVE_FEED", "0")))
simulator     = MonteCarloSimulator()
event_iter    = stream_macro_events(live=LIVE_FEED)   # async generator

# ─────────────────────────── Tools ──────────────────────────────────
@Tool("macro_event", "Stream the newest macro telemetry event.")
async def macro_event() -> dict:
    return await anext(event_iter)

@Tool("mc_risk", "Run Monte-Carlo risk. Returns hedge + scenario table.")
async def mc_risk(event: dict, portfolio: float = PORTFOLIO_USD) -> dict:
    factors = simulator.simulate(event)
    hedge   = simulator.hedge(factors, portfolio)
    scen    = simulator.scenario_table(factors).to_dict(orient="records")
    return {"hedge": hedge, "scenarios": scen}

@Tool("order_stub", "Draft a JSON order for Micro-ES future.")
async def order_stub(hedge: dict) -> dict:
    notional = hedge["es_notional"]
    side     = "SELL" if notional > 0 else "BUY"
    qty      = max(int(abs(notional)//50_000), 1)    # 50 k USD ≈ 1 MES
    return {"symbol": "MES", "qty": qty, "side": side, "type": "MKT"}

@Tool("explain", "Narrate risk & hedge for a PM.")
async def explain(event: dict, hedge: dict) -> str:
    prompt = (
        "You are a risk officer. In ~150 words, explain to a portfolio "
        "manager why the hedge below is sensible.\n\n"
        f"Event:\n```json\n{json.dumps(event, indent=2)}\n```\n"
        f"Hedge:\n```json\n{json.dumps(hedge, indent=2)}\n```"
    )
    return LLM(prompt)

# ─────────────────────────── Agent ──────────────────────────────────
sentinel = Agent(
    name  = "Macro-Sentinel",
    llm   = LLM,
    tools = [macro_event, mc_risk, order_stub, explain]
)

# Optionally expose via Google ADK (Agent-to-Agent federation)
try:  # pragma: no cover - optional dependency
    from alpha_factory_v1.backend import adk_bridge
    adk_bridge.auto_register([sentinel])
    adk_bridge.maybe_launch()
except Exception:
    pass

# ─────────────────────────── Gradio UI ──────────────────────────────
async def launch_ui() -> None:
    with gr.Blocks(title="Macro-Sentinel") as ui:
        gr.Markdown("## 📈 Macro-Sentinel — real-time macro risk radar")

        col1, col2 = gr.Row().children
        event_box   = gr.Json(label="Latest macro event", elem_id="evt")
        scen_df     = gr.Dataframe(label="Return scenarios (P50/P95/P99)")

        metrics_md  = gr.Markdown()
        story_md    = gr.Markdown()
        run_btn     = gr.Button("🔄 Run Sentinel Cycle")

        async def cycle():
            event   = await macro_event()
            risk    = await mc_risk(event, PORTFOLIO_USD)
            hedge   = risk["hedge"]
            story   = await explain(event, hedge)
            scen_df = pd.DataFrame(risk["scenarios"])

            metric = (f"**VaR 5 %:** {hedge['metrics']['var']:.2%} &nbsp;&nbsp;"
                      f"**CVaR 5 %:** {hedge['metrics']['cvar']:.2%} &nbsp;&nbsp;"
                      f"**Skew:** {hedge['metrics']['skew']:.2f}<br>"
                      f"**ES notional:** ${hedge['es_notional']:,.0f}  "
                      f"(Micro-ES qty ≈ {abs(int(hedge['es_notional']//50_000))})")

            return event, scen_df, metric, story

        run_btn.click(
            cycle,
            outputs=[event_box, scen_df, metrics_md, story_md]
        )

    fast = FastAPI()

    @fast.get("/healthz", response_class=PlainTextResponse, include_in_schema=False)
    async def _health() -> str:  # noqa: D401
        return "ok"

    gr_app = gr.mount_gradio_app(fast, ui, path="/")
    server = uvicorn.Server(
        uvicorn.Config(gr_app, host="0.0.0.0", port=7864, loop="asyncio")
    )
    await server.serve()

# ─────────────────────────── Main ───────────────────────────────────
if __name__ == "__main__":
    try:
        asyncio.run(launch_ui())
    finally:
        # tidy aiohttp session if running outside Docker
        from data_feeds import aiohttp, _SESSION
        if (s := _SESSION) and isinstance(s, aiohttp.ClientSession):
            with contextlib.suppress(Exception):
                asyncio.run(s.close())
