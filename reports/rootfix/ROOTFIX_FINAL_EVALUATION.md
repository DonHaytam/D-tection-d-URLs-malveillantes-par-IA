# ROOTFIX FINAL EVALUATION — Phishing AI Master 2

## Final selected model

**M1_LR_HARDNEG** (Logistic Regression, char TF-IDF 3-5, hard-negative mining from real FPs).

## Metrics (DEV, threshold 0.5)

| Metric | Value |
|---|---:|
| Accuracy | 0.8998 |
| Precision | 0.9596 |
| Recall | 0.8422 |
| FPR | 0.0381 |
| F1 | 0.8970 |
| ROC-AUC | 0.9610 |
| PR-AUC | 0.9695 |
| Brier | 0.0770 |
| ECE | 0.0370 |

## Threshold optimization (three-class)

Best thresholds: 0.25 / 0.75 (FPR 0.0087, Recall 0.7383, F1 0.8455, review rate 20.4%).

## Diagnostic URLs (old → new)

| URL | Old score | New score |
|---|---:|---:|
| paypal.com/signin | 96.18% | 78.85% |
| dropbox.com/login | 89.39% | 57.34% |
| github.com/login | 69.01% | 20.29% |
| google signin | 53.20% | 4.28% |
| amazon signin | 67.50% | 29.94% |
| apple account | 70.79% | 23.55% |
| linkedin login | — | 5.95% |

## Production gate

**STATUS = BLOCKED** — Recall 0.8422 < 0.85, FPR 0.0381 > 0.01.

## Root cause

The dataset teaches "login = phishing" because legitimate URLs contain authentication keywords in only 0.32% of cases vs 4.78% for phishing. This is a dataset construction bias, not a model bug.

## Conclusion

The model has been improved (FPR reduced 30% via hard-negative mining) but cannot meet the production targets without real legitimate authentication data. The production gate remains BLOCKED.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Évaluation finale rootfix.*