# SPDX-License-Identifier: Apache-2.0
# alpha_factory_v1/demos/macro_sentinel/data_feeds.py
# © 2025 MONTREAL.AI Apache-2.0 License
"""
Macro-Sentinel — Data Feeds
───────────────────────────
Bridges offline CSV snapshots *and* real-time APIs into a single async
generator that emits uniformly-shaped macro-events for the Orchestrator agent.

Highlights
----------
● Graceful degrade: zero-config offline mode falls back on CSVs bundled in
  `offline_samples/`.
● Multi-source live polling (FRED, Fed RSS, Etherscan, CME futures).
● Async HTTP via *aiohttp* to avoid blocking the agent loop.
● Optional publish hooks: TimescaleDB, Redis Streams, Qdrant vector store.
● All credentials pulled from `config.env`; no secrets in code.
"""

from __future__ import annotations
import os, csv, json, asyncio, datetime as dt, pathlib, random

try:  # aiohttp optional at test time
    import aiohttp
except ModuleNotFoundError:  # pragma: no cover - offline fallback
    aiohttp = None
from typing import AsyncIterator, Dict, Any, Optional
from collections import deque
from urllib.request import urlopen

# ───────────────────────── Config from env ──────────────────────────
DATA_DIR = pathlib.Path(__file__).parent / "offline_samples"

FRED_KEY      = os.getenv("FRED_API_KEY")
ETHERSCAN_KEY = os.getenv("ETHERSCAN_API_KEY")
RSS_URL       = os.getenv("FED_RSS_URL",
                          "https://www.federalreserve.gov/feeds/press_speeches.htm")
FRED_3M       = os.getenv("FRED_SERIES_3M",  "DTB3")
FRED_10Y      = os.getenv("FRED_SERIES_10Y", "DGS10")
STABLE_TOKEN  = os.getenv("STABLE_TOKEN",
                          "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606e48")   # USDC
CME_SYMBOL    = os.getenv("CME_SYMBOL", "ES")     # S&P 500 futures

# optional sinks
DB_URL    = os.getenv("DATABASE_URL")   # Timescale/Postgres
REDIS_URL = os.getenv("REDIS_URL")
VEC_URL   = os.getenv("VECTOR_HOST")    # Qdrant

# ───────────────────────── Helpers / offline CSV ────────────────────
OFFLINE_URLS = {
    "fed_speeches.csv": "https://raw.githubusercontent.com/MontrealAI/demo-assets/main/fed_speeches.csv",
    "yield_curve.csv":  "https://raw.githubusercontent.com/MontrealAI/demo-assets/main/yield_curve.csv",
    "stable_flows.csv": "https://raw.githubusercontent.com/MontrealAI/demo-assets/main/stable_flows.csv",
    "cme_settles.csv":  "https://raw.githubusercontent.com/MontrealAI/demo-assets/main/cme_settles.csv",
}

_DEFAULT_ROWS = {
    "fed_speeches.csv": {"text": "No speech"},
    "yield_curve.csv":  {"3m": "4.5", "10y": "4.4"},
    "stable_flows.csv": {"usd_mn": "25"},
    "cme_settles.csv":  {"settle": "5000"},
}

def _ensure_offline():
    DATA_DIR.mkdir(exist_ok=True)
    for name, url in OFFLINE_URLS.items():
        path = DATA_DIR / name
        if path.exists():
            continue
        try:
            with urlopen(url, timeout=5) as r, open(path, "wb") as f:
                f.write(r.read())
        except Exception:
            row = _DEFAULT_ROWS[name]
            with open(path, "w", newline="") as f:
                writer = csv.DictWriter(f, row.keys())
                writer.writeheader()
                writer.writerow(row)

def _csv(name: str) -> list[dict]:
    with open(DATA_DIR / name, newline="") as f:
        return list(csv.DictReader(f))

_ensure_offline()

OFF_FED    = _csv("fed_speeches.csv")
OFF_YIELD  = _csv("yield_curve.csv")
OFF_FLOW   = _csv("stable_flows.csv")
OFF_CME    = _csv("cme_settles.csv")  # snapshot of ES settles

# ───────────────────────── Async HTTP helpers ───────────────────────
_SESSION: Optional[aiohttp.ClientSession] = None
async def _session() -> aiohttp.ClientSession:
    global _SESSION
    if _SESSION is None:
        _SESSION = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5))
    return _SESSION

async def _http_json(url: str) -> Any:
    s = await _session()
    async with s.get(url) as r:
        r.raise_for_status()
        return await r.json()

async def _http_text(url: str) -> str:
    s = await _session()
    async with s.get(url) as r:
        r.raise_for_status()
        return await r.text()

