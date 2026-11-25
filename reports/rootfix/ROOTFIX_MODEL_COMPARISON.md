# ROOTFIX MODEL COMPARISON — Phishing AI Master 2

## Comparison table

| Model | Recall | FPR | ROC-AUC | ECE | F1 | Auth FP (paypal.com/signin) |
|---|---:|---:|---:|---:|---:|---:|
| FINAL_LR_C1.0 (original) | 0.8422 | 0.0381 | 0.9610 | 0.0370 | 0.8970 | 96.18% |
| ROOTFIX_HN (5k Tranco HN) | 0.8457 | 0.0584 | 0.9581 | 0.0302 | 0.8902 | 78.85% |
| ROOTFIX (5k+2.5k HN/HP, 5k features) | 0.8251 | 0.0783 | 0.9440 | 0.0148 | 0.8695 | 82.63% |
| Ensemble (soft voting) | 0.8698 | 0.0353 | 0.9741 | 0.0808 | 0.9143 | — |

## Conclusion

Le meilleur modèle reste M1_LR_HARDNEG (FPR 0.0381, AUC 0.9610). Les tentatives d'ajout de hard negatives construits (Tranco) ont amélioré les scores sur les URL diagnostiques mais dégradé les métriques globales.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Comparaison rootfix.*