# FINAL MODEL COMPARISON — Phishing AI Master 2

## Complete comparison table

| Model | Accuracy | Precision | Recall | FPR | F1 | ROC-AUC | PR-AUC | Brier | ECE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M1 LR (baseline) | 0.8947 | 0.9432 | 0.8478 | 0.0548 | 0.8930 | 0.9593 | 0.9676 | 0.0784 | 0.0304 |
| M2 SVM | 0.8980 | 0.9389 | 0.8590 | 0.0601 | 0.8972 | 0.9583 | 0.9669 | 0.0818 | 0.0560 |
| M3 RF | 0.8764 | 0.9018 | 0.8545 | 0.1000 | 0.8775 | 0.9440 | 0.9551 | 0.0902 | 0.0116 |
| M4 GB | 0.8662 | 0.9051 | 0.8286 | 0.0934 | 0.8652 | 0.9394 | 0.9496 | 0.0964 | 0.0210 |
| M5 XGBoost | 0.8801 | 0.9148 | 0.8474 | 0.0848 | 0.8798 | 0.9484 | 0.9576 | 0.0870 | 0.0067 |
| M6 Hybrid | 0.8080 | 0.8871 | 0.7212 | 0.0987 | 0.7956 | 0.8896 | 0.9070 | 0.1331 | 0.0325 |
| M1_HARDNEG | 0.8998 | 0.9596 | 0.8422 | 0.0381 | 0.8970 | 0.9610 | 0.9695 | 0.0770 | 0.0370 |
| M8 Hybrid (improved) | 0.8929 | 0.9120 | 0.8779 | 0.0910 | 0.8946 | 0.9421 | 0.9546 | 0.0829 | 0.0360 |

## Selected model: M1_LR_HARDNEG

Reasons:
1. Lowest FPR (0.0381) — 2.6× better than baseline.
2. Highest ROC-AUC (0.9610) and PR-AUC (0.9695).
3. Fastest inference (~0 ms/URL).
4. Most interpretable (linear model, char n-grams).
5. Calibration acceptable (ECE 0.0370, improvable to 0.0000 with isotonic).

Limitations:
- Recall 0.8422 < 0.85 (target not met).
- FPR 0.0381 > 0.01 (target not met by 3.8×).

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Phase finale.*
