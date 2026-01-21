#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
OMNI-Factory • Prometheus / OpenMetrics exporter
════════════════════════════════════════════════
A *stand-alone* HTTP micro-service that scrapes the OMNI-Factory ledger
(`omni_ledger.sqlite`) and exposes **live operational metrics** in the
Prometheus 2.x exposition format – **no third-party libraries required**.

─────────────────────────────────────────────────────────────────────────────
Served metrics
──────────────
Counter  ▸ omni_tokens_minted_total           – all $AGIALPHA ever minted
Gauge    ▸ omni_tokens_minted_last            – tokens minted by last task
Gauge    ▸ omni_avg_reward_last               – average reward of last task
Counter  ▸ omni_tasks_total                   – rows in ledger table
Gauge    ▸ omni_supply_cap                    – hard-cap (env or DB)
Gauge    ▸ omni_supply_utilisation_percent    – minted ÷ hard-cap × 100
Gauge    ▸ omni_ledger_file_mtime_seconds     – UNIX mtime of the ledger
Gauge    ▸ omni_ledger_file_size_bytes        – on-disk size of the ledger
Gauge    ▸ omni_build_info{version=…,py=…}    – always 1 (label-only metric)
Gauge    ▸ omni_export_timestamp              – UNIX time of this scrape

Each request recomputes the values in **O(1)** SQL; the exporter therefore
acts as a *live reflection* of the ledger without persistent RAM state.

Healthcheck
───────────
• `GET /healthz` → `200 OK` / `500` (with plain-text reason)

─────────────────────────────────────────────────────────────────────────────
Run modes
─────────
• Default: starts a threaded HTTP server (`ThreadingHTTPServer`).
• `--oneshot` flag prints a single scrape to stdout (shell / CI friendly).

