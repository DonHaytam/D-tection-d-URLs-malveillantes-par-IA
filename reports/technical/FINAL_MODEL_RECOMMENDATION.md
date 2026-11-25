# FINAL MODEL RECOMMENDATION — Phishing AI Master 2 (Phase 15)

## Decision

**Scenario B** — Targets not achieved. Optimization phase officially closed.

## Final selected model

**M1_LR_HARDNEG** (Logistic Regression, char TF-IDF 3-5, hard-negative mining).

## Justification

1. **Lowest FPR** among single models (0.0381).
2. **Highest ROC-AUC** among single models (0.9610).
3. **Fastest inference** (~0 ms/URL).
4. **Most interpretable** (linear model, char n-grams).
5. **Best calibration** among high-recall models (ECE 0.0370).
6. **Ensemble** (soft voting) improves recall (0.8698) and AUC (0.9741) but degrades ECE (0.0808) and increases latency.

## Ensemble vs single model

The soft voting ensemble (M1+M2+M5) achieves Recall 0.8698 (≥ 0.85 ✅) and FPR 0.0353 (still > 0.01). While better than M1 alone, it does not meet the FPR target. The ensemble is recommended as a future improvement if computational cost is acceptable.

## Production status

**STATUS = BLOCKED** — targets not achieved (Recall 0.8422 < 0.85, FPR 0.0381 > 0.01 for M1; Recall 0.8698 ≥ 0.85 but FPR 0.0353 > 0.01 for ensemble).

## Final recommendation

Deploy M1_LR_HARDNEG as the experimental model. The application is functional but not production-ready. The production gate remains BLOCKED.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Phase 15 (Recommandation finale).*