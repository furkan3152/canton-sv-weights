"""Stage 2: what one unit of SV weight earns, and where the escrowed share goes.

The SV tranche of a round is a fixed share of the round's issuance
(Splice daml/splice-amulet/daml/Splice/Issuance.daml,
computeIssuingRoundParameters):

    adjusted  = amuletToIssuePerYear / roundsPerYear * (1 - developmentFund)
    svTranche = adjusted * (1 - validatorRewardPercentage - appRewardPercentage)
    issuancePerSvRewardCoupon = svTranche / weight of the SV coupons issued

So every unit of weight, including weight on escrow (ghost) parties, takes the
same share. CIP-0066 says the host disables minting for escrowed parties, so
their share expires into the unclaimed-reward pool.

The issuance curve is read from the live AmuletRules in data/onchain/. Its
steps are keyed by issuance time, one tick per round, so they are placed at a
round number. Calendar dates of config changes are mapped to rounds with the
sampled round opening times in data/lighthouse/round_samples.csv. Rewards are
summed per round, so the result does not depend on how long rounds took.

Writes data/dilution.csv and figures/dilution.png.
"""

import csv
import glob
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from rounds import round_at, samples, when

ROOT = Path(__file__).resolve().parent.parent
# Default of optDevelopmentFundPercentage in Issuance.daml (CIP-0082).
DEV_FUND_DEFAULT = 0.05
# CIP-0082 took effect with the Amulet 0.1.14 -> 0.1.15 package vote
# (created 2026-02-09 by Digital-Asset-2, 12 accepts, effective at this time;
# see data/lighthouse/governance.json). The sampled rounds confirm that the
# tranche falls by 5% between 2026-02-07 and 2026-02-14.
DEV_FUND_START = datetime(2026, 2, 12, 19, 24, tzinfo=timezone.utc)
NOMINAL_ROUNDS_PER_YEAR = 365 * 24 * 6


