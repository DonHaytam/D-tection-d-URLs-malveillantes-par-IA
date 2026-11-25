# THRESHOLD EVALUATION REPORT — Phishing AI Master 2

## 1. Methodology

- Model: M1_LR_HARDNEG (Logistic Regression, char TF-IDF 3-5, hard-negative mining).
- Dataset: DEV (22 586 URL, 10 885 légitimes / 11 701 phishing).
- Métrique binaire : PHISHING = score ≥ high_threshold.
- Huit configurations de seuils évaluées.

## 2. Résultats

| low | high | Recall | Precision | F1 | FPR | Specificity | LEGITIMATE | NEEDS_REVIEW | PHISHING | Review rate |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.05 | 0.85 | 0.6721 | 0.9951 | 0.8023 | 0.0036 | 0.9964 | 2816 | 11867 | 7903 | 0.5254 |
| 0.25 | 0.75 | 0.7383 | 0.9891 | 0.8455 | 0.0087 | 0.9913 | 9237 | 4615 | 8734 | 0.2043 |
| 0.10 | 0.90 | 0.6203 | 0.9968 | 0.7647 | 0.0021 | 0.9979 | 4938 | 10367 | 7281 | 0.4590 |
| 0.15 | 0.85 | 0.6721 | 0.9951 | 0.8023 | 0.0036 | 0.9964 | 6667 | 8016 | 7903 | 0.3549 |
| 0.20 | 0.80 | 0.7092 | 0.9923 | 0.8272 | 0.0059 | 0.9941 | 8078 | 6146 | 8362 | 0.2721 |
| 0.30 | 0.70 | 0.7623 | 0.9849 | 0.8594 | 0.0126 | 0.9874 | 10105 | 3424 | 9057 | 0.1516 |
| 0.10 | 0.80 | 0.7092 | 0.9923 | 0.8272 | 0.0059 | 0.9941 | 4938 | 9286 | 8362 | 0.4111 |
| 0.20 | 0.75 | 0.7383 | 0.9891 | 0.8455 | 0.0087 | 0.9913 | 8078 | 5774 | 8734 | 0.2556 |

## 3. Analyse

### Configuration actuelle (0.05 / 0.85)
- Recall = 0.6721, FPR = 0.0036, F1 = 0.8023.
- 52.5% des URL nécessitent une revue manuelle (NEEDS_REVIEW).
- FPR excellent (0.0036 ≤ 0.01) mais recall insuffisant (0.6721 < 0.85).

### Configuration proposée (0.25 / 0.75)
- Recall = 0.7383, FPR = 0.0087, F1 = 0.8455.
- 20.4% des URL nécessitent une revue manuelle.
- FPR acceptable (0.0087 ≤ 0.01) mais recall insuffisant (0.7383 < 0.85).

### Meilleur F1 : (0.30 / 0.70)
- Recall = 0.7623, FPR = 0.0126, F1 = 0.8594.
- FPR légèrement au-dessus de 0.01 (0.0126).

## 4. Vérification des critères d'acceptation

| Configuration | Recall ≥ 0.85 ? | FPR ≤ 0.01 ? | Verdict |
|---|---|---|---|
| (0.05, 0.85) | ❌ (0.6721) | ✅ (0.0036) | Rejeté |
| (0.25, 0.75) | ❌ (0.7383) | ✅ (0.0087) | Rejeté |
| (0.30, 0.70) | ❌ (0.7623) | ❌ (0.0126) | Rejeté |

**Aucune configuration ne satisfait simultanément Recall ≥ 0.85 et FPR ≤ 0.01.**

## 5. Recommandation

**Conserver la configuration actuelle (0.05 / 0.85).**

Raisons :
1. La configuration proposée (0.25/0.75) améliore le recall (0.6721 → 0.7383) et le F1 (0.8023 → 0.8455), mais ne satisfait pas le critère Recall ≥ 0.85.
2. La configuration actuelle a le FPR le plus bas (0.0036) et la meilleure spécificité (0.9964).
3. Aucune configuration testée ne satisfait les deux critères simultanément.
4. Changer les seuils n'améliorerait pas substantiellement les métriques car le problème est fondamental (raccourci lexical du modèle).

Si l'utilisateur souhaite réduire le taux de revue manuelle (52.5% → 20.4%), la configuration (0.25/0.75) est un meilleur compromis, mais au prix d'une augmentation du FPR (0.0036 → 0.0087) et d'une baisse de la spécificité.

## 6. Impact sur les faux positifs et faux négatifs

- Passer de (0.05/0.85) à (0.25/0.75) réduit les faux négatifs (3837 → 3062, -20%) mais augmente les faux positifs (39 → 95, +144%).
- Le taux de revue manuelle passe de 52.5% à 20.4%.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Évaluation des seuils.*