"""Consistency checks on the generated data.

Run from the repository root after the pipeline:  python3 -m unittest -v
"""

import csv
import glob
import json
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
EPS = 1e-6
CLASSES = ("active", "escrow", "unassigned", "node")


def rows(name):
    with open(DATA / name, newline="") as f:
        return list(csv.DictReader(f))


class Snapshots(unittest.TestCase):
    def test_classes_add_up_to_total(self):
        for s in rows("snapshots.csv"):
            parts = sum(float(s[c]) for c in CLASSES)
            self.assertAlmostEqual(parts, float(s["total"]), delta=EPS, msg=s["commit"])

    def test_beneficiaries_add_up_to_snapshot(self):
        by_commit = defaultdict(lambda: defaultdict(float))
        for b in rows("beneficiaries.csv"):
            by_commit[b["commit"]][b["class"]] += float(b["weight"])
        for s in rows("snapshots.csv"):
            for c in CLASSES:
                self.assertAlmostEqual(by_commit[s["commit"]][c], float(s[c]), delta=EPS,
                                       msg=(s["commit"], c))

    def test_last_snapshot_matches_onchain_node_weights(self):
        path = sorted(glob.glob(str(DATA / "onchain" / "dso-*.json")))[-1]
        svs = json.loads(Path(path).read_text())["dso_rules"]["contract"]["payload"]["svs"]
        onchain = {info["name"]: int(info["svRewardWeight"]) / 10_000 for _, info in svs}
        last = rows("snapshots.csv")[-1]["commit"]
        config = defaultdict(float)
        for b in rows("beneficiaries.csv"):
            if b["commit"] == last:
                config[b["node"]] += float(b["weight"])
        self.assertEqual(set(config), set(onchain))
        for node, weight in onchain.items():
            self.assertAlmostEqual(config[node], weight, delta=EPS, msg=node)


class Grants(unittest.TestCase):
    def test_escrow_is_fully_accounted_for(self):
        for g in rows("grants.csv"):
            out = sum(float(g[k]) for k in
                      ("escrow_now", "earned_from_escrow", "released_unearned", "removed"))
            self.assertAlmostEqual(float(g["escrow_granted"]), out, delta=EPS, msg=g["cip"])

    def test_active_weight_is_earned_net_of_enforcement(self):
        for g in rows("grants.csv"):
            net = (float(g["earned_from_escrow"]) + float(g["earned_direct"])
                   - float(g["enforced"]) + float(g["restored"]))
            self.assertAlmostEqual(float(g["active_now"]), net, delta=EPS, msg=g["cip"])

    def test_grant_escrow_matches_snapshot_escrow(self):
        last = rows("snapshots.csv")[-1]
        escrow = sum(float(g["escrow_now"]) for g in rows("grants.csv"))
        self.assertAlmostEqual(escrow, float(last["escrow"]), delta=EPS)


class Dilution(unittest.TestCase):
    def test_ghost_share_never_exceeds_tranche(self):
        for r in rows("dilution.csv"):
            self.assertLessEqual(float(r["ghost_cc_per_year"]),
                                 float(r["sv_tranche_cc_per_year"]) + 1)

    def test_cumulative_never_decreases(self):
        values = [float(r["ghost_cc_cumulative"]) for r in rows("dilution.csv")]
        self.assertEqual(values, sorted(values))


class OnchainCheck(unittest.TestCase):
    def test_model_tranche_matches_onchain_issuance(self):
        # issuancePerSvRewardCoupon is per basis point of weight, per round.
        rounds = json.loads((DATA / "lighthouse" / "rounds.json").read_text())["rounds"]
        latest = max(rounds, key=lambda r: r["round"])
        last = rows("snapshots.csv")[-1]
        per_round = latest["issuance_per_sv_reward_coupon"] * float(last["total"]) * 10_000
        model = float(rows("dilution.csv")[-1]["sv_tranche_cc_per_round"])
        self.assertAlmostEqual(per_round / model, 1.0, delta=1e-6)

    def test_model_tranche_matches_sampled_rounds(self):
        # At each sampled round, the paid issuance per coupon times the total
        # weight is the SV tranche. Allow for samples taken around a weight
        # change, when the commit date and the on-chain change differ.
        samples = rows("lighthouse/round_samples.csv")
        intervals = [(float(r["round_start"]), float(r["round_stop"]), r) for r in rows("dilution.csv")]
        checked = close = 0
        for s in samples:
            n = int(s["round"])
            iv = next((r for a, b, r in intervals if a <= n < b), None)
            if iv is None:
                continue
            paid = float(s["issuance_per_sv_reward_coupon"]) * float(iv["total_weight"]) * 10_000
            checked += 1
            close += abs(paid / float(iv["sv_tranche_cc_per_round"]) - 1) < 0.005
        self.assertGreater(checked, 180)
        self.assertGreater(close / checked, 0.8)

    def test_cumulative_matches_the_paid_rate(self):
        import sys
        sys.path.insert(0, str(ROOT / "src"))
        from dilution import paid_rate_cumulative
        from rounds import samples
        model = float(rows("dilution.csv")[-1]["ghost_cc_cumulative"])
        self.assertAlmostEqual(paid_rate_cumulative(samples()) / model, 1.0, delta=0.02)

    def test_milestone_mints_are_close_to_the_model(self):
        ratios = [float(r["ratio"]) for r in rows("mints.csv") if r["comparable"] == "True"]
        self.assertGreaterEqual(len(ratios), 15)
        for ratio in ratios:
            self.assertTrue(0.75 < ratio < 1.05, ratio)


if __name__ == "__main__":
    unittest.main()
