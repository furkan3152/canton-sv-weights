"""Stage 2: what one unit of SV weight earns, and where the escrowed share goes.

The SV tranche of a round is a fixed share of the round's issuance
(Splice daml/splice-amulet/daml/Splice/Issuance.daml,
computeIssuingRoundParameters):

    adjusted = amuletToIssuePerYear / roundsPerYear * (1 - developmentFund)
    svTranche = adjusted * (1 - validatorRewardPercentage - appRewardPercentage)
    issuancePerSvRewardCoupon = svTranche / totalSvRewardWeight

So every unit of weight, including weight on escrow (ghost) parties, takes the
same share. CIP-0066 says the GSF disables minting for escrowed parties, so
their share is not minted and goes to the unminted (unclaimed) pool.

The issuance curve is read from the live AmuletRules in data/onchain/. Curve
steps are keyed by round time (round number x tick), which this script maps to
calendar time from the latest open mining round, assuming one round per tick.

Writes data/dilution.csv and figures/dilution.png.
"""

import csv
import glob
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
YEAR = timedelta(days=365)
# Default of optDevelopmentFundPercentage in Issuance.daml (CIP-0082).
DEV_FUND_DEFAULT = 0.05
# CIP-0082 took effect with the Amulet 0.1.14 -> 0.1.15 package vote
# (created 2026-02-09 by Digital-Asset-2, 12 accepts, effective at this time;
# see data/lighthouse/governance.json). Before it, no fund share was deducted.
DEV_FUND_START = datetime(2026, 2, 12, 19, 24, tzinfo=timezone.utc)


def curve():
    path = sorted(glob.glob(str(ROOT / "data" / "onchain" / "dso-*.json")))[-1]
    dso = json.load(open(path))
    rules = dso["amulet_rules"]["contract"]["payload"]["configSchedule"]["initialValue"]
    tick = timedelta(microseconds=int(rules["tickDuration"]["microseconds"]))
    latest = dso["latest_mining_round"]["contract"]["payload"]
    opens = datetime.fromisoformat(latest["opensAt"].replace("Z", "+00:00"))
    origin = opens - int(latest["round"]["number"]) * tick

    ic = rules["issuanceCurve"]
    steps = [(timedelta(0), ic["initialValue"])]
    steps += [
        (timedelta(microseconds=int(s["_1"]["microseconds"])), s["_2"])
        for s in ic["futureValues"]
    ]
    return origin, [(origin + offset, cfg) for offset, cfg in steps], path


def sv_per_year(cfg, dev_fund):
    share = 1 - float(cfg["validatorRewardPercentage"]) - float(cfg["appRewardPercentage"])
    pct = cfg.get("optDevelopmentFundPercentage")
    fund = 0.0 if dev_fund == 0.0 else float(pct) if pct is not None else dev_fund
    return float(cfg["amuletToIssuePerYear"]) * (1 - fund) * share


def step_at(steps, when):
    current = steps[0]
    for step in steps:
        if step[0] <= when:
            current = step
    return current


def main():
    origin, steps, source = curve()
    snaps = list(csv.DictReader(open(ROOT / "data" / "snapshots.csv")))
    end = datetime.fromisoformat(snaps[-1]["date"])

    # Split the timeline at every config change and every curve step, so that
    # each interval has one weight snapshot and one issuance configuration.
    first = datetime.fromisoformat(snaps[0]["date"])
    points = sorted(
        [(datetime.fromisoformat(s["date"]), s) for s in snaps]
        + [(when, None) for when, _ in steps if first < when < end]
        + [(DEV_FUND_START, None)],
        key=lambda p: p[0],
    )
    intervals, current = [], None
    for when, snap in points:
        current = snap or dict(current, date=when.isoformat())
        intervals.append(current)

    out, cumulative = [], 0.0
    for i, s in enumerate(intervals):
        start = datetime.fromisoformat(s["date"])
        stop = datetime.fromisoformat(intervals[i + 1]["date"]) if i + 1 < len(intervals) else end
        total = float(s["total"])
        ghost = float(s["escrow"]) + float(s["unassigned"])
        when, cfg = step_at(steps, start)
        sv_year = sv_per_year(cfg, DEV_FUND_DEFAULT if start >= DEV_FUND_START else 0.0)
        per_unit = sv_year / total
        ghost_year = sv_year * ghost / total
        span = (stop - start) / YEAR
        cumulative += ghost_year * span
        out.append({
            "date": s["date"], "commit": s["commit"], "total_weight": total,
            "ghost_weight": round(ghost, 4), "ghost_share": round(ghost / total, 4),
            "curve_step_from": when.date().isoformat(),
            "sv_tranche_cc_per_year": round(sv_year),
            "cc_per_weight_unit_per_year": round(per_unit),
            "ghost_cc_per_year": round(ghost_year),
            "ghost_cc_cumulative": round(cumulative),
        })

    with open(ROOT / "data" / "dilution.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)

    dates = [datetime.fromisoformat(r["date"]) for r in out]
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    ax.step(dates, [r["cc_per_weight_unit_per_year"] / 1e6 for r in out], where="post",
            color="#4C6A92", label="CC per year for one unit of SV weight")
    for when, cfg in steps:
        if dates[0] <= when <= dates[-1]:
            ax.axvline(when, color="#999", linestyle=":", linewidth=1)
            ax.annotate(f"curve step: {float(cfg['amuletToIssuePerYear']) / 1e9:.0f}B CC/yr",
                        xy=(when, ax.get_ylim()[1] if False else 0), xytext=(4, 6),
                        textcoords="offset points", fontsize=8, color="#666")
    ax.set_ylabel("Million CC per year per unit of weight")
    ax.set_title("What one unit of Super Validator weight earns on MainNet", loc="left")
    ax.set_xlim(dates[0], dates[-1])
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(frameon=False, fontsize=9)
    fig.text(0.01, 0.01, "Sources: SV weight from canton-foundation/configs; issuance curve from "
             "live AmuletRules; formula from Splice Issuance.daml (5% development fund from 12 Feb 2026)",
             fontsize=7, color="#666")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(ROOT / "figures" / "dilution.png")

    last = out[-1]
    print("curve source:", Path(source).name, "round origin:", origin.date())
    for when, cfg in steps:
        print(" step", when.date(), cfg["amuletToIssuePerYear"],
              "SV share", round(1 - float(cfg["validatorRewardPercentage"]) - float(cfg["appRewardPercentage"]), 3))
    print("first:", out[0]["date"][:10], out[0]["cc_per_weight_unit_per_year"])
    print("last:", last["date"][:10], last)


if __name__ == "__main__":
    main()
