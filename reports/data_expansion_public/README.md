# Public-data expansion: results index

This folder documents the use of three manually supplied public datasets:

- `data/LegitPhish Dataset`
- `data/Phishing Detection Dataset`
- `data/Phishing URL dataset`

`pyopdb` was supplied but has not been used (no credentials, no eligible
FULL_URL extraction yet).

All URL analysis is passive. No suspicious URL was fetched, resolved,
rendered, executed or interacted with. Original URL strings and labels were
preserved; normalization was used only for comparison and deduplication.

## Files

| file | contents |
|---|---|
| `01_data_audit.md` | dataset sizes, hashes, label mapping, validation, overlap, quarantine |
| `02_external_candidates.md` | external candidates EXP028–EXP036 and DEV/external-DEV comparison |
| `03_platform_and_auth.md` | Tranco ablation, auth reweighting, platform-aware variants, specialist, conclusion |
| `baseline_external_eval.json` | deployed `M1_LR_HARDNEG` on DEV, EXTERNAL_DEV and EXTERNAL_TEST |
| `external_test_hybrid.json` | held-out EXTERNAL_TEST comparison, baseline vs hybrid |
| `hybrid_roc_calibration.json` | hybrid calibration/ROC details |
| `hybrid_thresholds.json` | hybrid threshold sweep |
| `hybrid_variants.json` | EXP037–EXP041 Tranco ablation |
| `platform_aware.json` | EXP043–EXP044 platform masking/flags |
| `platform_specialist.json` | EXP045 two-branch platform specialist |
| `group_thresholds.json` | platform/ordinary group-threshold search |
| `dev_label_noise_audit.json` | passive DEV URL-shape audit (indicators only; not a relabeling) |

## Headline numbers (DEV, n = 22,586)

| model | recall @0.5 | FPR @0.5 | ROC-AUC | recall @FPR≤1% | 3-class strict recall (0.25/0.75) | 3-class FPR |
|---|---:|---:|---:|---:|---:|---:|
| deployed `M1_LR_HARDNEG` | 0.8422 | 0.0381 | 0.9610 | 0.7440 | 0.7383 | 0.0087 |
| `M1_HYBRID_REP_V2` | 0.9348 | 0.0560 | 0.9838 | 0.7657 | 0.8609 | 0.0265 |
| `PLATFORM_MASK` | 0.9550 | 0.0607 | 0.9863 | 0.7651 | 0.8868 | 0.0297 |

## Held-out EXTERNAL_TEST (n = 143,038, domain-disjoint)

| model | recall @0.5 | FPR @0.5 | ROC-AUC | 3-class 0.25/0.903 strict recall | review-inclusive | FPR |
|---|---:|---:|---:|---:|---:|---:|
| `M1_LR_HARDNEG` | 0.8796 | 0.0495 | 0.9603 | 0.7306 | 0.9392 | 0.00016 |
| `M1_HYBRID_REP_V2` | 0.9857 | 0.0711 | 0.9952 | 0.9485 | 0.9934 | 0.00325 |

## Decision

The production gate is **BLOCKED**. No candidate meets recall ≥ 0.85 and
FPR ≤ 0.01 simultaneously on DEV. `M1_LR_HARDNEG` remains deployed with the
frozen 0.25 / 0.75 thresholds; all candidates remain under
`models/versions/candidates/` and are not wired into the API or frontend.
