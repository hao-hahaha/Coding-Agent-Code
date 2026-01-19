#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
omni_ledger_cli.py ─ $AGIALPHA ledger companion
════════════════════════════════════════════════
A **safe-by-default**, cross-platform CLI to inspect, verify or export
the OMNI-Factory ledger produced by *omni_factory_demo.py*.

Highlights
──────────
• Pure Python std-lib only, UTF-8 everywhere.
• Read-only unless a mutating sub-command **and** `--force` are used.
• Built-in integrity audit (sha256 checksums + hard-cap).
• Human-friendly, colourised tables (auto-disabled for pipes / NO_COLOR).

Full help → `python omni_ledger_cli.py -h`
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import islice
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

# Keep in sync with omni_factory_demo.py ────────────────────────────
DEFAULT_LEDGER = Path("./omni_ledger.sqlite").resolve()
TOKEN_SYMBOL = "$AGIALPHA"
HARD_CAP_ENV = "OMNI_AGIALPHA_SUPPLY"

# ════════════════════════════════════════════════════════════════════
# Tiny helpers: colour, time, checksum, DB I/O
# ════════════════════════════════════════════════════════════════════
_IS_TTY = sys.stdout.isatty() and os.getenv("NO_COLOR", "") == ""


class _Colour:
    """Minimal ANSI colour helper (disabled if not on a TTY)."""

    @staticmethod
    def _wrap(code: str, txt: str) -> str:
        return f"\x1b[{code}m{txt}\x1b[0m" if _IS_TTY else txt

    bold = classmethod(lambda cls, txt: cls._wrap("1", txt))
    green = classmethod(lambda cls, txt: cls._wrap("32", txt))
    red = classmethod(lambda cls, txt: cls._wrap("31", txt))
    yellow = classmethod(lambda cls, txt: cls._wrap("33", txt))


def _pretty_ts(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _checksum(ts: float, scen: str, tok: int, rew: float) -> str:
    """Deterministic 16-hex digest used as a cheap tamper tag."""
    payload = f"{ts}{scen}{tok}{rew}".encode()
    return hashlib.sha256(payload).hexdigest()[:16]


def _open_db(path: Path) -> sqlite3.Connection:
    if not path.exists():
        sys.exit(_Colour.red(f"Ledger not found: {path}"))
    return sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)


# Basic row type (ts, scenario, tokens, avg_reward, checksum)
Row = Tuple[float, str, int, float, str]


def _stream_rows(conn: sqlite3.Connection) -> Iterable[Row]:
    yield from conn.execute("SELECT ts, scenario, tokens, avg_reward, checksum FROM ledger ORDER BY ts")


def _load_hard_cap() -> int:
    """
    Return the global mint hard-cap, favouring the environment override.
    Accepts underscores for readability, e.g. 10_000_000.
    """
    env = os.getenv(HARD_CAP_ENV)
    if env:
        return int(env.replace("_", ""))
    # Ledger schema v1 stores no cap → fall back to demo default
    return 10_000_000


# ════════════════════════════════════════════════════════════════════
# Sub-commands
# ════════════════════════════════════════════════════════════════════
def cmd_list(args: argparse.Namespace) -> None:
    """List the most recent ledger rows (use --tail N, 0 = all)."""
    with _open_db(args.ledger) as conn:
        rows = list(_stream_rows(conn))

    if args.tail and args.tail > 0:
        rows = rows[-args.tail :]

    table = [(_pretty_ts(ts), scen[:60], f"{tok:,}", f"{rew:.3f}") for ts, scen, tok, rew, _ in rows]
    _print_table(
        ("Timestamp", "Scenario", TOKEN_SYMBOL, "AvgReward"),
        table or [("—", "ledger is empty", "—", "—")],
    )


