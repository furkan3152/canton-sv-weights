# Handoff: Canton Community Research Grants entry (November 2026)

## Goal

Publish an original, evidence-backed research piece about Canton Super Validator
(SV) reward weight for the Canton Foundation's Community Research Grants
(https://canton.foundation/introducing-the-canton-community-research-grants/).

- Publish between 2026-11-01 and 2026-11-30. Share on X with @CantonFdn and
  #CantonResearchNov26 by 2026-12-04.
- Judged on accuracy, originality, evidence, educational value and reach.
  Constructive criticism is welcome. Purchased engagement is ignored.
- Terms and Conditions (KYC, disclosure rules) are expected by 2026-11-15. Read
  them before publishing and adjust the disclosure line at the end of the article.

## Author

Furkan Akdoğan (GitHub furkan3152). The article must read in his own voice; he
will rewrite sentences himself and must be able to explain every number. Commits
use his identity: `Furkan Akdoğan <70746444+furkan3152@users.noreply.github.com>`.

## Status

Done (each step is a commit in this repository):

1. `src/extract.py`: reads all 121 commits of
   `configs/MainNet/approved-sv-id-values.yaml` in canton-foundation/configs and
   writes `data/snapshots.csv` and `data/beneficiaries.csv`.
2. `src/lifecycle.py`: groups beneficiaries by CIP, writes `data/grants.csv`
   (38 grants) and `data/events.csv`.
3. `src/dilution.py`: SV tranche formula from Splice `Issuance.daml`
   (`computeIssuingRoundParameters`) and the live issuance curve in
   `data/onchain/`. Writes `data/dilution.csv` and `figures/dilution.png`.
4. `src/deadlines.py`: joins grants with `data/cip_milestones.json` (deadlines
   extracted from the CIP texts at canton-foundation/cips 92df641).
5. Figures: `figures/weight-classes.png`, `figures/dilution.png`,
   `figures/escrow-status.png`.
6. `article.md`: first full draft in English.

## Verified facts behind the draft

- Total weight 130 (2025-01-22) to 404.45 (2026-11-01). Node totals match the
  live on-chain DsoRules exactly (13 nodes, round 120,388, 2026-11-05).
- Escrow 177.125 on 33 ghost parties plus 3.095 unassigned = 180.22 (44.6%).
  Ghost hosts: GSF GhostSV-validator-1, MPCH-GHOSTvalidator-1, 5nghost-mainnet-1.
- CIP-0066 quotes: the GSF "disables the final minting action for all escrowed
  SV parties"; escrowed coin "goes into the unminted pool".
- SV tranche today: 10B CC/yr x 0.95 x 0.20 = 1.9B CC/yr; escrowed share about
  847M CC/yr. Cumulative since June 2025: 1.76B to 1.86B CC (the Development
  Fund's activation date is unknown, hence the range).
- One unit of weight: about 70.2M CC/yr (Jan 2025) to 4.7M CC/yr (Nov 2026).
  With weight fixed at 130 it would be 14.6M today.
- Grants: promised 262.45, earned 65.28, removed 19.45, escrowed 177.125.
  Monstera FZE and Woodside AI removed under CIP-0111 on 2026-05-17.
- Deadlines: 16 grants / 69 weight past every dated deadline; 2 / 12 partly;
  7 / 67 with unpublished milestones; 5 / 29.1 still ahead. CIP-0111 requires a
  TWG review when a deadline passes; it does not remove weight by itself.
- Over-allocation: four snapshots where GSF beneficiaries exceeded the node
  weight. `weightDistributionForSv` in Splice `SvUtil.scala` caps in list order,
  so only the last-listed escrow parties (DTCC, Société Générale) were capped.
- Docs mismatch: docs.canton.network tokenomics page says "Unclaimed rewards
  beyond all tranches go to SV rewards"; `AmuletRules.daml` (~line 600) records
  them in an `UnclaimedReward` contract instead.
- Do NOT cite the Franklin Templeton 926,060 CC unclaimed-pool vote as a
  milestone payout: its stated reason is a wrong party ID correction.

## Limits to keep in the article

- Beneficiary splits are SV app config, not on-chain; commit #358 shows the
  public file can drift from the running config.
- Scan API returned 403 without an allowlisted IP, so the real unminted pool
  was not measured; the escrowed share is what that weight would earn.
- TWG review outcomes live on lists.sync.global, which was not readable.
- Before ~March 2025 the file did not list beneficiaries.

## Next steps

1. Furkan reads the draft, marks anything unclear, rewrites in his voice.
2. Optional checks that would strengthen it: read TWG outcome posts on
   lists.sync.global; get Scan access (own validator or CCView) to measure the
   unminted pool and any milestone catch-up mints (CIP-0066 votes).
3. Publish the repository publicly, then the article (Medium, Mirror or an X
   Article), then a short X thread with the three figures.
4. Re-run `src/extract.py` against the latest configs before publishing so the
   numbers are current, and update the dates in the article.

To rerun: clone canton-foundation/configs next to this repo, then
`python3 src/extract.py ../configs && python3 src/lifecycle.py &&
python3 src/deadlines.py`; plots need `pip install matplotlib`.
