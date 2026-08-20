#!/usr/bin/env python3
"""
generate_data.py — synthetic detection-event generator for the
Attention Intelligence Platform.

Produces a stream of "detection events" (a brand recognised in egocentric
video, with a confidence score and a dwell time) grouped into sessions.

Designed to stay useful for the whole of Course 2:

  Week 1  raw events.json to load into SQLite
  Week 2  denormalised brand strings, no indexes -> you add both
  Week 3  --preset perf gives enough rows for sorting/search timing
  Week 4  contexts create a co-occurrence graph with real cluster structure
  Week 5  dwell_seconds is a KNOWN function of confidence and hour-of-day
  Week 6  session.context is ground truth to score your clustering against
  Week 7  --preset perf is large enough for profiling to be meaningful
  Week 8  one command regenerates every dataset the project needs

Usage:
    python3 generator_upgraded.py --preset dev
    python3 generator_upgraded.py --preset ml --stats
    python3 generator_upgraded.py --sessions 5000 --contexts 12 --sqlite
    python3 generator_upgraded.py --preset ml --messy      # nulls, dupes, outliers
    python3 generator_upgraded.py --preset ml --test-instances 1000
        # writes test_events.json: a held-out set (different seed, same
        # generating process) for evaluating a model trained on events.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sqlite3
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# GROUND TRUTH — the data-generating process.
#
# These are the numbers your Week 5 regression is trying to rediscover.
# Do not read them from your modelling code; use them to check your answers.
# ---------------------------------------------------------------------------

TRUE_INTERCEPT = 0.3
TRUE_BETA_CONFIDENCE = 1.8      # +1.8 dwell-seconds per 1.0 of confidence
TRUE_HOUR_AMPLITUDE = 0.8       # size of the (nonlinear) hour-of-day effect
TRUE_HOUR_PEAKS = (12.5, 19.0)  # bimodal: lunchtime and evening
TRUE_HOUR_WIDTH = 2.2
TRUE_NOISE_SD = 0.4
TRUE_WEEKEND_BONUS = 0.2

BRAND_REPEAT_PROB = 0.55  # chance the next detection is the same brand as the
                          # last (an object stays in frame across consecutive
                          # detections) rather than a fresh independent draw

# ---------------------------------------------------------------------------
# CONTEXTS — the latent structure. Brands repeat across contexts on purpose:
# those shared brands become the bridges that make 2-hop BFS interesting.
#
#   hours   : plausible start-time windows (start_hour, end_hour)
#   events  : (min, max) detections per session
#   gap     : (min, max) seconds between consecutive detections
# ---------------------------------------------------------------------------

CONTEXT_CATALOGUE = [
    {"name": "gym",          "base_dwell": 0.9, "events": (9, 24), "gap": (8, 45),
     "hours": [(6, 9), (17, 20)],
     "brands": ["Nike", "Adidas", "Gatorade", "Under Armour", "Lucozade"]},

    {"name": "commute",      "base_dwell": 0.4, "events": (7, 20), "gap": (5, 30),
     "hours": [(7, 10), (16, 19)],
     "brands": ["Starbucks", "Spotify", "Apple", "Costa", "Trainline"]},

    {"name": "grocery",      "base_dwell": 0.7, "events": (13, 35), "gap": (6, 35),
     "hours": [(10, 13), (17, 20)],
     "brands": ["Coca-Cola", "Kellogg's", "Heinz", "Tesco", "Cadbury"]},

    {"name": "office",       "base_dwell": 1.1, "events": (11, 31), "gap": (20, 180),
     "hours": [(9, 17)],
     "brands": ["Apple", "Dell", "Slack", "Nespresso", "Post-it"]},

    {"name": "cafe",         "base_dwell": 1.2, "events": (7, 18), "gap": (30, 200),
     "hours": [(8, 11), (14, 17)],
     "brands": ["Costa", "Pret", "Innocent", "Oatly", "Apple"]},

    {"name": "high_street",  "base_dwell": 0.6, "events": (15, 40), "gap": (4, 25),
     "hours": [(11, 18)],
     "brands": ["Zara", "H&M", "Uniqlo", "Nike", "Sephora"]},

    {"name": "cinema",       "base_dwell": 1.3, "events": (4, 15), "gap": (40, 300),
     "hours": [(18, 22)],
     "brands": ["Coca-Cola", "Pepsi", "Odeon", "Ben & Jerry's", "Haribo"]},

    {"name": "home_evening", "base_dwell": 1.5, "events": (7, 22), "gap": (60, 400),
     "hours": [(19, 23)],
     "brands": ["Netflix", "Deliveroo", "Samsung", "IKEA", "Sony"]},

    {"name": "sports_bar",   "base_dwell": 1.0, "events": (9, 26), "gap": (25, 150),
     "hours": [(19, 23)],
     "brands": ["Heineken", "Guinness", "Sky Sports", "Doritos", "Pepsi"]},

    {"name": "travel",       "base_dwell": 0.8, "events": (11, 29), "gap": (15, 120),
     "hours": [(5, 9), (15, 21)],
     "brands": ["British Airways", "Booking.com", "Samsonite", "Uber", "Costa"]},

    {"name": "university",   "base_dwell": 1.3, "events": (9, 26), "gap": (30, 240),
     "hours": [(9, 18)],
     "brands": ["Dell", "Moleskine", "Red Bull", "Pret", "Lenovo"]},

    {"name": "park_run",     "base_dwell": 0.5, "events": (7, 20), "gap": (10, 60),
     "hours": [(7, 11)],
     "brands": ["Nike", "Garmin", "Lucozade", "Strava", "Adidas"]},
]

PRESETS = {
    #          sessions  contexts   what it's for
    "test": (       20,        3),  # committed test fixture — small, eyeballable
    "dev":  (      300,        6),  # day-to-day development (Weeks 1–4)
    "ml":   (     1000,       10),  # model training (Weeks 5–6)
    "perf": (    50000,       12),  # timing and profiling (Weeks 3, 7)
}

EPOCH = datetime(2026, 1, 5, tzinfo=timezone.utc)  # a Monday


# ---------------------------------------------------------------------------
# The generating process
# ---------------------------------------------------------------------------

def hour_effect(hour: float) -> float:
    """Bimodal attention curve: peaks at lunchtime and in the evening.

    Deliberately NONLINEAR in `hour`. A linear regression on raw hour cannot
    capture this, but a decision tree or random forest can — which is what
    makes the Week 6 model comparison show a real difference.
    """
    p1, p2 = TRUE_HOUR_PEAKS
    w = TRUE_HOUR_WIDTH
    a = math.exp(-((hour - p1) ** 2) / (2 * w * w))
    b = 0.8 * math.exp(-((hour - p2) ** 2) / (2 * w * w))
    return TRUE_HOUR_AMPLITUDE * (a + b)


def brand_effect(brand: str) -> float:
    """A small fixed per-brand offset in [-0.25, 0.25].

    Uses crc32, NOT the built-in hash(): Python randomises string hashing per
    process, so hash() would give different data on every run.
    """
    return (zlib.crc32(brand.encode()) % 501) / 1000.0 - 0.25


def make_dwell(rng: random.Random, confidence: float, ts: datetime,
               base: float, brand: str) -> float:
    hour = ts.hour + ts.minute / 60.0
    dwell = (
        TRUE_INTERCEPT
        + base
        + TRUE_BETA_CONFIDENCE * confidence
        + hour_effect(hour)
        + brand_effect(brand)
        + (TRUE_WEEKEND_BONUS if ts.weekday() >= 5 else 0.0)
        + rng.gauss(0, TRUE_NOISE_SD)
    )
    return round(min(5.0, max(0.05, dwell)), 2)


def generate(n_sessions: int, n_contexts: int, seed: int, messy: bool):
    """Return (sessions, events).

    Prefix-stable: with the same seed and context count, the first N sessions
    are identical no matter how many you ask for in total. Tests written
    against --preset test keep passing against --preset ml.
    """
    rng = random.Random(seed)
    contexts = CONTEXT_CATALOGUE[:n_contexts]

    sessions, events = [], []
    day = EPOCH
    sessions_today = 0
    sessions_per_day = rng.randint(2, 4)

    for sid in range(1, n_sessions + 1):
        if sessions_today >= sessions_per_day:
            day += timedelta(days=1)
            sessions_today = 0
            sessions_per_day = rng.randint(2, 4)
        sessions_today += 1

        ctx = rng.choice(contexts)
        lo, hi = rng.choice(ctx["hours"])
        start = day + timedelta(
            hours=rng.uniform(lo, hi), seconds=rng.randint(0, 3599)
        )

        # --- deliberate edge cases, always in the first three sessions so
        # --- they exist even in the 20-session test fixture.
        if sid == 1:
            n_events = 0                       # empty session / isolated node
        elif sid == 2:
            n_events = 1                       # single event, no co-occurrence
        elif sid == 3:
            n_events = rng.randint(4, 7)       # all one brand -> self-pair only
        else:
            n_events = rng.randint(*ctx["events"])

        pool = ctx["brands"]
        forced = rng.choice(pool) if sid == 3 else None

        t = start
        last_brand = None
        for _ in range(n_events):
            if forced:
                brand = forced
            elif last_brand is not None and rng.random() < BRAND_REPEAT_PROB:
                brand = last_brand           # same object, another detection
            else:
                brand = rng.choice(pool)
            last_brand = brand
            confidence = round(min(0.995, 0.45 + rng.betavariate(5, 2) * 0.55), 3)
            events.append({
                "id": len(events) + 1,
                "session_id": sid,
                "timestamp": t.isoformat(),
                "brand": brand,
                "confidence": confidence,
                "dwell_seconds": make_dwell(
                    rng, confidence, t, ctx["base_dwell"], brand
                ),
            })
            t += timedelta(seconds=rng.randint(*ctx["gap"]))

        sessions.append({
            "id": sid,
            "started_at": start.isoformat(),
            "ended_at": t.isoformat(),
            "context": ctx["name"],   # GROUND TRUTH — for tests, never a feature
        })

    if messy:
        events = make_messy(events, rng)
    return sessions, events


def make_messy(events: list[dict], rng: random.Random) -> list[dict]:
    """Opt-in realism: nulls, casing noise, outliers, duplicates.

    Off by default so Weeks 1–4 aren't fighting dirty data. Turn it on for
    Week 6, where cleaning and encoding is the actual lesson.
    """
    for e in events:
        r = rng.random()
        if r < 0.02:
            e["confidence"] = None                       # missing value
        elif r < 0.04:
            e["brand"] = e["brand"].upper()              # inconsistent casing
        elif r < 0.05:
            e["brand"] = " " + e["brand"] + " "          # stray whitespace
        elif r < 0.055:
            e["dwell_seconds"] = round(e["dwell_seconds"] * 40, 2)   # outlier
    dupes = [dict(e) for e in rng.sample(events, max(1, len(events) // 100))]
    return events + dupes


def generate_test_events(n_events: int, n_contexts: int, seed: int, messy: bool):
    """Return a held-out list of ~n_events events for model evaluation.

    Uses the same generating process as generate() — same ground-truth
    relationships between confidence/hour/brand and dwell_seconds — but with
    a seed offset far outside the range anyone would pass to --seed, so a
    test set never accidentally overlaps a training draw. Session count is
    grown until the target is met, then events are truncated to exactly
    n_events.
    """
    test_seed = seed + 1_000_000
    n_sessions = max(10, n_events // 10)
    while True:
        sessions, events = generate(n_sessions, n_contexts, test_seed, messy)
        if len(events) >= n_events:
            break
        n_sessions *= 2
    return events[:n_events]


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_json(out: Path, sessions, events) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "sessions.json").write_text(json.dumps(sessions, indent=2))
    (out / "events.json").write_text(json.dumps(events, indent=2))


def write_sqlite(path: Path, sessions, events) -> None:
    """Convenience for later weeks.

    Note what is NOT here: no brands table, no foreign key on brand, no
    indexes. Normalisation is Week 2 Day 1 and indexing is Week 2 Day 2 —
    doing them for you would delete the exercise.
    """
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE sessions (
            id         INTEGER PRIMARY KEY,
            started_at TEXT NOT NULL,
            ended_at   TEXT,
            context    TEXT
        );
        CREATE TABLE events (
            id            INTEGER PRIMARY KEY,
            session_id    INTEGER NOT NULL REFERENCES sessions(id),
            timestamp     TEXT    NOT NULL,
            brand         TEXT    NOT NULL,
            confidence    REAL,
            dwell_seconds REAL    NOT NULL
        );
    """)
    con.executemany(
        "INSERT INTO sessions VALUES (?,?,?,?)",
        [(s["id"], s["started_at"], s["ended_at"], s["context"]) for s in sessions],
    )
    con.executemany(
        "INSERT INTO events (session_id,timestamp,brand,confidence,dwell_seconds)"
        " VALUES (?,?,?,?,?)",
        [(e["session_id"], e["timestamp"], e["brand"], e["confidence"],
          e["dwell_seconds"]) for e in events],
    )
    con.commit()
    con.close()


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------

