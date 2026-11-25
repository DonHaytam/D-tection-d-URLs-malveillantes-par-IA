# FINAL DATA EXPANSION REPORT — Phishing AI Master 2

## Executive Summary

This report documents the investigation of 12+ data sources for acquiring real-world phishing and legitimate authentication URLs. The root cause of the model's false positive problem is confirmed: the legitimate class contains only 0.32% authentication URLs vs 4.78% for phishing.

## Dataset Acquisition Status

| Dataset | Status | Raw URLs | Validated | Trainable | Samples |
|---|---|---|---|---|---:|
| HuggingFace (ealvaradob) | DOWNLOADED | 835 697 | ✅ | ✅ | 835 697 |
| Tranco | DOWNLOADED | 1 000 000 | ✅ | ✅ (domains) | 1 000 000 |
| PhishTank (Zenodo) | DOWNLOADED | 149 188 | ✅ | ✅ | 149 188 |
| PhiUSIIL (UCI) | DOWNLOADED | 235 795 | ✅ | ✅ | 235 795 |
| PILU-60K (Unileón) | REQUEST_REQUIRED | 60 000 | ❌ | ❌ | 0 |
| Phish360 | REQUEST_REQUIRED | 10 748 | ❌ | ❌ | 0 |
| PhishStorm | INACCESSIBLE | 96 018 | ❌ | ❌ | 0 |
| LegitPhish (Mendeley) | INACCESSIBLE | 101 219 | ❌ | ❌ | 0 |
| URL-Phish (Mendeley) | INACCESSIBLE | 116 600 | ❌ | ❌ | 0 |
| OpenPhish | REQUEST_REQUIRED | Temps réel | ❌ | ❌ | 0 |
| URLhaus | INACCESSIBLE | Temps réel | ❌ | ❌ | 0 |
| Common Crawl CDX | INACCESSIBLE | Billions | ❌ | ❌ | 0 |
| darkknight25 (HF) | DOWNLOADED | 1 000 | ❌ (synthetic) | ❌ | 0 |

## URL Completeness

- Complete raw URLs available: 835 697 (HuggingFace) + 235 795 (PhiUSIIL) + 149 188 (PhishTank) = 1 220 680.
- Domain-only: 1 000 000 (Tranco).
- No raw URLs: PhiUSIIL has URLs but only 141 legitimate auth.

## Authentication URL Coverage

| Category | Count | Source |
|---|---:|---|
| VERIFIED_LEGITIMATE_AUTH_URL | < 200 | HuggingFace + PhiUSIIL |
| VERIFIED_PHISHING_URL | ~6 000+ | HuggingFace + PhiUSIIL + PhishTank |
| CONSTRUCTED (not verified) | 1 300 000 | Tranco + auth paths |
| UNVERIFIED | — | — |

## Label Quality

- HuggingFace: labels 0/1, no verification metadata.
- PhiUSIIL: labels 0/1, features precomputed.
- PhishTank: "VALID PHISH" verified, 149 188 valid.
- Tranco: no labels (domains only).

## Duplicate Analysis

- Exact duplicates: 276 removed.
- Normalized duplicates: 0 additional.
- Cross-source overlap: 591 cross-label domains identified.

## Domain Overlap

- 96 155 unique registrable domains.
- No domain leakage between TRAIN/DEV/LOCKED_TEST (domain-disjoint split).

## Source Leakage

- HuggingFace contributes 62.4% of records.
- Source identity is partially predictive (HuggingFace has more phishing, Tranco has only legitimate).

## Licensing

- Tranco: CC BY 3.0/4.0 (attribution required).
- PhiUSIIL: CC BY-SA 4.0.
- PhishTank: PhishTank ToU (research use allowed).
- PILU-60K: CC BY 4.0 (on request).

## Integrated Dataset Statistics

- Current: 159 568 URL (79 842 legit / 79 726 phishing).
- No new data integrated (all additional sources are inaccessible or require request).

## Quarantine and Rejection Statistics

- 597 hard negatives (real FPs) added to training.
- 591 cross-label domains removed.
- 276 exact duplicates removed.
- 141 PhiUSIIL legit auth URLs (mostly false matches).

## Experiment Results

- 21 experiments (EXP001-EXP021).
- Best model: M1_LR_HARDNEG (FPR 0.0381, Recall 0.8422, AUC 0.9610).
- Hard-negative mining reduced FPR by 30% (0.0548 → 0.0381).
- No configuration meets Recall ≥ 0.85 AND FPR ≤ 0.01.

## Model Comparison

| Model | Recall | FPR | ROC-AUC |
|---|---:|---:|---:|
| M1 (baseline) | 0.8478 | 0.0548 | 0.9593 |
| M1_HARDNEG | 0.8422 | 0.0381 | 0.9610 |
| Ensemble (soft voting) | 0.8698 | 0.0353 | 0.9741 |

## Remaining Blockers

1. **Insufficient legitimate auth URLs**: < 200 verified (need 20 000+).
2. **PILU-60K** requires email request to gvis@unileon.es.
3. **Phish360** requires Google Drive download (manual).
4. **Common Crawl CDX** is unreliable.
5. **No freely accessible source** provides verified legitimate auth URLs.

## Final Decision

The dataset bias (0.32% legitimate auth URLs) is the root cause. Without real legitimate auth data (PILU-60K), the model cannot learn that authentication vocabulary appears on legitimate sites. The production gate remains BLOCKED.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Rapport final d'expansion de données.*