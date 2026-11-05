# The Ghost Weight: how much Canton Super Validator reward weight is waiting on a promise

*November 2026. Every number in this article is reproduced by the code and data in [github.com/furkan3152/canton-sv-weights](https://github.com/furkan3152/canton-sv-weights). Weights are as of the config commit of 1 November 2026; on-chain data is as of 5 November 2026.*

## Summary

- Total Super Validator (SV) reward weight on Canton MainNet grew from **130 to 404.45** between January 2025 and November 2026.
- **180.22 of that weight (44.6%)** belongs to no operating SV. 177.125 sits on 32 escrow ("ghost") parties for organisations that must first meet milestones, and 3.095 sits in an unassigned pool.
- That weight takes its share of every round's SV rewards. The coupons are never claimed and expire into the network's unclaimed-reward pool. At today's issuance this is about **847 million CC per 52,560 rounds** (one nominal year). Since escrow began in June 2025, the total is about **1.74 billion CC**.
- Milestone payouts confirm the calculation. For 19 grants, the mints approved by on-chain votes total **521 million CC**, against **540 million CC** calculated here (ratio 0.96).
- Of the **260.5 weight** placed in escrow, **65.28** has been earned, **3.095** was released without being earned, **15.0** was removed, and **177.125** is still escrowed.
- **18 grants holding 81 escrowed weight** have at least one dated milestone deadline behind them. Many of those milestones were met. The escrow tied to passed, dated milestones that have *not* been earned is **between 29.6 and 49.0 weight across 11 grants**. This is the weight that CIP-0111 requires the Tokenomics Working Group to review. A further **67 weight across 7 grants** has milestones that are not published.
- The on-chain pool records only an amount, so it cannot tell escrowed rewards from any other unclaimed reward. The escrow reserve therefore exists only as an off-chain calculation. This repository publishes that calculation for the whole network.

None of this is hidden. The escrow model is written into the CIPs, and every weight change is a public commit and an on-chain vote. What has been missing is the whole picture, checked against the chain. This article puts it together and ends with five suggestions.

## 1. How SV rewards are paid

Each mining round, a fixed share of new Canton Coin goes to Super Validators. This is set in the Splice source, in `Issuance.daml` (`computeIssuingRoundParameters`). The calculation starts from the round's issuance and deducts the Development Fund share (CIP-0082) and the full validator and app tranches. What remains is divided by the total weight of the SV reward coupons issued in that round. That weight equals the total SV weight whenever every node collects its coupons.

```
svTranche                 = amuletToIssuePerYear / roundsPerYear × (1 − developmentFund) × (1 − validator% − app%)
issuancePerSvRewardCoupon = svTranche / total weight of the SV reward coupons issued in the round
```

`roundsPerYear` counts 10-minute ticks, 52,560 a year. Issuance follows rounds, not the calendar. The issuance curve is keyed by "issuance time", which advances one tick per round, "independently of how real world time advances" (`AmuletRules.daml`). Since June 2025, rounds have averaged about 10.3 minutes, so a calendar year has held about 3% fewer rounds than a nominal one. This analysis therefore sums rewards round by round.

Today the curve issues 10 billion CC per nominal year. After 5% goes to the Development Fund, the SV share of 20% comes to an SV tranche of **36,149 CC per round**. The chain confirms this. The latest closed round (120,404) paid 0.0089378571 CC per SV coupon per basis point of weight; multiplied by the 4,044,500 basis points of total weight, that is 36,149 CC.

The repository also samples every 500th round since launch. At each sample, the paid rate times the config file's total weight reproduces the expected tranche:

- 182,648 CC per round before the curve step at round 78,840 (12 January 2026);
- 38,052 CC per round after the step;
- 36,149 CC per round once the Development Fund began taking its share in mid-February 2026.

Every unit of weight earns the same amount, so every new unit of weight reduces what the others earn.

The weight of each SV node, and how a node passes part of its weight to other parties ("beneficiaries"), is published in [`canton-foundation/configs`](https://github.com/canton-foundation/configs), file `configs/MainNet/approved-sv-id-values.yaml`. The file has 121 commits since 22 January 2025. Node totals also take effect on-chain through `UpdateSvRewardWeight` votes; section 7 compares the two.

Weight is economic, not political. Governance counts one vote per SV node. A vote needs 9 of 13 under the code's threshold, `ceil((n + f + 1) / 2)` with `f = floor((n − 1) / 3)`. The Global Synchronizer Foundation (GSF) node carries 195.3 weight, 48.3% of the total, and it has one vote.

## 2. The ghost weight

Since mid-2025, milestone-based CIPs have given organisations SV weight that they earn by meeting milestones such as an integration, a product launch or a volume target. Until a milestone is met, the weight sits on an escrow party hosted by another node. In the config file these parties are named `<Organisation>-ghost-1` (or `-Escrow-1`). They are hosted on three ghost validators:

- GSF's `GhostSV-validator-1`;
- MPC Holding's `MPCH-GHOSTvalidator-1`;
- Five North's `5nghost-mainnet-1`.

![Figure 1](figures/weight-classes.png)

*Figure 1. SV reward weight by holder, from every commit of the config file.*

On 1 November 2026:

| Holder | Weight | Share |
|---|---|---|
| Kept by the 13 SV nodes (11 organisations) | 83.625 | 20.7% |
| Passed to active beneficiaries | 140.605 | 34.8% |
| **Escrowed on 32 ghost parties** | **177.125** | **43.8%** |
| **Unassigned pool (`GhostSV-validator-1`)** | **3.095** | **0.8%** |
| Total | 404.45 | |

The escrow is held by GSF (97, on 20 parties), MPC Holding (53.125, on 7) and Five North (27, on 5).

Escrowed weight was zero until 3 June 2025. It passed a third of all weight on 5 November 2025 and has stayed between 31% and 45% since.

## 3. Where escrowed rewards go

The Splice code shows the whole path.

1. **Coupons are created for escrow parties.** Each round, an SV node calls `DsoRules_ReceiveSvRewardCoupon` with its beneficiary list. The contract requires "Total beneficiary weight matches SV operator weight" and creates one `SvRewardCoupon` per beneficiary, escrow parties included.
2. **The coupons expire unclaimed.** CIP-0066 says "The GSF specifically disables the final minting action for all escrowed SV parties". The other two escrow hosts are taken to do the same; later CIPs state that "The escrow SV will NOT mint rewards". After the round closes, `DsoRules_ClaimExpiredRewards` expires the coupons and creates an `UnclaimedReward` contract for `svRewardsWeight × issuancePerSvRewardCoupon`. Expired validator and app rewards go into the same contract.
3. **The pool keeps only an amount.** `UnclaimedReward` has two fields, `dso` and `amount`. `AmuletRules_MergeUnclaimedRewards` merges many of these contracts into one. Once rewards are in the pool, nothing on-chain records whether they came from an escrow party.
4. **Milestone payouts are votes.** When the Tokenomics Working Group (TWG) agrees that a milestone is met, the SVs vote on `CreateUnallocatedUnclaimedActivityRecord`. The vote names a beneficiary, an amount and a reason. An SV then calls `DsoRules_AllocateUnallocatedUnclaimedActivityRecord`, which archives `UnclaimedReward` contracts covering the amount, and the organisation mints the coins. A record that is not minted before it expires goes back to the pool. That is why some payouts were voted twice.

There have been 53 such votes since October 2025, and 48 were executed:

| Kind | Approved amount |
|---|---|
| Milestone payouts (repeated votes counted once) | 532.3 million CC |
| CIP-0067 one-time allocation of historical unclaimed rewards to GSF (3 November 2025) | 1,617.8 million CC |
| Corrections where an external party ID had prevented minting | 8.8 million CC |

CIP-0067 allocated all unclaimed rewards "as of the effective date" that were "not explicitly reserved under any approved milestone-based SV reward schedule". So the escrow reserve is a figure that has to be calculated off-chain. This analysis did not observe the pool's current balance, because the Scan API refused requests without an allowlisted IP. It is therefore not verified that the pool covers the reserve calculated here.

CIP-0111 (approved 23 April 2026) recognises the problem. When ghost weight is removed, its coupons "should be burned to indicate the tokens associated with them are no longer in the unminted pool". It also says "Enabling this functionality will require a change to the Canton Coin SV Reward DAML model." At Splice commit `2930ba1` (5 November 2026), the only choices that consume `UnclaimedReward` are the merge and the allocation described above. The CIP gives an off-chain formula for the unminted supply instead.

## 4. How much it is

![Figure 2](figures/dilution.png)

*Figure 2. CC per nominal year (52,560 rounds) earned by one unit of SV weight. The fall at round 78,840 (12 January 2026) is the scheduled curve step from 20 to 10 billion CC a year, when the SV share also fell from 48% to 20%.*

A unit of weight earned about **73.8 million CC per nominal year** in January 2025, and earns about **4.7 million** today. The scheduled curve explains most of the fall: if total weight had stayed at 130, a unit would still earn about 14.6 million. Weight growth explains the rest.

At today's issuance, 44.6% of the SV tranche goes to escrow and unassigned weight. That is about **847 million CC per nominal year**. Summed round by round from 3 June 2025 to round 120,400 (5 November 2026), the share comes to about **1.74 billion CC**. A second calculation uses the rate actually paid at each sampled round and gives 1.73 billion. Both apply the Development Fund share from the CIP-0082 package vote, effective 12 February 2026.

These coins are not lost. They wait in the unclaimed pool until one of two things happens. Governance may mint them to an organisation that met its milestones, or a CIP-0111 reduction may mark them for burning.

## 5. Checking the calculation against the payouts

The calculation makes a testable prediction. When a milestone is met, the organisation should be paid roughly what its earned weight accrued while it was escrowed. TWG announcements credit their payout calculations to Noves and IntellectEU. Kaiko's published methodology for its own claim uses the same rule. It splits the period into intervals of constant total weight and sums `hours × weight × hourly SV rewards / total weight`.

![Figure 3](figures/mints.png)

*Figure 3. For each grant, the CC its earned weight accrued in escrow according to this calculation, against the mints approved by on-chain votes.*

For the 19 grants where the comparison applies, approved mints total **521 million CC**, against **540 million CC** calculated here. The per-grant ratio runs from 0.82 to 1.00, with a median of 0.96. The calculation runs slightly high, as expected from how it is built:

- It starts each grant at the config commit. The TWG starts at the time an operator confirmed the weight.
- It counts every round, including rounds a node did not collect.

Two grants, covering three CIPs, are left out because their payouts follow a different rule:

- **CIP-0102/CIP-0114** (Tharimmune / Canton Strategic Holdings): most of the active weight is earned under the CIP-0114 programme.
- **CIP-0115** (Société Générale): two mints were made while its escrow stayed at 8.

The close match means the 1.74 billion CC figure is the same payout calculation the network already uses, applied to all escrowed weight. On the evidence of these 19 grants, it may run a few percent high.

## 6. Promises and outcomes

Grouping every beneficiary row by the CIP in its comment gives the history of 38 milestone grants and 84 weight changes. Each change links to its commit. Every unit of escrow is accounted for, and the code checks this identity for each grant:

| | Weight |
|---|---|
| Placed in escrow | 260.5 |
| Earned (escrow released to the organisation) | 65.28 |
| Released without being earned | 3.095 |
| Removed under CIP-0111 | 15.0 |
| **Still escrowed** | **177.125** |

- **Status of the 38 grants.**
  - 5 are fully earned.
  - Fireblocks' escrow is closed with 2.58 of 5 earned.
  - 15 are partly earned and 15 have earned nothing yet.
  - 2 were removed.
- **Time to first milestone.** For grants that met a milestone, the first one came after a median of about **92 days**.
- **The only CIP-0111 removals so far** are Monstera FZE (5) and Woodside AI (10). The CIPs were marked withdrawn on 6 May 2026, the on-chain vote took effect on 15 May, and the config file changed on 17 May. That was about nine months after the weight was added.
- **Partial earnings leave weight behind.** When an organisation earns less than the escrow released for a milestone, the difference is not removed. Since January 2026 the config file moves it to the unassigned `GhostSV-validator-1` pool; before then it sat with GSF's own share. Fireblocks' escrow is fully closed, but 2.42 of its weight now sits in that pool. Together with smaller remainders from Ubyx, Talos, BitGo and Wormhole, the pool holds 3.095 weight. That is about 14.5 million CC per nominal year, still going to the unclaimed pool.
- **CIP-0105 enforcement.** Lock enforcement under CIP-0105 has withheld and restored active weight several times (Taurus, Ledger, Quantstamp, Elliptic, DFNS). Net of reversals, 1.2 weight of milestone grants is withheld today.

### Deadlines

The CIP texts set deadlines for most milestones, often "+180 days from CIP approval". Many milestones have no fixed date, such as adoption targets measured after a launch. A passed date alone also says nothing about whether the milestone was met.

To separate these cases, the repository records the maximum weight of each dated milestone from the CIP text. For each grant it then bounds the escrow tied to passed, dated milestones that have not been earned. The low bound assumes the weight earned so far came from those milestones first; the high bound assumes it came from undated ones.

![Figure 4](figures/escrow-status.png)

*Figure 4. Escrowed weight on 1 November 2026 by deadline status. The first row uses the low bound.*

| Status | Grants | Escrowed weight |
|---|---|---|
| Tied to passed, dated milestones not yet earned (low bound) | 11 | 29.6 |
| Other escrow of grants with a passed deadline: undated or later milestones | 15 | 51.4 |
| Milestones not published | 7 | 67.0 |
| No dated deadline has passed yet | 5 | 29.1 |

For several grants the dated milestones were met, and the remaining escrow belongs to milestones with no fixed date:

- Zero Hash (CIP-0099 also extended its adoption incentives);
- Zenith;
- Republic;
- Talos;
- Taurus;
- the CIP-0065 bridges, apart from 0.4 of Wormhole's integration weight.

The largest escrow tied to passed, dated milestones is held by:

- YZi Labs, 10 (the programme term in CIP-0081 ended on 26 September 2026);
- Mesh, 4;
- Blockdaemon, 4;
- the USDT0 issuer, 3;
- Zodia Custody, 3.

Some of these bounds rest on reading free-text milestone weights; ChainSafe's escrow, for example, was set below its CIP maximum. The per-grant table is in `data/deadlines.csv`.

None of this means the weight is forfeit. CIP-0111 says: "At a minimum, the TWG must review SVs for potential weight reduction whenever the deadline for a milestone associated with a milestone-based SV CIP passes." Removal then needs a TWG recommendation, an off-chain SV vote posted on the tokenomics-announce list, and an on-chain vote. Deadlines can also be extended: CIP-0099 extended Zero Hash's, and the TWG once reset Woodside's approval date.

The public record shows only this much. Ten "Tokenomics Outcomes" posts were published on tokenomics-announce from 9 September to 29 October 2026. None of them reports a CIP-0111 review, an extension or a reduction.

Seven grants holding 67 weight have not published their milestones. CIP-0110, for example, says Apollo's "specific commitments, timelines, and commercial details will remain confidential". For these grants the community cannot tell how close the organisation is to earning its weight.

## 7. The config file against the chain

The config file is a public mirror. Node totals take effect on-chain through `UpdateSvRewardWeight` votes, and beneficiary lists are set in each SV node's own configuration.

- **Node totals.** Lighthouse records 69 executed weight votes. 17 of them carry a placeholder effective time, the day indexing began (6 July 2025). The other 52 have real effective times from May 2025 onwards. For 51 of these 52, the file reaches the same node total a median of 0.7 days after the vote takes effect (range −1.7 to 9.6 days).
  - The exception is GSF's 192.6, a CIP-0105 enforcement effective 1 May 2026. The file never showed it. A later commit "align[ed] public extraBeneficiaries with the actual SV configuration".
- **Timing at the round level.** The paid rate at sampled rounds shows where the file lagged the chain. For example, in late January 2026 the chain was already paying as if GSF's increase to 185.5 was in place: it took effect on 26 January, but the file showed it only on 4 February. These lags change the escrowed total by less than 1% (section 4).
- **A wrong field name.** From 5 February to 4 April 2026, nine commits gave Five North's beneficiary weights under `rewardWeightBps` instead of `weight`. Upstream #328 fixed it on 11 April. The on-chain node totals were right throughout. This analysis first read those lines as node totals, and the comparison with on-chain votes exposed the error.
- **More weight listed than the node had.** On four commits, GSF's beneficiaries in the file added up to more than the node's weight: three times by 0.45 (January and February 2026) and once by 2.9 (May 2026).
  - The on-chain contract would reject such a list. The SV app's `weightDistributionForSv` caps the last entries against the on-chain node weight.
  - If the node's real configuration had matched the file in January, the capped entry would have been the DTCC escrow party (9.55 instead of 10), until GSF's on-chain weight rose on 26 January.
  - The May excess of 2.9 equals the CIP-0105 cuts the node had already applied (Elliptic, Ledger, DFNS), so it was most likely an artefact of the stale file.
  - Either way, the entries that could have been capped were escrow parties, so no active participant would have been paid less.
- **A documentation mismatch.** The [tokenomics reference](https://docs.canton.network/overview/reference/tokenomics-of-gs) says "Unclaimed rewards beyond all tranches go to SV rewards". In the code, the SV tranche is computed after deducting the full validator and app tranches (`Issuance.daml`). Unused validator, app and SV issuance goes to an `UnclaimedReward` contract (`AmuletRules.daml`, around line 600).

## 8. Suggestions

1. **Publish an escrow ledger.** This would be one page, generated from the config repository and the mint votes. For each grant it would list the CIP, escrowed and earned weight, CC accrued in escrow, CC paid out, and milestone deadlines. The code in this repository already produces it.
2. **Record CIP-0111 reviews publicly, one line each.** Each line would state the outcome: met, extended to a date, or reduced. That would show the process working for the 29.6–49.0 weight tied to passed, dated milestones.
3. **Give the unclaimed pool provenance, or implement the burn that CIP-0111 asks for.** While `UnclaimedReward` holds only an amount, the reserve for escrowed SVs depends on an off-chain calculation.
4. **Resolve weight left behind by partial earnings.** Either remove it, as the CIPs describe for unmet milestones, or state where it is meant to go.
5. **Check the public file against the chain automatically.** A CI check could compare the file's node totals with `DsoRules` and validate field names. It would have caught the cases in section 7 the day they happened.

## Method and limits

- **Weights** come from every commit of `configs/MainNet/approved-sv-id-values.yaml`.
  - A party is classed as escrow if its name contains "ghost" or "escrow", or if it is hosted on a ghost validator.
  - "Unassigned" means `GhostSV-validator-1`.
  - Before March 2025 the file did not list beneficiaries, so all early weight shows as kept by the node.
- **Node totals** were checked against the live on-chain `DsoRules` (all 13 nodes) and against every executed weight vote with a real effective time.
- **Beneficiary lists** are SV node configuration and could not be checked on-chain. The Scan API, which would expose individual SV reward coupons, refused requests without an allowlisted IP.
- **Rewards** use the formula in `Issuance.daml` and the live issuance curve, summed per round.
  - Calendar dates are mapped to rounds with 241 sampled rounds from Lighthouse.
  - The formula was checked against the paid issuance per SV coupon at every sample.
  - Dates are commit dates. Operators may apply a change hours or days earlier or later.
- **Mint votes** come from Lighthouse (`lighthouse.cantonloop.com`), an independent indexer of on-chain vote requests. Votes repeating an executed vote's exact amount are counted once. The minted amounts themselves were not observed.
- **Deadlines and milestone weights** were read from the CIP texts (canton-foundation/cips at `92df641`).
  - Undated milestones, such as "180 days after go-live", are not counted as passed.
  - Weights given as a range ("Max +2") are recorded at their maximum.
- **TWG outcomes** were read from the tokenomics-announce RSS feed, which carries only the latest 20 posts.

## Prior work

Kaiko's *Methodology for Computing Unclaimed Super-Validator Canton Coin Rewards* (5 September 2025) sets out the calculation for Kaiko's own milestone claim. This article applies the same calculation to every escrowed grant over the whole history, and checks it against all on-chain milestone payouts. Its weight timeline matches the totals in Kaiko's tables (163.45, 164.45, 165.45, 166.45, 168.95).

## Reproduce it

```
git clone https://github.com/canton-foundation/configs
git clone https://github.com/furkan3152/canton-sv-weights && cd canton-sv-weights
pip install matplotlib
./run.sh ../configs        # rebuilds every table and figure, then runs the consistency tests
```

*Disclosure: I hold no CC and have no commercial relationship with any organisation named here.*