def cmd_stats(args: argparse.Namespace) -> None:
    """Aggregate statistics: minted total, avg reward, utilisation …"""
    with _open_db(args.ledger) as conn:
        rows = list(_stream_rows(conn))

    if not rows:
        sys.exit("Ledger is empty.")

    tokens_total = sum(r[2] for r in rows)
    reward_mean = sum(r[3] for r in rows) / len(rows)
    first_ts, last_ts = rows[0][0], rows[-1][0]
    days = max((last_ts - first_ts) / 86_400, 1e-6)
    utilisation = tokens_total / _load_hard_cap() * 100

    print(_Colour.bold("Ledger statistics"))
    print(f"Entries          : {len(rows):,}")
    print(f"Total {TOKEN_SYMBOL:10}: {tokens_total:,} " f"({_Colour.yellow(f'{utilisation:.2f}%')} of hard-cap)")
    print(f"Average reward   : {reward_mean:.3f}")
    print(f"First entry      : {_pretty_ts(first_ts)}")
    print(f"Last entry       : {_pretty_ts(last_ts)}")
    print(f"{TOKEN_SYMBOL}/day     : {tokens_total / days:,.1f}")


def _determine_format(outfile: Path) -> str:
    ext = outfile.suffix.lower()
    if ext in (".csv", ".tsv"):
        return "csv"
    if ext in (".jsonl", ".json"):
        return "jsonl"
    sys.exit(_Colour.red("Use .csv, .tsv, .jsonl or .json for --outfile"))


