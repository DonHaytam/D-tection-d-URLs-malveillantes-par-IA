# MODEL COMPARISON REPORT — Phishing AI Master 2 (Phase 14)

## Complete comparison table

| Model / Ensemble | Accuracy | Precision | Recall | FPR | F1 | ROC-AUC | PR-AUC | ECE | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| M1 LR (baseline) | 0.8947 | 0.9432 | 0.8478 | 0.0548 | 0.8930 | 0.9593 | 0.9676 | 0.0304 | ~0 ms |
| M2 SVM | 0.8980 | 0.9389 | 0.8590 | 0.0601 | 0.8972 | 0.9583 | 0.9669 | 0.0560 | ~0 ms |
| M3 RF | 0.8764 | 0.9018 | 0.8545 | 0.1000 | 0.8775 | 0.9440 | 0.9551 | 0.0116 | 0.634 ms |
| M4 GB | 0.8662 | 0.9051 | 0.8286 | 0.0934 | 0.8652 | 0.9394 | 0.9496 | 0.0210 | ~0 ms |
| M5 XGBoost | 0.8801 | 0.9148 | 0.8474 | 0.0848 | 0.8798 | 0.9484 | 0.9576 | 0.0067 | 0.075 ms |
| M6 Hybrid | 0.8080 | 0.8871 | 0.7212 | 0.0987 | 0.7956 | 0.8896 | 0.9070 | 0.0325 | 0.334 ms |
| M1_HARDNEG | 0.8998 | 0.9596 | 0.8422 | 0.0381 | 0.8970 | 0.9610 | 0.9695 | 0.0370 | ~0 ms |
| Soft voting (M1+M2+M5) | 0.9155 | 0.9664 | 0.8698 | 0.0353 | 0.9143 | 0.9741 | 0.9798 | 0.0808 | ~1 ms |
| Weighted voting | 0.9154 | 0.9663 | 0.8696 | 0.0354 | 0.9142 | 0.9740 | 0.9797 | 0.0807 | ~1 ms |

## Key findings

1. **Soft voting ensemble** achieves the best overall performance: Recall 0.8698 (≥ 0.85 ✅), FPR 0.0353 (still > 0.01), ROC-AUC 0.9741.
2. **M1_HARDNEG** remains the best single model: lowest FPR (0.0381), best AUC among singles (0.9610).
3. The ensemble improves recall (+0.0276) and reduces FPR slightly (-0.0028) vs M1_HARDNEG, but ECE degrades (0.0808 vs 0.0370).
4. **No configuration meets FPR ≤ 0.01.** Best FPR remains 0.0353 (3.5× target).

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Phase 14 (Comparaison finale).*