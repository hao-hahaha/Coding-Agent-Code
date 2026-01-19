#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Streamlit dashboard for the α‑AGI Insight demo."""
from __future__ import annotations

import json

from .insight_demo import DEFAULT_SECTORS, parse_sectors, run, verify_environment


def main() -> None:
    """Launch the Streamlit dashboard."""
    try:
        import streamlit as st
    except Exception as exc:  # pragma: no cover - optional dep
        raise SystemExit(
            "Streamlit is required for the dashboard. Install via `pip install streamlit`."
        ) from exc

    st.set_page_config(page_title="α‑AGI Insight Dashboard", page_icon="👁️")
    st.title("👁️ α‑AGI Insight — Beyond Human Foresight")

    st.sidebar.header("Configuration")

    episodes = st.sidebar.number_input("Episodes", min_value=1, max_value=50, value=5)
    exploration = st.sidebar.number_input(
        "Exploration", min_value=0.1, max_value=5.0, value=1.4, step=0.1
    )
    rewriter = st.sidebar.selectbox("Rewriter", ["random", "openai", "anthropic"], 0)
    target = st.sidebar.number_input("Target index", min_value=0, value=3)
    sectors_text = st.sidebar.text_area(
        "Sectors (comma separated)", ", ".join(DEFAULT_SECTORS)
    )
    seed = st.sidebar.number_input("Seed", value=0)
    model = st.sidebar.text_input("Model", value="gpt-4o")

    if st.sidebar.button("Run Search"):
        verify_environment()
        sectors = parse_sectors(None, sectors_text)
        result_json = run(
            episodes=episodes,
            exploration=exploration,
            rewriter=rewriter,
            target=target,
            seed=seed,
            model=model,
            sectors=sectors,
            json_output=True,
        )
        data = json.loads(result_json)
        st.subheader(f"Best sector: {data['best']} – score {data['score']:.3f}")
        if data.get("ranking"):
            sectors_r, scores = zip(*data["ranking"])
            st.bar_chart({"impact": scores}, x=sectors_r)


if __name__ == "__main__":  # pragma: no cover - streamlit
    main()