# ───────────────────────── Live fetchers ─────────────────────────────
async def _fred_latest(series: str) -> Optional[float]:
    if not FRED_KEY:
        return None
    url = ("https://api.stlouisfed.org/fred/series/observations"
           f"?series_id={series}&api_key={FRED_KEY}&file_type=json"
           "&sort_order=desc&limit=1")
    j = await _http_json(url)
    val = j["observations"][0]["value"]
    return float(val) if val not in {"", "."} else None

_CACHE_SPEECH = deque(maxlen=10)
async def _latest_fed_speech() -> Optional[str]:
    try:
        xml = await _http_text(RSS_URL)
        title_start = xml.index("<title>") + 7
        title_end   = xml.index("</title>", title_start)
        title = xml[title_start:title_end]
        if title not in _CACHE_SPEECH:
            _CACHE_SPEECH.append(title)
            return title
    except Exception:
        return None
    return None

async def _latest_stable_flow() -> Optional[float]:
    if not ETHERSCAN_KEY:
        return None
    url = (f"https://api.etherscan.io/api?module=account&action=tokentx"
           f"&contractaddress={STABLE_TOKEN}&page=1&offset=1&sort=desc"
           f"&apikey={ETHERSCAN_KEY}")
    j = await _http_json(url)
    val = j["result"][0]["value"]
    return float(val) / 1e6

async def _latest_cme_settle() -> Optional[float]:
    # Deribit free endpoint as CME fallback
    try:
        url = f"https://www.deribit.com/api/v2/public/ticker?instrument_name={CME_SYMBOL}-PERPETUAL"
        j   = await _http_json(url)
        return float(j["result"]["last_price"])
    except Exception:
        return None

# ───────────────────────── Optional fan-out sinks ────────────────────
def _safe(f, *a, **kw):
    try:
        f(*a, **kw)
    except Exception:
        pass

def _push_db(evt: Dict[str, Any]):
    if not DB_URL:
        return
    import psycopg2
    with psycopg2.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO macro_events "
            "(ts,speech,y10y,y3m,stable_flow,es_settle)"
            "VALUES (%s,%s,%s,%s,%s,%s)",
            (evt["timestamp"], evt["fed_speech"], evt["yield_10y"],
             evt["yield_3m"], evt["stable_flow"], evt["es_settle"])
        )

def _push_redis(evt: Dict[str, Any]):
    if not REDIS_URL:
        return
    import redis, json as _j
    r = redis.from_url(REDIS_URL)
    r.xadd("macro_stream", {"json": _j.dumps(evt)}, maxlen=10000)

def _push_qdrant(evt: Dict[str, Any]):
    if not VEC_URL:
        return
    import af_requests as requests, hashlib, json as _j
    vec = hashlib.sha256(evt["fed_speech"].encode()).digest()[:8]
    payload = {"points":[{"id":evt["timestamp"],"vector":list(vec),"payload":evt}]}
    requests.put(f"http://{VEC_URL}/collections/macro/points",
                 data=_j.dumps(payload),
                 headers={"Content-Type":"application/json"})

def _fanout(evt: Dict[str, Any]):
    _safe(_push_db,   evt)
    _safe(_push_redis,evt)
    _safe(_push_qdrant,evt)

# ───────────────────────── Main async generator ──────────────────────
async def stream_macro_events(live: bool = False) -> AsyncIterator[Dict[str, Any]]:
    idx = 0
    while True:
        evt = {"timestamp": dt.datetime.now(dt.timezone.utc).isoformat()}
        if live:
            speech = await _latest_fed_speech() or OFF_FED[idx]["text"]
            y10    = await _fred_latest(FRED_10Y)  or float(OFF_YIELD[idx]["10y"])
            y3     = await _fred_latest(FRED_3M)   or float(OFF_YIELD[idx]["3m"])
            flow   = await _latest_stable_flow()   or float(OFF_FLOW[idx]["usd_mn"])
            es     = await _latest_cme_settle()    or float(OFF_CME[idx]["settle"])
        else:
            speech = OFF_FED[idx]["text"]
            y10, y3 = float(OFF_YIELD[idx]["10y"]), float(OFF_YIELD[idx]["3m"])
            flow = float(OFF_FLOW[idx]["usd_mn"])
            es   = float(OFF_CME[idx]["settle"])

        evt.update({
            "fed_speech":  speech,
            "yield_10y":   y10,
            "yield_3m":    y3,
            "stable_flow": flow,
            "es_settle":   es
        })
        _fanout(evt)
        yield evt
        idx = (idx + 1) % len(OFF_FED)
        await asyncio.sleep(15 if live else 1)
