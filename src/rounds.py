"""Map calendar time to mining rounds, from sampled closed rounds.

Issuance follows rounds, not the calendar: the issuance curve is keyed by
issuance time, which advances one tick per round "independently of how real
world time advances" (Splice AmuletRules.daml). Rounds have taken a little
longer than one tick, so calendar dates must be mapped to round numbers from
observed round opening times.
"""

import csv
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def when(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def samples():
    rows = csv.DictReader(open(ROOT / "data" / "lighthouse" / "round_samples.csv"))
    return [(when(r["open_at"]), int(r["round"]), float(r["issuance_per_sv_reward_coupon"]))
            for r in rows]


def round_at(t, points=None):
    """Round number (fractional) open at calendar time t, by linear interpolation."""
    points = points or samples()
    if t <= points[0][0]:
        return float(points[0][1])
    for (t0, r0, _), (t1, r1, _) in zip(points, points[1:]):
        if t0 <= t <= t1:
            return r0 + (r1 - r0) * (t - t0) / (t1 - t0)
    return float(points[-1][1])
