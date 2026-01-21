# SPDX-License-Identifier: Apache-2.0

"""
alpha_factory_v1.demos.meta_agentic_agi.ui.lineage_app
=====================================================================
Streamlit dashboard for **Meta-Agentic α-AGI** lineage tracking.

Key features
------------
• Zero-config launch – `streamlit run lineage_app.py` (or add to Procfile).  
• Works with *any* SQLite DB produced by `meta_agentic_agi_demo.py`.  
• Auto-refresh & reactive controls (no manual reloads).  
• Interactive Altair charts for **multi-objective** metrics.  
• Toggle code snippets, filter generations, export to CSV.  
• No external services, JS, or CSS – pure-Python + Streamlit.  

Copyright © 2025 MONTREAL.AI  |  Apache-2.0
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict

import altair as alt
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh  # pip install streamlit-autorefresh

# ────────────────────────────────────────────────────────────────────────────────
# 1. Configuration ─ env overrides make it portable & CI-friendly
# ────────────────────────────────────────────────────────────────────────────────
DB_ENV   = os.getenv("METAAGI_DB")              # custom DB path (optional)
REFRESH  = int(os.getenv("METAAGI_REFRESH", 5)) # seconds between polls
THEME    = os.getenv("METAAGI_THEME", "light")  # Streamlit theme override

DB_PATH = (
    Path(DB_ENV).expanduser().resolve()
    if DB_ENV else
    (Path(__file__).parent / ".." / "meta_agentic_agi_demo.sqlite").resolve()
)

# ────────────────────────────────────────────────────────────────────────────────
# 2. Low-level helpers
# ────────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def connect(db_path: Path) -> sqlite3.Connection:
    """Connect once per session; raise early if missing."""
    if not db_path.exists():
        raise FileNotFoundError(
            f"[lineage_app] SQLite database not found at: {db_path}\n"
            "‣ Make sure you have run `meta_agentic_agi_demo.py` at least once, or\n"
            "‣ Set METAAGI_DB env-var to the correct .sqlite path."
        )
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@st.cache_data(ttl=2, show_spinner=False)
def fetch_dataframe(conn: sqlite3.Connection) -> pd.DataFrame:
    """Load & denormalise lineage table → Pandas DataFrame."""
    df = pd.read_sql("SELECT * FROM lineage ORDER BY gen ASC", conn)
    if df.empty:
        return df

    # Flatten the JSON fitness column → individual metric columns
    metrics_df = pd.json_normalize(df["fitness"].apply(json.loads))
    metrics_df.columns = [c.split(".")[-1] for c in metrics_df.columns]

    return pd.concat([df.drop(columns=["fitness"]), metrics_df], axis=1)


def nice(name: str) -> str:
    """Human-friendly metric name."""
    return name.replace("_", " ").title()


# ────────────────────────────────────────────────────────────────────────────────
# 3. Streamlit page setup
# ────────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Lineage – Meta-Agentic α-AGI",
    layout="wide",
    page_icon="📊",
    theme={"base": THEME}
)

st.title("📊 Meta-Agentic α-AGI Lineage")
st.caption(
    f"Live DB → `{DB_PATH}` &nbsp;·&nbsp; auto-refresh every **{REFRESH}s** "
    "(change with env var `METAAGI_REFRESH`)."
)

# Auto-refresh (has no effect in static export)
st_autorefresh(interval=REFRESH * 1000, key="__refresh")

# DB connection
try:
    conn = connect(DB_PATH)
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

df = fetch_dataframe(conn)
if df.empty:
    st.info("⏳ Waiting for first generation… (run demo, then refresh)")
    st.stop()

# ────────────────────────────────────────────────────────────────────────────────
# 4. Sidebar – filters & options
# ────────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Controls")

    g_min, g_max = int(df["gen"].min()), int(df["gen"].max())
    gen_range = st.slider(
        "Generation range",
        min_value=g_min,
        max_value=g_max,
        value=(g_min, g_max),
        step=1,
        format="%d"
    )

    metric_cols = ["accuracy", "latency", "cost", "carbon", "novelty"]
    sel_metric = st.selectbox(
        "Metric to plot",
        metric_cols,
        index=0,
        format_func=nice,
    )

    show_code  = st.checkbox("Show code snippets", value=False)
    csv_button = st.download_button(
        "📥 Export filtered CSV",
        data=df.to_csv(index=False).encode(),
        file_name="meta_agentic_lineage.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.caption("© 2025 MONTREAL.AI  |  Apache-2.0")

# Apply generation filter
view_df = df.query("@gen_range[0] <= gen <= @gen_range[1]")

# ────────────────────────────────────────────────────────────────────────────────
# 5. Chart – interactive Altair
# ────────────────────────────────────────────────────────────────────────────────
chart = (
    alt.Chart(view_df)
    .mark_line(point=True, interpolate="monotone")
    .encode(
        x=alt.X("gen:Q", title="Generation"),
        y=alt.Y(f"{sel_metric}:Q", title=nice(sel_metric)),
        tooltip=["gen"] + metric_cols
    )
    .interactive()
)

st.altair_chart(chart, use_container_width=True)

# ────────────────────────────────────────────────────────────────────────────────
# 6. Data table
# ────────────────────────────────────────────────────────────────────────────────
st.subheader("📑 Lineage records")

code_col = [] if show_code else ["code"]
st.dataframe(
    view_df.sort_values("gen", ascending=False).drop(columns=code_col),
    use_container_width=True,
    height=450
)

# Optional code viewer
if show_code:
    st.subheader("🧩 Agent code (latest selected row)")
    latest_code: Dict[str, Any] = (
        view_df.sort_values("gen", ascending=False).iloc[0].to_dict()
    )
    st.code(latest_code["code"], language="python")