def curve():
    path = sorted(glob.glob(str(ROOT / "data" / "onchain" / "dso-*.json")))[-1]
    rules = json.load(open(path))["amulet_rules"]["contract"]["payload"]["configSchedule"]["initialValue"]
    tick = int(rules["tickDuration"]["microseconds"])
    ic = rules["issuanceCurve"]
    steps = [(0, ic["initialValue"])]
    steps += [(int(s["_1"]["microseconds"]) // tick, s["_2"]) for s in ic["futureValues"]]
    return steps


def tranche_per_round(cfg, fund_on):
    share = 1 - float(cfg["validatorRewardPercentage"]) - float(cfg["appRewardPercentage"])
    pct = cfg.get("optDevelopmentFundPercentage")
    fund = (float(pct) if pct is not None else DEV_FUND_DEFAULT) if fund_on else 0.0
    return float(cfg["amuletToIssuePerYear"]) / NOMINAL_ROUNDS_PER_YEAR * (1 - fund) * share


def step_at(steps, rnd):
    current = steps[0]
    for step in steps:
        if step[0] <= rnd:
            current = step
    return current


def intervals():
    """Split the rounds at every config change, curve step and the fund start."""
    steps = curve()
    pts = samples()
    snaps = list(csv.DictReader(open(ROOT / "data" / "snapshots.csv")))
    end = float(pts[-1][1])
    dev_round = round_at(DEV_FUND_START, pts)
    marks = [(round_at(when(s["date"]), pts), s) for s in snaps]
    marks += [(float(r), None) for r, _ in steps if marks[0][0] < r < end]
    marks += [(dev_round, None)]
    marks.sort(key=lambda m: m[0])

    out, current = [], None
    for i, (start, snap) in enumerate(marks):
        current = snap or current
        stop = marks[i + 1][0] if i + 1 < len(marks) else end
        if stop <= start:
            continue
        _, cfg = step_at(steps, start)
        out.append({"snap": current, "round_start": start, "round_stop": stop,
                    "tranche": tranche_per_round(cfg, start >= dev_round)})
    return out, pts, steps


def paid_rate_cumulative(pts):
    """Escrowed share using the issuance per coupon actually paid at each sample.

    A cross-check on the model: it uses the on-chain rate, which reflects the
    weight of the coupons really issued, instead of the tranche divided by the
    config file's total.
    """
    snaps = [(round_at(when(s["date"]), pts), float(s["escrow"]) + float(s["unassigned"]))
             for s in csv.DictReader(open(ROOT / "data" / "snapshots.csv"))]
    total = 0.0
    for (_, r0, rate), (_, r1, _) in zip(pts, pts[1:]):
        ghost = 0.0
        for start, g in snaps:
            if start <= r0:
                ghost = g
        total += rate * ghost * 10_000 * (r1 - r0)
    return total


def main():
    rows, pts, steps = intervals()
    out, cumulative = [], 0.0
    for iv in rows:
        s = iv["snap"]
        total = float(s["total"])
        ghost = float(s["escrow"]) + float(s["unassigned"])
        rounds = iv["round_stop"] - iv["round_start"]
        ghost_cc = iv["tranche"] * rounds * ghost / total
        cumulative += ghost_cc
        out.append({
            "date": s["date"], "commit": s["commit"],
            "round_start": round(iv["round_start"], 1), "round_stop": round(iv["round_stop"], 1),
            "total_weight": total, "ghost_weight": round(ghost, 4),
            "ghost_share": round(ghost / total, 4),
            "sv_tranche_cc_per_round": round(iv["tranche"], 4),
            "sv_tranche_cc_per_year": round(iv["tranche"] * NOMINAL_ROUNDS_PER_YEAR),
            "cc_per_weight_unit_per_round": round(iv["tranche"] / total, 6),
            "cc_per_weight_unit_per_year": round(iv["tranche"] / total * NOMINAL_ROUNDS_PER_YEAR),
            "ghost_cc_per_year": round(iv["tranche"] * NOMINAL_ROUNDS_PER_YEAR * ghost / total),
            "ghost_cc_in_interval": round(ghost_cc),
            "ghost_cc_cumulative": round(cumulative),
        })

    with open(ROOT / "data" / "dilution.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)

    def date_of(rnd):
        for (t0, r0, _), (t1, r1, _) in zip(pts, pts[1:]):
            if r0 <= rnd <= r1:
                return t0 + (t1 - t0) * ((rnd - r0) / (r1 - r0))
        return pts[-1][0]

    dates = [date_of(r["round_start"]) for r in out] + [pts[-1][0]]
    values = [r["cc_per_weight_unit_per_year"] / 1e6 for r in out]
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    ax.step(dates, values + values[-1:], where="post", color="#4C6A92",
            label="CC per 52,560 rounds (one nominal year) for one unit of SV weight")
    for rnd, cfg in steps:
        if out[0]["round_start"] < rnd < out[-1]["round_stop"]:
            t = date_of(rnd)
            ax.axvline(t, color="#999", linestyle=":", linewidth=1)
            ax.annotate(f"curve step at round {rnd:,}: "
                        f"{float(cfg['amuletToIssuePerYear']) / 1e9:.0f}B CC/yr",
                        xy=(t, 0), xytext=(4, 6), textcoords="offset points",
                        fontsize=8, color="#666")
    ax.set_ylabel("Million CC per nominal year per unit of weight")
    ax.set_title("What one unit of Super Validator weight earns on MainNet", loc="left")
    ax.set_xlim(dates[0], dates[-1])
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(frameon=False, fontsize=9)
    fig.text(0.01, 0.01, "Sources: SV weight from canton-foundation/configs; issuance curve from "
             "live AmuletRules; round times from Lighthouse; formula from Splice Issuance.daml "
             "(5% development fund from 12 Feb 2026)", fontsize=7, color="#666")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(ROOT / "figures" / "dilution.png")

    last = out[-1]
    print("first:", out[0]["date"][:10], out[0]["cc_per_weight_unit_per_year"])
    print("last:", last)
    print("through round", last["round_stop"], "at", pts[-1][0].isoformat())
    print("cross-check with the paid rate:", round(paid_rate_cumulative(pts)))


if __name__ == "__main__":
    main()
