# Platform-aware and auth-focused experiments (EXP037–EXP044)

All experiments below use only real `FULL_URL` records from the project
splits and the audited external pool. No URL was fetched, resolved, rendered
or executed. DEV was used for selection; LOCKED_TEST and the project's
internal test splits were not used.

## 1. Tranco-feature ablation (EXP037–EXP041)

Five hybrid variants were trained on TRAIN + 40K external rows with identical
char TF-IDF and model settings. Only the reputation-feature block changed.

| variant | numeric cols | DEV recall @0.5 | DEV FPR @0.5 | DEV AUC | DEV recall @FPR≤1% | external DEV recall @FPR≤1% |
|---|---:|---:|---:|---:|---:|---:|
| HYB_V2_FULL | 40 | 0.9348 | 0.0560 | 0.9838 | **0.7657** | 0.9458 |
| HYB_V2_NOPRESENCE | 35 | 0.9328 | 0.0578 | 0.9832 | 0.7566 | 0.9455 |
| HYB_V2_RANKONLY | 34 | 0.9291 | 0.0629 | 0.9811 | 0.7399 | 0.9398 |
| HYB_V2_NOTRANCO | 30 | 0.8588 | 0.0630 | 0.9631 | 0.7116 | **0.9561** |
| HYB_V2_BASEONLY | 28 | 0.8433 | 0.0561 | 0.9610 | 0.6856 | 0.9508 |

Removing Tranco improves external-DEV recall at the 1% FPR point but loses
7–8 points of DEV recall. Binary presence/absence features therefore help on
DEV and overfit the external distribution; neither ablation clears the gate.

## 2. Auth-focused reweighting (EXP042)

`AUTH_W5` upweights the 118 real legitimate authentication URLs in
TRAIN + external sample by 5× (no synthetic URLs). It reduces the mean score
of legitimate auth URLs but also lowers ranking quality:

- DEV @0.5: recall 0.8453, FPR 0.0574, AUC 0.9564
- DEV @FPR≤1%: recall 0.7093 (vs 0.7657 for the hybrid)
- DEV legitimate-auth subset: mean score 0.3798; 35.7% ≥0.5; 10.7% ≥0.75
- External DEV @0.5: recall 0.9616, FPR 0.0062, AUC 0.9963

The external FPR is excellent, but the DEV trade-off is unacceptable.
Higher weights (10×, 20×) were stopped after the 5× result showed the
direction was wrong; they are not reported as completed experiments.

## 3. Platform-aware reputation (EXP043–EXP044)

Shared platforms (free hosts, shorteners, document/form hosts, cloud buckets)
host both legitimate pages and phishing pages. The Tranco rank of their
registrable domain describes the platform, not the page. In DEV, 890 URLs are
on such platforms:

| platform type | legitimate | phishing |
|---|---:|---:|
| free host | 14 | 574 |
| shortener | 5 | 154 |
| document host | 29 | 93 |
| cloud bucket | 3 | 18 |
| **total** | **51** | **839** |

Two variants were tested: masking Tranco features for platform URLs
(`PLATFORM_MASK`) and adding explicit platform interactions (`PLATFORM_FLAGS`).

| variant | DEV recall @0.5 | DEV FPR @0.5 | DEV AUC | DEV recall @FPR≤1% | DEV 3-class strict recall | DEV 3-class FPR | external DEV FPR @0.5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| HYB_V2_FULL | 0.9348 | 0.0560 | 0.9838 | 0.7657 | 0.8609 | 0.0265 | 0.0701 |
| PLATFORM_MASK | **0.9550** | 0.0607 | **0.9863** | 0.7651 | **0.8868** | 0.0297 | 0.0502 |
| PLATFORM_FLAGS | 0.9474 | 0.0661 | 0.9852 | 0.7624 | 0.8800 | 0.0316 | 0.0424 |

