# HARD NEGATIVE EXPERIMENT — Phishing AI Master 2 (Phase F)

## Procédure

- Source des hard negatives : faux positifs de M1 sur DEV (légitimes classés phishing, score ≥ 0.5).
- Nombre de hard negatives ajoutés : 597
- TRAIN augmenté : 114873 → 115470 (+597)
- Ré-entraînement : char TF-IDF (3-5) + Logistic Regression (C=1.0, balanced).

## Résultats (jeu DEV)

| Métrique | M1 (original) | M1_HARDNEG |
|---|---:|---:|
| Accuracy | 0.8947 | 0.8998 |
| Recall | 0.8478 | 0.8422 |
| FPR | 0.0548 | 0.0381 |
| Precision | 0.9432 | 0.9596 |
| F1 | 0.8930 | 0.8970 |
| ROC-AUC | 0.9593 | 0.9610 |
| ECE | 0.0304 | 0.0370 |

## Conclusion

Amélioration du FPR (0.0381 vs 0.0548). Le hard-negative mining réduit le FPR de manière notable.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Phase F (Hard-negative mining).*
