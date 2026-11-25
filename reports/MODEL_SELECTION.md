# MODEL SELECTION — Phishing URL detection (Phase 11)

## Résultats sur DEV (jeu de validation)

| Model | Accuracy | Precision | Recall | FPR | F1 | ROC-AUC | PR-AUC | Brier | ECE |
|---|---|---|---|---|---|---|---|---|---|
| Logistic Regression (M1) | 0.8947 | 0.9432 | 0.8478 | 0.0548 | 0.8930 | 0.9593 | 0.9676 | 0.0784 | 0.0304 |
| Linear SVM (M2) | 0.8980 | 0.9389 | 0.8590 | 0.0601 | 0.8972 | 0.9583 | 0.9669 | 0.0818 | 0.0560 |
| Random Forest (M3) | 0.8764 | 0.9018 | 0.8545 | 0.1000 | 0.8775 | 0.9440 | 0.9551 | 0.0902 | 0.0116 |
| Gradient Boosting (M4) | 0.8662 | 0.9051 | 0.8286 | 0.0934 | 0.8652 | 0.9394 | 0.9496 | 0.0964 | 0.0210 |
| XGBoost (M5) | 0.8801 | 0.9148 | 0.8474 | 0.0848 | 0.8798 | 0.9484 | 0.9576 | 0.0870 | 0.0067 |
| Hybrid (M6) | 0.8080 | 0.8871 | 0.7212 | 0.0987 | 0.7956 | 0.8896 | 0.9070 | 0.1331 | 0.0325 |

## Réponses aux questions de sélection

1. **Meilleure performance globale** : Linear SVM (M2) — accuracy 0.8980, recall 0.8590.
2. **Meilleur recall** : Linear SVM (M2) — 0.8590 (seul ≥ 0.85 avec M3 à 0.8545).
3. **Plus bas FPR** : Logistic Regression (M1) — 0.0548 (meilleur, mais encore 5.5× au-dessus de la cible 0.01).
4. **Meilleure généralisation** : à vérifier Phase 10 (non mesuré à ce stade).
5. **Meilleure calibration** : XGBoost (M5) — ECE 0.0067, puis Random Forest (M3) — ECE 0.0116.
6. **Plus efficace computationnellement** : Logistic Regression (M1) — entraînement 3.9 s, latence ~0 ms/URL.
7. **Modèle final sélectionné (expérimental)** : **Logistic Regression (M1)** — choisi pour le plus bas FPR, le meilleur ROC-AUC (0.9593) et PR-AUC (0.9676), la simplicité et l'interprétabilité.
8. **Modèles rejetés** :
   - M2 (SVM) : FPR plus élevé (0.0601), calibration moins bonne (ECE 0.0560).
   - M3 (RF) : FPR élevé (0.1000), latence supérieure (0.634 ms).
   - M4 (GB) : recall sous la cible (0.8286), FPR élevé.
   - M5 (XGBoost) : recall sous la cible (0.8474), FPR élevé.
   - M6 (Hybrid) : performances nettement inférieures sur tous les critères (acc 0.8080, recall 0.7212).
9. **Limitations restantes** : aucun modèle n'atteint FPR ≤ 0.01 ; le FPR le plus bas est 0.0548 (5.5× la cible). Recall M1 = 0.8478 < 0.85 (manque 0.0022).

## ⚠️ Statut production

**Aucun modèle ne satisfait la porte de production** (Recall ≥ 0.85 ET FPR ≤ 0.01 simultanément).

- M2 et M3 satisfont Recall ≥ 0.85 mais pas FPR ≤ 0.01.
- M1 a le FPR le plus bas mais Recall = 0.8478 < 0.85.

**STATUS = BLOCKED** (voir `reports/PRODUCTION_READINESS_GATE.md`).

Le meilleur candidat expérimental sélectionné est M1 (Logistic Regression), mais il ne satisfait pas la porte de production. Ceci est reporté honnêtement, conformément aux règles absolues du projet.

## Résultats des expériences d'optimisation (Phases B-F)

| Expérience | Modèle | Recall | FPR | ROC-AUC | ECE | Note |
|---|---|---:|---:|---:|---:|---|
| EXP001-006 | M1-M6 (originaux) | 0.72-0.86 | 0.055-0.100 | 0.890-0.959 | 0.007-0.056 | Voir MODEL_COMPARISON.md |
| EXP007-010 | M7_LR_ENHANCED (numeric) | 0.723-0.728 | 0.087-0.091 | 0.895 | 0.018 | Inférieur à M1 |
| EXP011 | M1_LR_HARDNEG | 0.8422 | 0.0381 | 0.9610 | 0.0370 | **Meilleur FPR** |
| Calibration | M1 isotonic | — | — | 0.9598 | 0.0000 | Brier 0.0761 |
| Allow-list | M1 + Tranco top 10k | 0.8209 | 0.0298 | — | — | Recall trop bas |
| Allow-list | M1 + Tranco top 50k | 0.7922 | 0.0164 | — | — | Recall trop bas |

## Conclusion

Le meilleur FPR atteint est **0.0381** (M1_LR_HARDNEG), soit 3.8× la cible de 0.01. Aucune configuration ne satisfait simultanément Recall ≥ 0.85 et FPR ≤ 0.01.

**STATUS = BLOCKED** (voir `reports/PRODUCTION_READINESS_GATE.md`).

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Phase 11 (Sélection du modèle).*

