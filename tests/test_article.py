"""Check that every number quoted in article.md matches the generated data.

Each figure is recomputed from data/ and formatted the way the article
writes it. A failure means the data changed and the article was not
updated, or the article quotes a number the data does not support.

Run from the repository root:  python3 -m unittest discover -s tests
"""

import csv
import json
import statistics
import sys
import unittest
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "src"))

ARTICLE = (ROOT / "article.md").read_text()


def rows(name):
    with open(DATA / name, newline="") as f:
        return list(csv.DictReader(f))


def when(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


class ArticleNumbers(unittest.TestCase):
    def quoted(self, *texts):
        for text in texts:
            self.assertTrue(text in ARTICLE, f"article does not quote {text!r}")

    def quoted_number(self, template, value):
        """Accept the value written as 15 or 15.0, 177.125 or 177.1."""
        forms = {f"{value:g}", f"{value:.1f}", f"{value:.2f}", f"{value:.3f}"}
        self.assertTrue(any(template.format(f) in ARTICLE for f in forms),
                        f"article does not quote {template.format(value)!r}")

    def test_weight_split(self):
        last = rows("snapshots.csv")[-1]
        total = float(last["total"])
        ghost = float(last["escrow"]) + float(last["unassigned"])
        self.quoted(f"{total:g}", f"{ghost:.2f}", f"{ghost / total:.1%}",
                    f"{float(last['escrow']):g}", f"{float(last['unassigned']):g}",
                    f"{float(last['node']):g}", f"{float(last['active']):g}",
                    f"{float(last['node']) / total:.1%}", f"{float(last['active']) / total:.1%}",
                    f"{float(last['escrow']) / total:.1%}", f"{float(last['unassigned']) / total:.1%}")
        first = rows("snapshots.csv")[0]
        self.quoted(f"from {float(first['total']):g}" if f"from {float(first['total']):g}" in ARTICLE
                    else f"stayed at {float(first['total']):g}")

    def test_escrow_hosts_and_parties(self):
        last = rows("snapshots.csv")[-1]["commit"]
        hosts = defaultdict(float)
        parties = Counter()
        for b in rows("beneficiaries.csv"):
            if b["commit"] == last and b["class"] == "escrow":
                hosts[b["node"]] += float(b["weight"])
                parties[b["node"]] += 1
        self.quoted(f"{sum(parties.values())} ghost parties",
                    f"GSF hosts {hosts['Global-Synchronizer-Foundation']:g} of the escrowed weight on "
                    f"{parties['Global-Synchronizer-Foundation']} parties",
                    f"MPC Holding {hosts['MPC-Holding-Inc']:g} on {parties['MPC-Holding-Inc']}",
                    f"Five North {hosts['Five-North-1']:g} on {parties['Five-North-1']}")

    def test_node_weights(self):
        path = sorted((DATA / "onchain").glob("dso-*.json"))[-1]
        svs = json.loads(path.read_text())["dso_rules"]["contract"]["payload"]["svs"]
        weights = {info["name"]: int(info["svRewardWeight"]) / 10_000 for _, info in svs}
        gsf = weights["Global-Synchronizer-Foundation"]
        self.quoted(f"{gsf:g} weight, {gsf / sum(weights.values()):.1%}", f"{len(weights)} SV nodes")

    def test_rewards(self):
        dil = rows("dilution.csv")
        last = dil[-1]
        self.quoted(f"{float(last['sv_tranche_cc_per_round']):,.0f} CC per round",
                    f"about {float(dil[0]['cc_per_weight_unit_per_year']) / 1e6:.1f} million CC per nominal year",
                    f"about {float(last['cc_per_weight_unit_per_year']) / 1e6:.1f} million today",
                    f"about {float(last['ghost_cc_per_year']) / 1e6:.0f} million CC per nominal year",
                    f"about {float(last['ghost_cc_cumulative']) / 1e9:.2f} billion CC",
                    f"{float(last['ghost_share']):.1%} of today's SV tranche")
        counterfactual = float(last["sv_tranche_cc_per_year"]) / float(rows("snapshots.csv")[0]["total"])
        self.quoted(f"about {counterfactual / 1e6:.1f} million. The rest")
        from dilution import paid_rate_cumulative
        from rounds import samples
        self.quoted(f"gives {paid_rate_cumulative(samples()) / 1e9:.2f} billion")
        pool = rows("snapshots.csv")[-1]["unassigned"]
        per_unit = float(last["cc_per_weight_unit_per_year"])
        self.quoted(f"about {float(pool) * per_unit / 1e6:.1f} million CC per nominal year")

    def test_round_cadence(self):
        pts = rows("lighthouse/round_samples.csv")
        start = next(p for p in pts if p["open_at"] >= "2025-06-03")
        minutes = (when(pts[-1]["open_at"]) - when(start["open_at"])).total_seconds() / 60 \
            / (int(pts[-1]["round"]) - int(start["round"]))
        self.quoted(f"averaged about {minutes:.1f} minutes")

    def test_payouts(self):
        votes = rows("mint_votes.csv")
        self.quoted(f"there have been {len(votes)} such votes, "
                    f"{sum(v['status'] == 'executed' for v in votes)} of them executed")
        by_kind = defaultdict(float)
        for v in votes:
            if v["status"] == "executed" and v["repeat"] == "False":
                by_kind[v["kind"]] += float(v["amount_cc"])
        self.quoted(f"{by_kind['milestone'] / 1e6:,.1f} million CC",
                    f"{by_kind['one-time allocation (CIP-0067)'] / 1e6:,.1f} million CC",
                    f"{by_kind['party correction'] / 1e6:,.1f} million CC")
        comparable = [r for r in rows("mints.csv") if r["comparable"] == "True"]
        ratios = sorted(float(r["ratio"]) for r in comparable)
        mint = sum(float(r["approved_mint_cc"]) for r in comparable)
        model = sum(float(r["modeled_escrow_cc"]) for r in comparable)
        self.quoted(f"For the {len(comparable)} grants where the comparison applies",
                    f"{mint / 1e6:.0f} million CC and the method gives {model / 1e6:.0f} million",
                    f"from {ratios[0]:.2f} to {ratios[-1]:.2f}, with a median of {statistics.median(ratios):.2f}")

    def test_grant_accounting(self):
        grants = rows("grants.csv")
        total = lambda k: sum(float(g[k]) for g in grants)
        for label, key in (("Placed in escrow", "escrow_granted"),
                           ("Earned and released to the organisation", "earned_from_escrow"),
                           ("Released without being earned", "released_unearned"),
                           ("Removed under CIP-0111", "removed"),
                           ("Still escrowed", "escrow_now")):
            self.quoted_number(f"| {label} | {{}} |", total(key))
        self.quoted(f"history of {len(grants)} milestone grants and {len(rows('events.csv'))} weight changes")
        status = Counter(g["status"] for g in grants)
        self.quoted(f"{status['fully earned']} are fully earned", f"{status['partly earned']} are partly earned",
                    f"{status['fully escrowed']} have earned nothing yet", f"{status['removed']} were removed")
        self.assertEqual(status["closed, partly earned"], 1)

    def test_deadlines(self):
        due = [r for r in rows("deadlines.csv") if r["review_due"] == "True"]
        low = sum(float(r["unmet_passed_low"]) for r in due)
        high = sum(float(r["unmet_passed_high"]) for r in due)
        n_low = sum(float(r["unmet_passed_low"]) > 0 for r in due)
        other = sum(float(r["escrow_now"]) - float(r["unmet_passed_low"]) for r in due)
        n_other = sum(float(r["escrow_now"]) - float(r["unmet_passed_low"]) > 1e-9 for r in due)
        self.quoted(f"Between {low:.1f} and {high:.1f} escrowed weight, across {n_low} grants",
                    f"| {n_low} | {low:.1f} |", f"| {n_other} | {other:.1f} |")
        rest = [r for r in rows("deadlines.csv") if r["review_due"] != "True" and float(r["escrow_now"]) > 0]
        conf = [r for r in rest if r["timeline_confidential"] == "True"]
        ahead = [r for r in rest if r["timeline_confidential"] != "True"]
        self.quoted(f"| {len(conf)} | {sum(float(r['escrow_now']) for r in conf):.1f} |",
                    f"| {len(ahead)} | {sum(float(r['escrow_now']) for r in ahead):.1f} |")
        top = sorted(due, key=lambda r: -float(r["unmet_passed_low"]))[:5]
        for r in top:
            self.quoted(f", {float(r['unmet_passed_low']):g}")

    def test_history(self):
        snaps = rows("snapshots.csv")
        first = next(s for s in snaps if float(s["escrow"]) > 0)
        self.assertEqual(first["date"][:10], "2025-06-03")
        self.quoted("Escrow did not exist before 3 June 2025")
        third = next(s for s in snaps if float(s["escrow"]) / float(s["total"]) > 1 / 3)
        self.assertEqual(third["date"][:7], "2025-11")
        later = [float(s["escrow"]) / float(s["total"]) for s in snaps if s["date"] >= third["date"]]
        self.quoted(f"between {min(later):.0%} and {max(later):.0%} since")
        events = rows("events.csv")
        start, first_ms = {}, {}
        for e in events:
            if e["kind"] == "grant":
                start.setdefault(e["cip"], e["date"])
            if e["kind"] == "milestone":
                first_ms.setdefault(e["cip"], e["date"])
        days = [(datetime.fromisoformat(first_ms[c]) - datetime.fromisoformat(start[c])).days
                for c in first_ms]
        self.quoted(f"median {round(statistics.median(days))} days")
        grants = {g["cip"]: g for g in rows("grants.csv")}
        fb = grants["CIP-0072"]
        self.quoted(f"{float(fb['released_unearned']):g} of its weight is now in that pool",
                    f"{float(fb['active_now']):g} of its {float(fb['escrow_granted']):g} earned")
        withheld = sum(float(g["enforced"]) - float(g["restored"]) for g in grants.values())
        self.quoted(f"Net of reversals, {withheld:.1f} weight")
        over = {b["commit"] for b in rows("beneficiaries.csv")
                if b["party_name"] == "(node operator)" and float(b["weight"]) < -1e-9}
        self.assertEqual(len(over), 4)
        self.quoted("On four commits")

    def test_weight_votes(self):
        votes = json.loads((DATA / "lighthouse" / "governance.json").read_text())["vote_requests"]
        executed = [v for v in votes if v["action_kind"] == "SRARC_UpdateSvRewardWeight"
                    and v["status"] == "executed"]
        placeholder = [v for v in executed if v["target_effective_at"].startswith("2025-07-06T08:16")]
        matched = [r for r in rows("weight_votes.csv") if r["lag_days"] != ""]
        lags = sorted(float(r["lag_days"]) for r in matched)
        self.quoted(f"records {len(executed)} executed weight votes",
                    f"{len(placeholder)} carry a placeholder" if len(placeholder) > 20
                    else "Seventeen carry a placeholder",
                    f"the other {len(executed) - len(placeholder)} have real effective times",
                    f"For {len(matched)} of those {len(executed) - len(placeholder)}",
                    f"median lag of {lags[len(lags) // 2]:.1f} days and a maximum of {lags[-1]:.1f}")
        self.assertEqual(len(placeholder), 17)


if __name__ == "__main__":
    unittest.main()
