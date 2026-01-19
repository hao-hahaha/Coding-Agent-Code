# SPDX-License-Identifier: Apache-2.0
"""
omni_dashboard.py
════════════════════════════════════════════════════════════════════
Interactive, self-hosted dashboard for the OMNI-Factory demo
(Alpha-Factory v1 • Multi-Agent AGENTIC α-AGI).

Highlights
──────────
• **Live** charts (cumulative $AGIALPHA supply, daily mint rate, avg-reward).
• **Instant** stats panel (entries, utilisation -vs- hard-cap, reward mean…).
• **Responsive** table of recent ledger events (sortable, scrollable).
• **Zero-config** – point at any SQLite ledger via LEDGER_PATH env var or
  `--ledger` CLI flag. Works fully offline; only needs `dash` + `pandas`
  (+ optional `dash-bootstrap-components` for a sleeker theme).

Launch
──────
    python omni_dashboard.py                   # auto-opens browser
    python omni_dashboard.py --ledger ./custom.sqlite --port 8060

The script never writes to the ledger – safe for production mirroring.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

# ── Configuration ────────────────────────────────────────────────────────────
DEFAULT_LEDGER = Path(os.getenv("LEDGER_PATH", "./omni_ledger.sqlite")).expanduser()
POLL_INTERVAL_SEC = float(os.getenv("DASH_REFRESH", "2"))  # UI refresh cadence
TOKEN_SYMBOL = "$AGIALPHA"
HARD_CAP_ENV = "OMNI_AGIALPHA_SUPPLY"  # keep in sync with ledger CLI
DEFAULT_HARD_CAP = 10_000_000

# ── Soft dependencies with graceful fallback ─────────────────────────────────
missing_pkgs = []
try:
    import pandas as pd
except ModuleNotFoundError:
    missing_pkgs.append("pandas")

try:
    import dash
    from dash import dcc, html, dash_table, Output, Input, State
except ModuleNotFoundError:
    missing_pkgs.append("dash")

# Optional but nice-to-have (Bootstrap styling)
try:
    import dash_bootstrap_components as dbc  # type: ignore

    _THEME = dbc.themes.CYBORG  # auto-dark-/light-aware
    _USE_BOOTSTRAP = True
except ModuleNotFoundError:  # fallback to bare Dash
    _USE_BOOTSTRAP = False
    _THEME = None  # type: ignore

if missing_pkgs:
    print(
        "[omni_dashboard] Missing required packages:\n  "
        + "\n  ".join(missing_pkgs)
        + "\nInstall with:\n    pip install "
        + " ".join(missing_pkgs + (["dash-bootstrap-components"] if _USE_BOOTSTRAP else [])),
        file=sys.stderr,
    )
    sys.exit(1)


# ── Data access layer ────────────────────────────────────────────────────────
@dataclass
class _Cache:
    df: "pd.DataFrame"
    stat: Tuple[int, int]  # (st_mtime_ns, st_size)


_CACHE: Dict[Path, _Cache] = {}


def _load_ledger(ledger: Path) -> "pd.DataFrame":
    """
    Efficiently load or incremental-append ledger rows into an in-memory DataFrame.
    The cache key is the (mtime_ns, size) tuple – if unchanged, reuse DataFrame.
    """
    stat = ledger.stat() if ledger.exists() else None
    key = (stat.st_mtime_ns, stat.st_size) if stat else (-1, -1)  # pragma: no cover
    cached = _CACHE.get(ledger)
    if cached and cached.stat == key:
        return cached.df

    # Full reload (handles truncate / first load / append)
    if not ledger.exists():
        df = pd.DataFrame(columns=["ts", "scenario", "tokens", "avg_reward"])
    else:
        with sqlite3.connect(ledger) as conn:
            df = pd.read_sql_query(
                "SELECT ts, scenario, tokens, avg_reward FROM ledger ORDER BY ts",
                conn,
            )

    df["ts"] = pd.to_datetime(df["ts"], unit="s", utc=True)
    _CACHE[ledger] = _Cache(df=df, stat=key)
    return df


def _hard_cap() -> int:
    """Hard-cap from env or default."""
    env = os.getenv(HARD_CAP_ENV)
    return int(env) if env and env.isdigit() else DEFAULT_HARD_CAP


# ── Dash application factory ─────────────────────────────────────────────────
def _build_app(ledger: Path) -> "dash.Dash":
    external_stylesheets = [_THEME] if _USE_BOOTSTRAP else []
    app = dash.Dash(
        __name__,
        title="OMNI-Factory Dashboard",
        external_stylesheets=external_stylesheets,
        suppress_callback_exceptions=True,
    )

    def _metric_card(title: str, value_id: str) -> "dash.development.base_component.Component":
        body = html.Div(
            [
                html.H6(title, className="card-title", style={"marginBottom": "0.25rem"}),
                html.H4(id=value_id, className="card-text", style={"margin": 0}),
            ],
            style={"textAlign": "center"},
        )
        if _USE_BOOTSTRAP:
            return dbc.Card(body, className="m-1 p-2", color="dark", inverse=True)
        return html.Div(body, style={"border": "1px solid #444", "padding": "0.5rem", "margin": "0.25rem"})

    # ── Layout ────────────────────────────────────────────────────────────
    app.layout = (dbc.Container if _USE_BOOTSTRAP else html.Div)(  # type: ignore[assignment]
        fluid=True,
        children=[
            html.H2("🏙️ OMNI-Factory • Smart-City Resilience Dashboard", style={"textAlign": "center"}),
            dcc.Interval(id="tick", interval=POLL_INTERVAL_SEC * 1000, n_intervals=0),
            # Stats row
            (_USE_BOOTSTRAP and dbc.Row or html.Div)(  # type: ignore
                [
                    _metric_card("Entries", "m_entries"),
                    _metric_card(f"Total {TOKEN_SYMBOL}", "m_total"),
                    _metric_card("Utilisation", "m_util"),
                    _metric_card("Mean Reward", "m_reward"),
                ]
            ),
            # Charts
            dcc.Tabs(
                [
                    dcc.Tab(label="Cumulative Supply", children=[dcc.Graph(id="fig_cumulative")]),
                    dcc.Tab(label="Daily Mint Rate", children=[dcc.Graph(id="fig_daily")]),
                ]
            ),
            # Ledger table
            html.H4("Latest events"),
            dash_table.DataTable(
                id="table",
                page_size=12,
                sort_action="native",
                style_cell={"textAlign": "left", "whiteSpace": "normal"},
                style_table={"overflowX": "auto"},
            ),
            html.Footer("Ledger file: " + str(ledger), style={"marginTop": "1.5rem", "fontSize": "0.8em"}),
        ],
    )

    # ── Callbacks ────────────────────────────────────────────────────────
    @app.callback(
        Output("fig_cumulative", "figure"),
        Output("fig_daily", "figure"),
        Output("table", "data"),
        Output("table", "columns"),
        Output("m_entries", "children"),
        Output("m_total", "children"),
        Output("m_util", "children"),
        Output("m_reward", "children"),
        Input("tick", "n_intervals"),
        State("table", "page_current"),
    )
    def _update(_, _page_current):  # noqa: ANN001
        df = _load_ledger(ledger)
        if df.empty:
            empty_fig = {
                "layout": {
                    "xaxis": {"visible": False},
                    "yaxis": {"visible": False},
                    "annotations": [
                        {
                            "text": "No data yet",
                            "xref": "paper",
                            "yref": "paper",
                            "showarrow": False,
                            "font": {"size": 18},
                        }
                    ],
                }
            }
            return empty_fig, empty_fig, [], [], "0", "0", "0 %", "—"

        # Cumulative
        df_cum = df.copy()
        df_cum["cumulative"] = df_cum["tokens"].cumsum()
        fig_cum = {
            "data": [
                {
                    "x": df_cum["ts"],
                    "y": df_cum["cumulative"],
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": f"Cumulative {TOKEN_SYMBOL}",
                }
            ],
            "layout": {
                "margin": {"l": 50, "r": 20, "t": 20, "b": 40},
                "yaxis": {"title": TOKEN_SYMBOL},
                "xaxis": {"title": "Time"},
            },
        }

        # Daily mint rate (bar per calendar day UTC)
        df_daily = (
            df.set_index("ts")
            .groupby(pd.Grouper(freq="1D"))["tokens"]
            .sum()
            .reset_index()
            .rename(columns={"tokens": "daily_tokens"})
        )
        fig_daily = {
            "data": [
                {
                    "x": df_daily["ts"],
                    "y": df_daily["daily_tokens"],
                    "type": "bar",
                    "name": f"Daily {TOKEN_SYMBOL}",
                }
            ],
            "layout": {
                "margin": {"l": 50, "r": 20, "t": 20, "b": 40},
                "yaxis": {"title": TOKEN_SYMBOL},
                "xaxis": {"title": "Date"},
            },
        }

        # Table
        table_data = df.sort_values("ts", ascending=False).to_dict("records")
        table_cols = [{"name": c, "id": c} for c in df.columns]

        # Metrics
        entries = len(df)
        total = int(df["tokens"].sum())
        cap = _hard_cap()
        util_pct = f"{total / cap * 100:,.2f} %"
        reward_mean = f"{df['avg_reward'].mean():.3f}"

        return (
            fig_cum,
            fig_daily,
            table_data,
            table_cols,
            f"{entries:,}",
            f"{total:,}",
            util_pct,
            reward_mean,
        )

    return app


# ── Browser auto-open helper ────────────────────────────────────────────────
def _auto_open(url: str) -> None:
    def _open() -> None:  # pragma: no cover
        import webbrowser, socket

        # Wait until port is open (up to 3 s)
        host, port = url.replace("http://", "").split(":")
        port = int(port.split("/")[0])
        for _ in range(30):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex((host, port)) == 0:
                    break
            time.sleep(0.1)
        try:
            webbrowser.open(url, new=1, autoraise=True)
        except webbrowser.Error:
            pass

    threading.Thread(target=_open, daemon=True).start()


# ── CLI ─────────────────────────────────────────────────────────────────────
def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="OMNI-Factory live dashboard")
    p.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER, help="Path to omni_ledger.sqlite")
    p.add_argument("--host", default="127.0.0.1", help="HTTP bind address")
    p.add_argument("--port", type=int, default=8050, help="HTTP port")
    p.add_argument("--no-browser", action="store_true", help="Do not auto-open the default browser")
    return p.parse_args()


def main() -> None:  # pragma: no cover
    args = _parse_args()
    ledger_path: Path = args.ledger.expanduser().resolve()
    app = _build_app(ledger_path)

    url = f"http://{args.host}:{args.port}/"
    if not args.no_browser:
        _auto_open(url)

    print(f"[omni_dashboard] Serving at {url}  (ledger: {ledger_path})")
    try:
        app.run_server(host=args.host, port=args.port, debug=False)
    except KeyboardInterrupt:
        print("\n[omni_dashboard] Stopped – goodbye.")


if __name__ == "__main__":  # pragma: no cover
    main()
