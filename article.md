# The Ghost Weight: how much Canton Super Validator reward weight is waiting on a promise

*November 2026. Every number in this article is reproduced by the code and data in [github.com/furkan3152/canton-sv-weights](https://github.com/furkan3152/canton-sv-weights). Figures are as of the config commit of 1 November 2026 and on-chain state of 5 November 2026.*

## Summary

- Total Super Validator (SV) reward weight on Canton MainNet grew from **130 to 404.45** between January 2025 and November 2026.
- **180.22 of that weight (44.6%)** belongs to no operating SV. 177.125 sits on 33 escrow ("ghost") parties for organisations that must first meet milestones, and 3.095 sits in an unassigned pool.
- Escrowed weight takes its share of every round's SV rewards, but the coupons are never claimed. They expire into the network's unclaimed-reward pool. At today's issuance this is about **847 million CC a year**, and about **1.83 billion CC** since escrow began in June 2025.
- On-chain mint votes that pay milestone rewards out of that pool match this model closely. For 19 grants, the approved mints total **521 million CC** against a modelled **570 million CC** (ratio 0.91).
- Of **260.5 weight** placed in escrow, **65.28 has been earned**, **15.05 removed**, **3.045 released without being earned**, and **177.125 is still escrowed**.
- **69 escrowed weight across 16 grants** is past every deadline that can be dated from the CIP texts. That is the point at which CIP-0111 requires a review. Another **67 weight across 7 grants** has milestones that were never published.
- The on-chain pool records only an amount. It cannot tell escrowed rewards from any other unclaimed reward, so the escrow reserve exists only as an off-chain calculation. This repository publishes that calculation for the whole network.

None of this is hidden. The escrow model is written into the CIPs, and every weight change is a public commit and an on-chain vote. What has been missing is the whole picture, checked against the chain. This article puts it together and ends with five suggestions.

## 1. How SV rewards are paid

Each round (10 minutes), a fixed share of new Canton Coin goes to Super Validators. In the Splice source (`Issuance.daml`, `computeIssuingRoundParameters`), the SV tranche is the round's issuance, minus the Development Fund share (CIP-0082) and the validator and app shares, divided by the total SV reward weight:

```
svTranche                 = amuletToIssuePerYear / roundsPerYear × (1 − developmentFund) × (1 − validator% − app%)
issuancePerSvRewardCoupon = svTranche / totalSvRewardWeight
```

Today the curve issues 10 billion CC a year. The SV share is 20%, after 5% goes to the Development Fund, so the SV tranche is **1.9 billion CC a year**. This can be checked on-chain: the latest closed round (120,404) paid 0.0089378571 CC per SV coupon per basis point of weight. Multiplied by the 4,044,500 basis points of total weight and 52,560 rounds a year, that gives exactly 1.900 billion CC.

Every unit of weight earns the same amount, so every new unit reduces what the others earn.

The weight of each SV node, and how a node passes part of its weight to other parties ("beneficiaries"), is published in [`canton-foundation/configs`](https://github.com/canton-foundation/configs), file `configs/MainNet/approved-sv-id-values.yaml`. The file has 121 commits since 22 January 2025. Node totals are also set on-chain by `UpdateSvRewardWeight` votes. Section 7 shows that the two agree.

Weight is economic, not political. Governance votes count one vote per SV: 9 of 13 under the code's threshold `ceil((n + f + 1) / 2)`. The Global Synchronizer Foundation (GSF) node carries 195.3 weight, 48.3% of the total, and has one vote.

## 2. The ghost weight

Since mid-2025, milestone-based CIPs have given organisations SV weight that they earn by meeting milestones: an integration, a product launch, a volume target. Until a milestone is met, the weight sits on an escrow party hosted by another node. In the config file these parties are named `<Organisation>-ghost-1` (or `-Escrow-1`). They are hosted on three ghost validators: GSF's `GhostSV-validator-1`, MPC Holding's `MPCH-GHOSTvalidator-1` and Five North's `5nghost-mainnet-1`.

![Figure 1](figures/weight-classes.png)

*Figure 1. SV reward weight by holder, from every commit of the config file.*

On 1 November 2026:

| Holder | Weight | Share |
|---|---|---|
| Kept by the 13 SV node operators | 83.625 | 20.7% |
| Passed to active beneficiaries | 140.605 | 34.8% |
| **Escrowed on 33 ghost parties** | **177.125** | **43.8%** |
| **Unassigned pool (`GhostSV-validator-1`)** | **3.095** | **0.8%** |
| Total | 404.45 | |

The escrow is held by GSF (97), MPC Holding (53.125) and Five North (27).

Escrowed weight was zero until 3 June 2025 and passed a third of all weight on 5 November 2025. It has stayed between 31% and 45% since then.

## 3. Where escrowed rewards go

The Splice code shows the whole path.

1. **Coupons are created for escrow parties.** Each round, an SV node calls `DsoRules_ReceiveSvRewardCoupon` with its beneficiary list. The contract requires "Total beneficiary weight matches SV operator weight" and creates one `SvRewardCoupon` per beneficiary, escrow parties included.
2. **The coupons expire unclaimed.** The escrow party's wallet does not mint. CIP-0066 says the host "disables the final minting action for all escrowed SV parties". After the round closes, `DsoRules_ClaimExpiredRewards` expires the coupons and creates an `UnclaimedReward` contract for `svRewardsWeight × issuancePerSvRewardCoupon`. Unclaimed validator and app rewards go into the same contract.
3. **The pool keeps only an amount.** `UnclaimedReward` has two fields, `dso` and `amount`. `AmuletRules_MergeUnclaimedRewards` merges many of them into one. Once rewards are in the pool, nothing on-chain records whether they came from an escrow party or from any other unclaimed reward.
4. **Milestone payouts are votes.** When the Tokenomics Working Group (TWG) agrees that a milestone is met, SVs vote on `CreateUnallocatedUnclaimedActivityRecord`, which names a beneficiary, an amount and a reason. An SV then allocates it with `DsoRules_AllocateUnallocatedUnclaimedActivityRecord`. That call archives `UnclaimedReward` contracts covering the amount, and the organisation mints the coins.

There have been 53 such votes since October 2025; 48 were executed.

| Kind | Approved amount |
|---|---|
| Milestone payouts (repeated votes counted once) | 532.3 million CC |
| CIP-0067 one-time allocation of historical unclaimed rewards to GSF (3 November 2025) | 1,617.8 million CC |
| Corrections where an external party ID had prevented minting | 8.8 million CC |

CIP-0067 transferred all unclaimed rewards "not explicitly reserved under any approved milestone-based SV reward schedule". The escrow reserve is therefore a number that has to be calculated off-chain.

CIP-0111 (approved 23 April 2026) recognises this. When ghost weight is removed, its coupons "should be burned to indicate the tokens associated with them are no longer in the unminted pool", and "enabling this functionality will require a change to the Canton Coin SV Reward DAML model". At Splice commit `2930ba1` (5 November 2026), no such choice exists. The CIP gives an off-chain formula for the unminted supply instead.

## 4. How much it is

![Figure 2](figures/dilution.png)

*Figure 2. CC per year earned by one unit of SV weight. The fall on 20 January 2026 is the scheduled curve step from 20 to 10 billion CC a year, when the SV share also fell from 48% to 20%.*

A unit of weight earned about **73.8 million CC a year** in January 2025. Today it earns about **4.7 million CC a year**. The scheduled curve explains most of the fall: if total weight had stayed at 130, a unit would still earn about 14.6 million CC a year. Weight growth explains the rest.

At the current curve, 44.6% of the SV tranche, about **847 million CC a year**, is assigned to escrow and unassigned weight. Since escrow began on 3 June 2025, the total is about **1.83 billion CC** to 1 November 2026. This total applies the Development Fund share from the CIP-0082 package vote, effective 12 February 2026 at 19:24 UTC.

These coins are not lost. They wait in the unclaimed pool until governance mints them to an organisation that met its milestones, or until a CIP-0111 reduction marks them for burning.

## 5. Checking the model against the chain

The model makes a testable prediction. When a milestone is met, the organisation should be paid roughly what its earned weight accrued while it was escrowed. TWG calculations follow the same rule: Kaiko's published methodology for its own claim splits the period into intervals of constant total weight and sums `hours × weight × hourly SV rewards / total weight`.

![Figure 3](figures/mints.png)

*Figure 3. For each grant: the CC its earned weight accrued in escrow according to the model, against the mints approved by on-chain votes.*

For the 19 grants where the comparison applies, approved mints total **521 million CC** against **570 million CC** in the model. The per-grant ratio runs from 0.80 to 0.96, with a median of 0.91. The model runs a little high for three reasons it does not capture:

- The TWG counts from when an operator confirmed the weight, which can be later than the config commit.
- It ignores rounds an SV node did not collect.
- It uses commit dates, not operator times.

Three grants are left out because their payouts follow a different rule:

- **CIP-0102/CIP-0114** (Tharimmune / Canton Strategic Holdings): most of the active weight is earned under the CIP-0114 programme.
- **CIP-0115** (Société Générale): two mints were made while its escrow stayed at 8.

The agreement means the 1.83 billion CC figure is not a theoretical upper bound. It is the same calculation the network already uses to pay milestones, applied to all escrowed weight.

## 6. Promises and outcomes

Grouping every beneficiary row by the CIP in its comment gives the history of 38 milestone grants and 84 weight changes. Each change links to its commit. Every unit of escrow is accounted for, and the code checks this identity for each grant:

| | Weight |
|---|---|
| Placed in escrow | 260.5 |
| Earned (escrow released to the organisation) | 65.28 |
| Released without being earned | 3.045 |
| Removed under CIP-0111 or by correction | 15.05 |
| **Still escrowed** | **177.125** |

- 6 grants are fully earned, 15 are partly earned, 15 have earned nothing yet, and 2 were removed.
- For the 20 grants that met a milestone, the first one came after a median of **92 days**.
- **The only CIP-0111 removals so far** are Monstera FZE (5) and Woodside AI (10). The steps were: CIPs marked withdrawn on 6 May 2026, an on-chain vote effective 15 May, and the config change on 17 May, about nine months after the weight was added.
- **Partial earnings leave weight behind.** When an organisation earns less than the escrow released for a milestone, the difference is not removed. It moves to the unassigned `GhostSV-validator-1` pool. Fireblocks' escrow is fully closed, but 2.42 of its weight now sits in that pool. Together with smaller remainders from Talos, BitGo and Wormhole and a 0.05 correction to Ubyx, the pool holds 3.095 weight, about 14.5 million CC a year, still accruing to the unclaimed pool.
- CIP-0105 lock enforcement withheld and restored active weight several times (Taurus, Ledger, Quantstamp, Elliptic, DFNS). Net of reversals, 1.2 weight of milestone grants is withheld today.

### Deadlines

The CIP texts set deadlines for most milestones, often "+180 days from CIP approval". The escrow on 1 November 2026 compares with those deadlines as follows:

![Figure 4](figures/escrow-status.png)

*Figure 4. Escrowed weight by deadline status.*

| Status | Grants | Escrowed weight |
|---|---|---|
| Every dated deadline has passed | 16 | 69.0 |
| Some dated deadlines have passed | 2 | 12.0 |
| Milestones not published | 7 | 67.0 |
| Deadlines still ahead | 5 | 29.1 |

A passed deadline does not mean the weight is forfeit. CIP-0111 says: "At a minimum, the TWG must review SVs for potential weight reduction whenever the deadline for a milestone associated with a milestone-based SV CIP passes." Removal then needs a recommendation, an off-chain SV vote posted on the tokenomics-announce list, and an on-chain vote. Some deadlines may have been extended; Woodside's approval date, for example, was reset once by the TWG. Some milestones also run from another event rather than a date.

What the public record shows is narrower. For 16 grants holding 69 weight, every dated deadline has passed. In the nine "Tokenomics Outcomes" posts published from 9 September to 29 October 2026, none reports a CIP-0111 review, extension or reduction.

Seven grants holding 67 weight did not publish their milestones. CIP-0110, for example, says Apollo's "specific commitments, timelines, and commercial details will remain confidential". For these grants the community cannot tell how close the organisation is to earning its weight.

## 7. The config file against the chain

The config file is a public mirror. Node totals take effect on-chain through `UpdateSvRewardWeight` votes, and beneficiary lists are set in each SV node's own configuration. Comparing the two shows how well the mirror tracks the chain.

- **Node totals.** Since Lighthouse began indexing in July 2025, there have been 52 executed weight votes. For 51 of them the file reaches the same node total, a median of 0.7 days after the vote takes effect (range −1.7 to 9.6 days). The exception is GSF's 192.6 (1 May 2026, a CIP-0105 enforcement). The file never showed that value; a later commit "align[ed] public extraBeneficiaries with the actual SV configuration".
- **A wrong field name.** From 5 February to 11 April 2026, nine commits gave Five North's beneficiary weights under `rewardWeightBps` instead of `weight`. Upstream #328 fixed it. The on-chain node totals were right throughout. This analysis first read those lines as node totals; the comparison with on-chain votes exposed the problem.
- **More weight listed than the node had.** On four commits (January, February and May 2026), GSF's beneficiaries added up to more than the node's weight: 0.45 more, and once 2.9 more. The on-chain contract would reject such a list, so the SV app must cap it before submitting. `weightDistributionForSv` in `SvUtil.scala` walks the list in order and caps the last entries. The entries capped were the DTCC escrow party (9.55 instead of 10, for about 23 days) and the Société Générale escrow party (5.1 instead of 8, for about one day). Both are escrow parties, so no active participant was paid less.
- **A documentation mismatch.** The [tokenomics reference](https://docs.canton.network/overview/reference/tokenomics-of-gs) says "Unclaimed rewards beyond all tranches go to SV rewards". In the code, unclaimed validator, app and SV rewards all go to `UnclaimedReward` contracts (section 3).

## 8. Suggestions

1. **Publish an escrow ledger.** One page, generated from the config repository and the mint votes, listing each grant: CIP, escrowed weight, earned weight, CC accrued in escrow, CC paid out, and deadlines. The code in this repository already produces it.
2. **Record CIP-0111 reviews publicly, one line each.** For example: met, extended to a date, or reduced. That would show the review process is working for the 69 weight past its deadlines.
3. **Give the unclaimed pool provenance, or implement the burn CIP-0111 asks for.** While `UnclaimedReward` holds only an amount, the reserve for escrowed SVs depends on an off-chain calculation.
4. **Resolve weight left behind by partial earnings.** Either remove it, as the CIPs describe for unmet milestones, or state where it is meant to go.
5. **Check the public file against the chain automatically.** A CI check that compares the file's node totals with `DsoRules`, and validates field names, would have caught the cases in section 7 the day they happened.

## Method and limits

- **Weights** come from every commit of `configs/MainNet/approved-sv-id-values.yaml`. A party is classed as escrow if its name contains "ghost" or "escrow", or if it is hosted on a ghost validator. "Unassigned" means `GhostSV-validator-1`.
- **Node totals** were checked against the live on-chain `DsoRules` (all 13 nodes) and against every executed weight vote since July 2025. **Beneficiary lists** are SV node configuration and could not be checked on-chain. The Scan API, which would expose individual SV reward coupons, refused requests without an allowlisted IP.
- **Rewards** use the formula in `Issuance.daml` and the live issuance curve, assuming every round's coupons were created. The formula was checked against the on-chain issuance per SV coupon. Dates are commit dates; operators may apply a change hours or days earlier or later.
- **Mint votes** come from Lighthouse (`lighthouse.cantonloop.com`), an independent indexer of on-chain vote requests. A vote creates a record that can expire. Votes repeating an executed vote's exact amount are counted once, but the actual minted amounts were not observed.
- **Deadlines** were extracted from the CIP texts (canton-foundation/cips at `92df641`). Undated milestones, such as "180 days after go-live", are not counted as passed. TWG outcomes were read from the tokenomics-announce RSS feed, which carries only the latest 20 posts.
- Before March 2025 the file did not list beneficiaries, so all early weight shows as kept by the node.

## Prior work

Kaiko's *Methodology for Computing Unclaimed Super-Validator Canton Coin Rewards* (September 2025) sets out the per-claim calculation that the TWG uses. This article applies the same calculation to every escrowed grant over the whole history and checks it against the on-chain mint votes. Its weight timeline matches the totals in Kaiko's tables (163.45, 164.45, 165.45, 166.45, 168.95).

## Reproduce it

```
git clone https://github.com/canton-foundation/configs
git clone https://github.com/furkan3152/canton-sv-weights && cd canton-sv-weights
pip install matplotlib
./run.sh ../configs        # rebuilds every table and figure, then runs the consistency tests
```

*Disclosure: I hold no CC and have no commercial relationship with any organisation named here.*
