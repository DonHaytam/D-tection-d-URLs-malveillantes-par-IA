# ENSEMBLE EVALUATION REPORT — Phishing AI Master 2 (Phase 8)

## 1. Configurations testées

| Ensemble | Accuracy | Recall | FPR | F1 | ROC-AUC | ECE |
|---|---:|---:|---:|---:|---:|---:|
| Soft voting (M1+M2+M5) | 0.9155 | 0.8698 | 0.0353 | 0.9143 | 0.9741 | 0.0808 |
| Weighted voting | 0.9154 | 0.8696 | 0.0354 | 0.9142 | 0.9740 | 0.0807 |

## 2. Référence

| Modèle seul | Accuracy | Recall | FPR | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| M1_HARDNEG | 0.8998 | 0.8422 | 0.0381 | 0.8970 | 0.9610 |

## 3. Conclusion

L'ensemble par vote pondéré améliore le FPR par rapport à M1 seul.
Le vote pondéré réduit le recall.

L'ensemble n'apporte pas d'amélioration significative par rapport au meilleur modèle seul (M1_HARDNEG).

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Phase 8 (Ensemble).*