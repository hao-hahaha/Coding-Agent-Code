#!/usr/bin/env python3
"""Simple Gradio dashboard for the Alpha‑AGI Business demo."""
from __future__ import annotations

import os
import requests
import gradio as gr

HOST = os.getenv("BUSINESS_HOST", "http://localhost:8000")
PORT = int(os.getenv("GRADIO_PORT", "7860"))


def _list_agents() -> list[str]:
    resp = requests.get(f"{HOST}/agents", timeout=5)
    resp.raise_for_status()
    return resp.json()


def _trigger(agent: str) -> str:
    resp = requests.post(f"{HOST}/agent/{agent}/trigger", timeout=5)
    resp.raise_for_status()
    return f"{agent} queued"


def _recent_alpha(limit: int = 5) -> list[dict]:
    resp = requests.get(
        f"{HOST}/memory/alpha_opportunity/recent", params={"n": limit}, timeout=5
    )
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    with gr.Blocks(title="Alpha‑AGI Business Dashboard") as ui:
        gr.Markdown("# Alpha‑AGI Business Dashboard")
        out = gr.JSON()
        with gr.Row():
            list_btn = gr.Button("List Agents")
            disc_btn = gr.Button("Trigger Discovery")
            opp_btn = gr.Button("Trigger Opportunity")
            exe_btn = gr.Button("Trigger Execution")
            risk_btn = gr.Button("Trigger Risk")
            alpha_btn = gr.Button("Recent Alpha")

        list_btn.click(_list_agents, outputs=out)
        disc_btn.click(lambda: _trigger("alpha_discovery"), outputs=out)
        opp_btn.click(lambda: _trigger("alpha_opportunity"), outputs=out)
        exe_btn.click(lambda: _trigger("alpha_execution"), outputs=out)
        risk_btn.click(lambda: _trigger("alpha_risk"), outputs=out)
        alpha_btn.click(_recent_alpha, outputs=out)

    ui.launch(server_name="0.0.0.0", server_port=PORT, share=False)


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