Masking clearly improves the operating range used by the three-class policy
(+2.6 points strict recall, +1.9 points AUC) and reduces external-DEV FPR, but
it does not move the 1%-FPR tail. The platform interaction flags add no value
and slightly hurt DEV.

Crucially, EXTERNAL_DEV contains only 4 platform URLs (all phishing) and no
legitimate platform pages, so the platform branch cannot be validated on
external data. Its apparent DEV gain may not transfer, and it is not a
deployment candidate on its own.

## 4. Interpretation

The remaining DEV errors are structural, not just model-capacity errors:

- 839 DEV phishing URLs are hosted on shared platforms, where the URL string
  alone often carries no page-level reputation signal (opaque shortener codes,
  Google Forms IDs, cloud bucket paths).
- EXTERNAL_TRAIN contains 21,400 platform rows, but almost all legitimate
  platform rows are free hosts (8,860); document hosts and shorteners have
  fewer than 20 legitimate examples each. This is not enough to learn a
  reliable page-level reputation model for those platforms.
- The strict gate (recall ≥ 0.85 at FPR ≤ 0.01) remains unmet. The best
  strict-tail result is still the hybrid at 0.7657, and no ablation or
  reweighting closes the gap.

## 5. Two-branch platform specialist (EXP045)

A path-focused specialist was trained on the 25,830 platform rows in
TRAIN + EXTERNAL_TRAIN (10,022 legitimate / 11,914 phishing free-host rows,
plus 30/3,108 shortener, 10/355 document-host and 29/362 cloud rows). At
inference, platform URLs were routed to the specialist and all other URLs to
`PLATFORM_MASK`.

The specialist failed on DEV:

- Platform-subset AUC: **0.526** (near random), versus **0.898** for the
  full-URL `PLATFORM_MASK` model on the same 890 URLs.
- Combined DEV recall at FPR ≤ 1%: **0.7407**, below the 0.7651 of the
  full model alone.
- The path-only representation loses the host-identity signal that makes
  platform pages distinguishable, while the external legitimate platform
  rows are overwhelmingly free hosts (8,860) and do not cover document hosts
  or shorteners.

Group-specific thresholds were also searched (separate threshold for
platform vs ordinary URLs under the same global 1% FPR constraint):

- Best DEV result: recall **0.7655** (platform threshold 0.920, other 0.918),
  statistically identical to the single-threshold 0.7631–0.766.
- Platform-subset recall at that point was 0.7938 with 9.8% platform FPR; the
  global budget has no room to lower the platform threshold further.

## 6. Conclusion and deployment decision

The new public data and the platform-aware representation improve the model
at the operating points used for triage:

- PLATFORM_MASK: DEV recall 0.9550 at threshold 0.5 (deployed baseline:
  0.8422) and three-class strict recall 0.8868 at 0.25/0.75 (deployed:
  0.7383), but DEV FPR is 0.0607 / 0.0297, above the 1% gate.
- HYBRID_EXT40K: the best held-out external-test result (recall 0.9857,
  FPR 0.0711 at 0.5; three-class 0.9485 strict / 0.9934 review-inclusive at
  0.25/0.903), but it still fails the DEV gate.

No candidate satisfies **simultaneous** recall ≥ 0.85 and FPR ≤ 0.01 on DEV.
The production artifact therefore remains `M1_LR_HARDNEG` with the frozen
0.25 / 0.75 thresholds. `M1_HYBRID_REP_V2` and the platform variants stay in
`models/versions/candidates/` as documented experimental candidates. EXP027
remains invalidated because its labels were inverted and must not be cited.

The residual error is structural: 839 of 11,701 DEV phishing URLs (7.2%) are
on shared platforms whose URL string does not identify the page, and external
legitimate data cannot supervise those platform types. Reaching the strict
gate would require page-level evidence (content, redirects, certificates) or
a review-inclusive operating mode, both outside the current passive
URL-string-only scope.
