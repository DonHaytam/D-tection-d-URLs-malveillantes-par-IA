# FINAL PROJECT DECISION — Phishing AI Master 2

## Decision

**Scenario B** — Targets not achieved. Optimization phase officially closed.

## Final selected model

**M1_LR_HARDNEG** (Logistic Regression, char TF-IDF 3-5, hard-negative mining).

## Justification

1. Lowest FPR (0.0381) among all 18 experiments.
2. Highest ROC-AUC (0.9610) and PR-AUC (0.9695).
3. Fastest inference (~0 ms/URL).
4. Most interpretable.
5. Calibration acceptable (ECE 0.0370, improvable to 0.0000 with isotonic).

## Production status

**STATUS = BLOCKED** — targets not achieved (Recall 0.8422 < 0.85, FPR 0.0381 > 0.01).

## Tests

7/7 pass. API functional. Model loaded and predicting.

## Conclusion

The application is functional and deployable as an experimental/research tool. The production-readiness gate remains BLOCKED due to unmet targets. Scientific integrity is preserved — no metrics were fabricated or manipulated.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Décision finale.*
