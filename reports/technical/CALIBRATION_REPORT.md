# CALIBRATION REPORT — Phishing AI Master 2

## 1. Résultats

| Méthode | Brier | ECE | ROC-AUC |
|---|---:|---:|---:|
| Raw (M1) | 0.0784 | 0.0304 | 0.9593 |
| Platt (sigmoid) | 0.0774 | 0.0158 | 0.9593 |
| Isotonic | 0.0761 | 0.0000 | 0.9598 |

## 2. Analyse

- Isotonic donne la meilleure calibration (ECE 0.0000, Brier 0.0761).
- Platt améliore légèrement (ECE 0.0158).
- La calibration ne change pas le ranking (AUC inchangé).
- La calibration améliore la fiabilité des probabilités mais pas la discrimination.

## 3. Conclusion

Isotonic est la meilleure méthode de calibration. Elle devrait être utilisée en production pour des scores de risque fiables.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Calibration.*