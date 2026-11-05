"""Figure 1: total SV reward weight on MainNet, split by who holds it.

Reads data/snapshots.csv (written by extract.py) and writes
figures/weight-classes.png.
"""

import csv
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent

CLASSES = [
    ("node", "Kept by the SV node operator", "#4C6A92"),
    ("active", "Passed to an active beneficiary", "#7FA6C9"),
    ("escrow", "Escrowed for a milestone (ghost party)", "#D98C5F"),
    ("unassigned", "Not yet assigned (GhostSV pool)", "#E8C07D"),
]


def main():
    rows = list(csv.DictReader(open(ROOT / "data" / "snapshots.csv")))
    dates = [datetime.fromisoformat(r["date"]) for r in rows]
    # Clip the operator remainder at zero: in four snapshots the GSF node lists
    # more beneficiary weight than its own weight (see the notes).
    series = {
        key: [max(float(r[key]), 0.0) for r in rows] for key, _, _ in CLASSES
    }

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=150)
    ax.stackplot(
        dates,
        *[series[key] for key, _, _ in CLASSES],
        labels=[label for _, label, _ in CLASSES],
        colors=[color for _, _, color in CLASSES],
        step="post",
        linewidth=0,
    )
    ax.set_title("Canton MainNet: Super Validator reward weight by holder", loc="left")
    ax.set_ylabel("Reward weight (1.0 = 10,000 bps)")
    ax.set_xlim(dates[0], dates[-1])
    ax.grid(axis="y", alpha=0.3)
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    last = rows[-1]
    ghost = float(last["escrow"]) + float(last["unassigned"])
    ax.annotate(
        f"{float(last['total']):.1f} total\n{ghost / float(last['total']):.0%} escrowed or unassigned",
        xy=(dates[-1], float(last["total"])),
        xytext=(-150, -10),
        textcoords="offset points",
        fontsize=9,
    )
    fig.text(
        0.01,
        0.01,
        "Source: git history of configs/MainNet/approved-sv-id-values.yaml, "
        "github.com/canton-foundation/configs",
        fontsize=7,
        color="#666",
    )
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    out = ROOT / "figures" / "weight-classes.png"
    fig.savefig(out)
    print(out)


if __name__ == "__main__":
    main()