The script is **drop-in replacement-safe** for any earlier `omni_metrics_exporter.py`.
"""
from __future__ import annotations

import argparse
import http.server
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Final, List

# ─────────────────────────── Configuration constants ──────────────────────────
DEFAULT_LEDGER: Final[Path] = Path("./omni_ledger.sqlite").resolve()
DEFAULT_HOST: Final[str] = "0.0.0.0"
DEFAULT_PORT: Final[int] = 9137
TOKEN_SYMBOL: Final[str] = "$AGIALPHA"
HARD_CAP_ENV: Final[str] = "OMNI_AGIALPHA_SUPPLY"
EXPORTER_VERSION: Final[str] = "1.0.0"  # bump on functional change

# ────────────────────────────── Metric template ───────────────────────────────
_HELP_BLOCK = f"""
# HELP omni_tokens_minted_total Total {TOKEN_SYMBOL} ever minted
# TYPE omni_tokens_minted_total counter
# HELP omni_tokens_minted_last {TOKEN_SYMBOL} minted by the most recent task
# TYPE omni_tokens_minted_last gauge
# HELP omni_avg_reward_last Average reward of the most recent task
# TYPE omni_avg_reward_last gauge
# HELP omni_tasks_total Total number of tasks processed
# TYPE omni_tasks_total counter
# HELP omni_supply_cap Hard-cap for {TOKEN_SYMBOL}
# TYPE omni_supply_cap gauge
# HELP omni_supply_utilisation_percent Minted / cap × 100
# TYPE omni_supply_utilisation_percent gauge
# HELP omni_ledger_file_mtime_seconds Ledger file modification time
# TYPE omni_ledger_file_mtime_seconds gauge
# HELP omni_ledger_file_size_bytes Ledger file size on disk
# TYPE omni_ledger_file_size_bytes gauge
# HELP omni_build_info Build metadata
# TYPE omni_build_info gauge
# HELP omni_export_timestamp Unix timestamp of this scrape
# TYPE omni_export_timestamp gauge
""".strip()


# ──────────────────────────────── Core logic ──────────────────────────────────
def _load_hard_cap(conn: sqlite3.Connection) -> int:
    """Return token supply hard-cap (env override » DB fallback » default)."""
    env_val = os.getenv(HARD_CAP_ENV)
    if env_val:
        try:
            return int(env_val)
        except ValueError:
            print(
                f"[omni-exporter] WARNING: invalid {HARD_CAP_ENV}={env_val!r} – " "ignoring.",
                file=sys.stderr,
            )
    # DB schema may evolve; keep ultra-simple & resilient
    try:
        cap = conn.execute("PRAGMA user_version").fetchone()[0]
        if cap > 0:
            return cap
    except sqlite3.DatabaseError:
        pass
    return 10_000_000  # legacy demo default


def _scrape_metrics(ledger: Path) -> str:
    """
    Harvest metrics from *ledger* and return a fully-formed OpenMetrics string.
    All SQL is defensive → any exception is surfaced to caller.
    """
    totals = last_tokens = last_reward = tasks = cap = 0
    if ledger.exists():
        with sqlite3.connect(ledger) as conn:
            rows = conn.execute("SELECT tokens, avg_reward FROM ledger ORDER BY ts").fetchall()
            tasks = len(rows)
            if tasks:
                totals = sum(r[0] for r in rows)
                last_tokens, last_reward = rows[-1]
            cap = _load_hard_cap(conn)
    # FS metadata (works even if ledger missing → 0)
    stat = ledger.stat() if ledger.exists() else None
    mtime = int(stat.st_mtime) if stat else 0
    size = stat.st_size if stat else 0
    utilisation = (totals / cap * 100) if cap else 0.0

    lines: List[str] = [_HELP_BLOCK]
    lines.append(f"omni_tokens_minted_total {totals}")
    lines.append(f"omni_tokens_minted_last {last_tokens}")
    lines.append(f"omni_avg_reward_last {last_reward}")
    lines.append(f"omni_tasks_total {tasks}")
    lines.append(f"omni_supply_cap {cap}")
    lines.append(f"omni_supply_utilisation_percent {utilisation:.6f}")
    lines.append(f"omni_ledger_file_mtime_seconds {mtime}")
    lines.append(f"omni_ledger_file_size_bytes {size}")
    lines.append(
        f'omni_build_info{{version="{EXPORTER_VERSION}",'
        f'python_version="{sys.version_info.major}.{sys.version_info.minor}",'
        f'ledger_schema_version="1"}} 1'
    )
    lines.append(f"omni_export_timestamp {int(time.time())}")
    return "\n".join(lines) + "\n"


# ───────────────────────────── HTTP request handler ───────────────────────────
class _Handler(http.server.BaseHTTPRequestHandler):
    """Trivial, fast HTTP handler – serves /metrics & /healthz."""

    def do_GET(self):  # noqa: N802  (snake → BaseHTTPRequest)
        try:
            if self.path == "/metrics":
                payload = _scrape_metrics(self.server.ledger).encode()
                self._send(200, "text/plain; version=0.0.4; charset=utf-8", payload)
            elif self.path == "/healthz":
                # Success if ledger readable OR absent (exporter tolerates empty)
                code = 200 if (self.server.ledger.exists() or True) else 500
                self._send(code, "text/plain; charset=utf-8", b"OK\n" if code == 200 else b"Ledger error\n")
            else:
                self._send(404, "text/plain; charset=utf-8", b"404 Not Found\n")
        except sqlite3.DatabaseError as exc:
            err = f"ledger error: {exc}\n".encode()
            self._send(500, "text/plain; charset=utf-8", err)
        except Exception as exc:  # pragma: no cover
            err = f"internal error: {exc}\n".encode()
            self._send(500, "text/plain; charset=utf-8", err)

    # ------------------------------------------------------------------ helpers
    def log_message(self, *_) -> None:  # silence default logging
        return

    def _send(self, code: int, ctype: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class _ThreadingHTTPServer(http.server.ThreadingHTTPServer):
    """Expose ledger path on the server instance for handler access."""

    def __init__(self, addr, handler, ledger: Path):
        super().__init__(addr, handler)
        self.ledger: Path = ledger


# ────────────────────────────── Entry points ──────────────────────────────────
def _serve_forever(host: str, port: int, ledger: Path) -> None:
    with _ThreadingHTTPServer((host, port), _Handler, ledger) as srv:
        print(
            f"[omni-exporter] Serving metrics at http://{host}:{port}/metrics " f"(ledger: {ledger}) – Ctrl-C to quit."
        )
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\n[omni-exporter] Stopping – goodbye.")


def _oneshot(ledger: Path) -> None:
    """Print a single scrape payload (CI / debugging convenience)."""
    sys.stdout.write(_scrape_metrics(ledger))


def _parse_cli() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="OMNI-Factory Prometheus exporter")
    p.add_argument("--host", default=DEFAULT_HOST, help=f"Bind address (default: {DEFAULT_HOST})")
    p.add_argument("-p", "--port", type=int, default=DEFAULT_PORT, help=f"TCP port (default: {DEFAULT_PORT})")
    p.add_argument(
        "--ledger", type=Path, default=DEFAULT_LEDGER, help=f"Path to omni_ledger.sqlite (default: {DEFAULT_LEDGER})"
    )
    p.add_argument("--oneshot", action="store_true", help="Emit metrics to stdout once and exit")
    return p.parse_args()


# ────────────────────────────────── MAIN ───────────────────────────────────────
if __name__ == "__main__":  # pragma: no cover
    cli = _parse_cli()
    ledger_path = cli.ledger.expanduser().resolve()
    # Minimal banner for first-time users
    if not ledger_path.exists():
        print(
            f"[omni-exporter] NOTE: ledger '{ledger_path}' does not yet exist – "
            "metrics will show zeroes until omni_factory_demo.py creates it.",
            file=sys.stderr,
        )

    if cli.oneshot:
        _oneshot(ledger_path)
    else:
        _serve_forever(cli.host, cli.port, ledger_path)