def cmd_export(args: argparse.Namespace) -> None:
    """Dump the full ledger to CSV/TSV or JSONL (read-only)."""
    out: Path = args.outfile.expanduser().resolve()
    if out.exists():
        sys.exit(_Colour.red(f"Refusing to overwrite existing file: {out}"))
    with _open_db(args.ledger) as conn:
        rows = list(_stream_rows(conn))

    fmt = _determine_format(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "csv":
        delim = "\t" if out.suffix.lower() == ".tsv" else ","
        with out.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh, delimiter=delim)
            writer.writerow(("timestamp", "scenario", "tokens", "avg_reward"))
            for ts, scen, tok, rew, _ in rows:
                writer.writerow((ts, scen, tok, rew))
    else:  # jsonl / json
        with out.open("w", encoding="utf-8") as fh:
            for ts, scen, tok, rew, _ in rows:
                fh.write(
                    json.dumps(
                        {
                            "timestamp": ts,
                            "scenario": scen,
                            "tokens": tok,
                            "avg_reward": rew,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
    print(_Colour.green(f"Exported {len(rows):,} rows → {out}"))


def cmd_histogram(args: argparse.Namespace) -> None:
    """Quick ASCII bar-chart of daily $AGIALPHA minted."""
    with _open_db(args.ledger) as conn:
        rows = list(_stream_rows(conn))
    if not rows:
        sys.exit("Ledger is empty.")

    # Tokens per UTC day
    totals: dict[int, int] = defaultdict(int)
    for ts, _, tok, *_ in rows:
        totals[int(ts // 86_400)] += tok

    # Optional binning to reduce bar count
    if args.bins:
        min_day, max_day = min(totals), max(totals)
        span = max_day - min_day + 1
        bin_size = max(1, span // args.bins)
        merged = Counter()
        for day, tok in totals.items():
            merged[(day - min_day) // bin_size] += tok
        totals = merged  # type: ignore[assignment]

    max_tok = max(totals.values())
    width = 40
    for idx in sorted(totals):
        tok = totals[idx]
        bar = "█" * max(1, int(tok / max_tok * width))
        date = datetime.fromtimestamp((min(totals) + idx) * 86_400, tz=timezone.utc).strftime("%Y-%m-%d")
        print(f"{date} {bar} {tok:,}")


def cmd_supply(args: argparse.Namespace) -> None:
    """Print total minted vs hard-cap."""
    with _open_db(args.ledger) as conn:
        total = conn.execute("SELECT SUM(tokens) FROM ledger").fetchone()[0] or 0
    cap = _load_hard_cap()
    pct = total / cap * 100
    print(f"{TOKEN_SYMBOL} minted: {total:,} / {cap:,} ({pct:.2f}%)")


def cmd_verify(args: argparse.Namespace) -> None:
    """Full ledger audit (timestamp order, checksums, non-neg, hard-cap)."""
    with _open_db(args.ledger) as conn:
        cur = _stream_rows(conn)
        cap = _load_hard_cap()

        ok = True
        total = 0
        prev_ts = -math.inf

        for idx, (ts, scen, tok, rew, chk) in enumerate(cur, 1):
            if ts < prev_ts:
                print(_Colour.red(f"[row {idx}] timestamp disorder: {ts} < {prev_ts}"))
                ok = False
            prev_ts = ts

            if chk != _checksum(ts, scen, tok, rew):
                print(_Colour.red(f"[row {idx}] checksum mismatch ({_pretty_ts(ts)})"))
                ok = False

            if tok < 0:
                print(_Colour.red(f"[row {idx}] negative token amount: {tok}"))
                ok = False

            total += tok

        if total > cap:
            print(_Colour.red(f"Hard-cap exceeded: {total:,} > {cap:,} {TOKEN_SYMBOL}"))
            ok = False

    if ok:
        print(_Colour.green("Ledger verification ✓ – all checks passed."))
    else:
        sys.exit(2)


# ════════════════════════════════════════════════════════════════════
# Hidden self-test (CI / local sanity)
# ════════════════════════════════════════════════════════════════════
def _cmd_selftest(_: argparse.Namespace) -> None:
    """
    Build a temp ledger → verify passes → corrupt checksum → verify fails.
    Exits 0 on success, 1 on detection failure.
    """
    import tempfile

    tmp = Path(tempfile.mktemp(suffix=".sqlite"))
    try:
        with sqlite3.connect(tmp) as conn:
            conn.execute("CREATE TABLE ledger(ts REAL, scenario TEXT, tokens INT, " "avg_reward REAL, checksum TEXT)")
            ts = time.time()
            row = (ts, "unit-test", 100, 1.0, _checksum(ts, "unit-test", 100, 1.0))
            conn.execute("INSERT INTO ledger VALUES (?,?,?,?,?)", row)

        class _Args:
            ledger = tmp

        print(_Colour.yellow("• Positive path …"))
        cmd_verify(_Args)  # should not exit

        print(_Colour.yellow("• Negative path (corruption) …"))
        with sqlite3.connect(tmp) as conn:
            conn.execute("UPDATE ledger SET checksum='badhash'")

        try:
            cmd_verify(_Args)
        except SystemExit as exc:
            if exc.code == 2:
                print(_Colour.green("Self-test ✓"))
                return
        print(_Colour.red("Self-test ✗ – corruption went undetected"))
        sys.exit(1)
    finally:
        tmp.unlink(missing_ok=True)


# ════════════════════════════════════════════════════════════════════
# Argument-parsing boilerplate (single authoritative definition)
# ════════════════════════════════════════════════════════════════════
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="omni_ledger_cli",
        description=f"Inspect, verify or export the {TOKEN_SYMBOL} ledger.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER, help="Path to ledger DB")
    sub = p.add_subparsers(dest="command", required=True)

    def _cmd(name: str, func, help_: str, extra: list[tuple[str, dict]] | None = None):
        sp = sub.add_parser(name, help=help_)
        if extra:
            for flag, kwargs in extra:
                sp.add_argument(flag, **kwargs)
        sp.set_defaults(func=func)

    _cmd(
        "list",
        cmd_list,
        "List recent ledger rows",
        [("--tail", {"type": int, "default": 20, "help": "Lines to show (0 = all)"})],
    )
    _cmd("stats", cmd_stats, "Aggregate statistics")
    _cmd(
        "histogram",
        cmd_histogram,
        "ASCII histogram of minted tokens",
        [("--bins", {"type": int, "default": 60, "help": "Approx. number of bars"})],
    )
    _cmd("supply", cmd_supply, f"Show total minted {TOKEN_SYMBOL}")
    _cmd(
        "export",
        cmd_export,
        "Export ledger",
        [("--outfile", {"type": Path, "required": True, "help": "Destination file"})],
    )
    _cmd("verify", cmd_verify, "Audit ledger integrity & hard-cap")
    _cmd("selftest", _cmd_selftest, argparse.SUPPRESS)  # hidden
    return p


def main(argv: List[str] | None = None) -> None:  # pragma: no cover
    args = _build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main()
