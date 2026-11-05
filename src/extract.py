"""Rebuild the history of Super Validator reward weight on Canton MainNet.

Source: the git history of configs/MainNet/approved-sv-id-values.yaml in
https://github.com/canton-foundation/configs. Each commit is a snapshot of the
reward weight that SV operators approve for every SV node and for the
beneficiary parties that receive part of a node's weight.

The script reads the file at every commit that touched it and writes:

  data/beneficiaries.csv  one row per (commit, node, beneficiary)
  data/snapshots.csv      one row per commit, with totals per weight class

Weights are stored in the file as basis points of one unit of weight
(10_000 = 1.0). This script reports them in weight units.

Usage: python3 src/extract.py /path/to/configs-clone
"""

import csv
import re
import subprocess
import sys
from pathlib import Path

PATH = "configs/MainNet/approved-sv-id-values.yaml"
BPS = 10_000

NODE_RE = re.compile(r"^\s*-\s*name:\s*(\S+)")
# Early revisions quote the numbers ("100000"); later ones use 10_0000.
NODE_WEIGHT_RE = re.compile(r"^\s*rewardWeightBps:\s*\"?([\d_]+)")
BENEFICIARY_RE = re.compile(r'^\s*-\s*beneficiary:\s*"?([^"#\s]+)"?\s*(#.*)?$')
WEIGHT_RE = re.compile(r"^\s*weight:\s*\"?([\d_]+)")
CIP_RE = re.compile(r"CIP-?(\d{4})", re.IGNORECASE)


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def parse(text):
    """Return a list of nodes: {name, weight, beneficiaries: [...]}."""
    nodes = []
    pending = None
    for line in text.splitlines():
        if m := NODE_RE.match(line):
            nodes.append({"name": m.group(1), "weight": 0.0, "beneficiaries": []})
            pending = None
        elif (m := NODE_WEIGHT_RE.match(line)) and pending is not None:
            # From 2026-02-05 to 2026-04-11 the Five North entries gave each
            # beneficiary's weight as rewardWeightBps instead of weight (fixed
            # in #328). Read it as the beneficiary weight it was meant to be.
            pending["weight"] = int(m.group(1).replace("_", "")) / BPS
            pending["wrong_field"] = True
            nodes[-1]["beneficiaries"].append(pending)
            pending = None
        elif (m := NODE_WEIGHT_RE.match(line)) and nodes:
            nodes[-1]["weight"] = int(m.group(1).replace("_", "")) / BPS
        elif (m := BENEFICIARY_RE.match(line)) and nodes:
            party = m.group(1)
            name, _, fingerprint = party.partition("::")
            pending = {
                "party_name": name,
                "fingerprint": fingerprint,
                "comment": (m.group(2) or "").lstrip("# ").strip(),
            }
        elif (m := WEIGHT_RE.match(line)) and pending is not None:
            pending["weight"] = int(m.group(1).replace("_", "")) / BPS
            nodes[-1]["beneficiaries"].append(pending)
            pending = None
    return nodes


def ghost_hosts(nodes):
    """Fingerprints of the parties that hold escrowed ("ghost") weight.

    An escrow party is named *-ghost-* or *-Escrow-* and its comment says it is
    an escrow party. All escrow parties of one node share the fingerprint of
    that node's ghost validator, so the fingerprint identifies the escrow host.
    """
    hosts = set()
    for node in nodes:
        for b in node["beneficiaries"]:
            name = b["party_name"].lower()
            if "ghost" in name or "escrow" in name:
                hosts.add(b["fingerprint"])
    return hosts


def classify(b, hosts):
    name = b["party_name"].lower()
    comment = b["comment"].lower()
    if name.startswith("ghostsv-validator"):
        # Weight not yet assigned to any SV, held by the GSF ghost validator.
        return "unassigned"
    if "ghost" in name or "escrow" in name or "escrow party" in comment:
        return "escrow"
    if b["fingerprint"] in hosts:
        return "escrow"
    return "active"


def main(repo):
    repo = Path(repo)
    out = Path(__file__).resolve().parent.parent / "data"
    out.mkdir(exist_ok=True)
    log = git(repo, "log", "--reverse", "--format=%H|%cI|%s", "--", PATH)
    commits = [line.split("|", 2) for line in log.splitlines() if line]

    rows, snaps, wrong_field = [], [], []
    for sha, date, subject in commits:
        try:
            text = git(repo, "show", f"{sha}:{PATH}")
        except subprocess.CalledProcessError:
            continue  # file deleted or renamed at this commit
        nodes = parse(text)
        hosts = ghost_hosts(nodes)
        if any(b.get("wrong_field") for n in nodes for b in n["beneficiaries"]):
            wrong_field.append(sha[:7])
        totals = {"active": 0.0, "escrow": 0.0, "unassigned": 0.0, "node": 0.0}
        for node in nodes:
            assigned = 0.0
            for b in node["beneficiaries"]:
                cls = classify(b, hosts)
                totals[cls] += b["weight"]
                assigned += b["weight"]
                rows.append({
                    "commit": sha[:7], "date": date, "node": node["name"],
                    "party_name": b["party_name"], "fingerprint": b["fingerprint"][:12],
                    "weight": round(b["weight"], 4), "class": cls,
                    "cips": ";".join(sorted(set(CIP_RE.findall(b["comment"])))),
                    "comment": b["comment"],
                })
            # The node operator keeps whatever is not passed to beneficiaries.
            remainder = node["weight"] - assigned
            totals["node"] += remainder
            rows.append({
                "commit": sha[:7], "date": date, "node": node["name"],
                "party_name": "(node operator)", "fingerprint": "",
                "weight": round(remainder, 4), "class": "node", "cips": "", "comment": "",
            })
        total = sum(n["weight"] for n in nodes)
        snaps.append({
            "commit": sha[:7], "date": date, "subject": subject,
            "nodes": len(nodes), "total": round(total, 4),
            **{k: round(v, 4) for k, v in totals.items()},
        })

    with open(out / "beneficiaries.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(out / "snapshots.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(snaps[0]))
        w.writeheader()
        w.writerows(snaps)
    print(f"{len(snaps)} snapshots, {len(rows)} beneficiary rows -> {out}")
    if wrong_field:
        print(f"{len(wrong_field)} commits gave a beneficiary weight as rewardWeightBps:",
              " ".join(wrong_field))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
