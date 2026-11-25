# FINAL OPTIMIZATION ATTEMPT — Phishing AI Master 2

## 1. What was changed

- Multi-round hard-negative mining (597 legitimate FPs from DEV added to TRAIN).
- LR regularization tuning (C ∈ {0.3, 0.5, 1.0}).
- Threshold optimization across all 6 original + enhanced models.
- Calibration comparison (Platt vs isotonic on M1).
- Allow-list policy layer (Tranco top-N domains).
- Enhanced feature engineering (brand position + Tranco rank + cleaned data).
- Cross-label domain removal from training data.

## 2. Experiments performed

| Exp | Model | Recall | FPR | ROC-AUC | ECE |
|---|---|---:|---:|---:|---:|
| EXP001 | M1 LR (baseline) | 0.8478 | 0.0548 | 0.9593 | 0.0304 |
| EXP002 | M2 SVM | 0.8590 | 0.0601 | 0.9583 | 0.0560 |
| EXP003 | M3 RF | 0.8545 | 0.1000 | 0.9440 | 0.0116 |
| EXP004 | M4 GB | 0.8286 | 0.0934 | 0.9394 | 0.0210 |
| EXP005 | M5 XGBoost | 0.8474 | 0.0848 | 0.9484 | 0.0067 |
| EXP006 | M6 Hybrid | 0.7212 | 0.0987 | 0.8896 | 0.0325 |
| EXP007-010 | M7 LR Enhanced | 0.723-0.728 | 0.087-0.091 | 0.895 | 0.018 |
| EXP011 | M1_HARDNEG | 0.8422 | 0.0381 | 0.9610 | 0.0370 |
| EXP013-018 | M8 Hybrid improved | 0.878-0.888 | 0.091-0.107 | 0.942 | 0.035-0.036 |
| EXP019-021 | FINAL_LR (C tuning) | 0.819-0.842 | 0.043-0.038 | 0.954-0.961 | 0.049-0.037 |
| Calibration | M1 isotonic | — | — | 0.9598 | 0.0000 |
| Allow-list | M1 + Tranco top 10k | 0.8209 | 0.0298 | — | — |
| Allow-list | M1 + Tranco top 50k | 0.7922 | 0.0164 | — | — |

## 3. Were both targets achieved?

**NO.** No configuration satisfies both Recall ≥ 0.85 AND FPR ≤ 0.01 simultaneously.

- Best recall with FPR constraint: M2 SVM = 0.8590 (FPR 0.0601).
- Best FPR with recall constraint: M1_HARDNEG = 0.0381 (recall 0.8422).
- At threshold 0.4774: recall 0.8500, FPR 0.0469 (4.7× target).

## 4. Final selected model

**M1_LR_HARDNEG** (Logistic Regression, char TF-IDF, hard-negative mining).

Justification:
- Lowest FPR (0.0381) among all models.
- Highest ROC-AUC (0.9610) and PR-AUC (0.9695).
- Fastest inference (~0 ms/URL).
- Most interpretable.
- Calibration acceptable (ECE 0.0370, improvable to 0.0000 with isotonic).

## 5. Final production status

**STATUS = BLOCKED** — targets not achieved.

## 6. Tests

7/7 tests pass. API functional. Model loaded and predicting.

## 7. Files created or modified

- `models/versions/metadata.json` (updated to FINAL_LR_C1.0)
- `reports/technical/FINAL_OPTIMIZATION_ATTEMPT.md`
- `reports/technical/FINAL_MODEL_COMPARISON.md`
- `reports/technical/FINAL_ERROR_ANALYSIS.md`
- `reports/FINAL_PROJECT_DECISION.md`
- `reports/tables/final_threshold_results.json`

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Phase finale (Optimisation).*