def print_stats(sessions, events) -> None:
    from collections import defaultdict
    from itertools import combinations

    by_session = defaultdict(set)
    for e in events:
        if e["brand"]:
            by_session[e["session_id"]].add(str(e["brand"]).strip().title())

    graph = defaultdict(set)
    for brands in by_session.values():
        for a in brands:
            graph.setdefault(a, set())
        for a, b in combinations(sorted(brands), 2):
            graph[a].add(b)
            graph[b].add(a)

    v = len(graph)
    edges = sum(len(n) for n in graph.values()) // 2
    max_e = v * (v - 1) / 2 if v > 1 else 0
    density = edges / max_e if max_e else 0.0

    dwells = sorted(e["dwell_seconds"] for e in events)
    median = dwells[len(dwells) // 2] if dwells else 0
    high = sum(1 for d in dwells if d > median)

    print(f"sessions            {len(sessions):,}")
    print(f"events              {len(events):,}")
    print(f"events/session      {len(events)/max(1,len(sessions)):.1f}")
    print(f"brands (nodes)      {v}")
    print(f"co-occurrence edges {edges}")
    print(f"graph density       {density:.3f}   (target 0.05–0.25)")
    print(f"avg degree          {2*edges/v:.2f}" if v else "")
    print(f"median dwell        {median:.2f}s")
    print(f"class balance       {high/len(dwells):.1%} high / "
          f"{1-high/len(dwells):.1%} low" if dwells else "")

    if density > 0.35:
        print("\n!! Graph is saturating. Raise --contexts or lower --sessions,")
        print("   or threshold edges on co-occurrence count.")
    elif density < 0.03:
        print("\n!! Graph is too sparse for multi-hop BFS. Lower --contexts.")


# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--preset", choices=PRESETS, default="dev")
    p.add_argument("--sessions", type=int, help="override preset session count")
    p.add_argument("--contexts", type=int, help="override preset context count")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", type=Path, default=Path("."))
    p.add_argument("--sqlite", action="store_true", help="also write events.db")
    p.add_argument("--messy", action="store_true", help="inject dirty data")
    p.add_argument("--stats", action="store_true", help="print diagnostics")
    p.add_argument("--test-instances", type=int, nargs="?", const=1000,
                   help="write a held-out test_events.json with this many "
                        "events (default 1000) instead of the normal "
                        "training output")
    args = p.parse_args()

    n_sessions, n_contexts = PRESETS[args.preset]
    n_sessions = args.sessions or n_sessions
    n_contexts = min(args.contexts or n_contexts, len(CONTEXT_CATALOGUE))

    if args.test_instances:
        test_events = generate_test_events(
            args.test_instances, n_contexts, args.seed, args.messy
        )
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "test_events.json").write_text(json.dumps(test_events, indent=2))
        print(f"wrote {len(test_events):,} test events "
              f"-> {args.out}/test_events.json (seed={args.seed + 1_000_000})")
        return

    sessions, events = generate(n_sessions, n_contexts, args.seed, args.messy)
    write_json(args.out, sessions, events)
    if args.sqlite:
        write_sqlite(args.out / "events.db", sessions, events)

    print(f"wrote {len(events):,} events across {len(sessions):,} sessions "
          f"-> {args.out}/  (seed={args.seed}, contexts={n_contexts})")
    if args.stats:
        print()
        print_stats(sessions, events)


if __name__ == "__main__":
    main()