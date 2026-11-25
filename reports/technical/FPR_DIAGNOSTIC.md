# FPR DIAGNOSTIC — Phishing AI Master 2 (Phase A)

## 1. Confusion matrix (M1 Logistic Regression, seuil 0.5, jeu DEV)

| | Prédit 0 (légitime) | Prédit 1 (phishing) |
|---|---:|---:|
| Réel 0 (légitime) | TN = 10 288 | FP = 597 |
| Réel 1 (phishing) | FN = 1 781 | TP = 9 920 |

- FPR = 597 / (597 + 10 288) = **0.0548**
- FNR = 1 781 / (1 781 + 9 920) = **0.1522**
- Precision = 0.9432
- Recall = 0.8478
- ROC-AUC = 0.9593
- PR-AUC = 0.9676

## 2. FPR par TLD (légitimes uniquement, top 15 par volume)

| TLD | n | FP | FPR |
|---|---:|---:|---:|
| com | 6 943 | 281 | 0.0405 |
| org | 650 | 18 | 0.0277 |
| net | 613 | 29 | 0.0473 |
| edu | 235 | 0 | 0.0000 |
| uk | 188 | 11 | 0.0585 |
| ru | 140 | 9 | 0.0643 |
| in | 138 | 7 | 0.0507 |
| ca | 132 | 0 | 0.0000 |
| io | 112 | 1 | 0.0089 |
| gov | 108 | 0 | 0.0000 |
| de | 99 | 7 | 0.0707 |
| jp | 99 | 11 | 0.1111 |
| cn | 51 | 28 | 0.5490 |
| ar | 48 | 20 | 0.4167 |
| it | 45 | 5 | 0.1111 |

**Observation** : les TLD `.cn` et `.ar` présentent des FPR très élevés (0.549 et 0.417), liés à la sous-représentation dans l'entraînement et à la distribution des données. `.edu`, `.gov`, `.ca`, `.io` ont FPR ≈ 0 (bien représentés / moins ambigus).

## 3. FPR par longueur d'URL

| Bucket | n | FP | FPR |
|---|---:|---:|---:|
| 0-20 | 2 834 | 122 | 0.0430 |
| 21-40 | 3 903 | 317 | 0.0812 |
| 41-60 | 2 311 | 119 | 0.0515 |
| 61-80 | 998 | 26 | 0.0261 |
| 81-120 | 700 | 11 | 0.0157 |
| 121-200 | 127 | 1 | 0.0079 |
| 200+ | 12 | 1 | 0.0833 |

**Observation** : les URLs courtes (21-40 caractères) concentrent le plus de faux positifs (FPR 0.081). Les URLs longues (> 80) ont un FPR bas. Le modèle semble sur-réagir aux URLs courtes contenant des tokens suspects.

## 4. FPR par source

| Source | n | FP | FPR |
|---|---:|---:|---:|
| huggingface_ealvaradob | 6 240 | 313 | 0.0502 |
| tranco_top1m | 4 645 | 284 | 0.0611 |

Les deux sources ont des FPR comparables (~0.05-0.06).

## 5. Principaux faux positifs (scores les plus élevés)

Les URLs légitimes les plus fortement classées comme phishing contiennent des tokens de marque ou des mots-clés suspects :
- `http://dapeco.com.om` (0.998)
- `http://thd.org.tr` (0.996)
- `https://paypal.me` (0.988) — marque PayPal
- `https://www.sunpass.com/...` (0.963) — service de péage
- `https://www.amazon.cn/` (0.951) — marque Amazon
- `http://www.bankofbeirut.com/...` (0.963) — mot "bank"
- `https://www.sunpass.com/vector/account/home/accountLogin.do` (0.963) — "account", "login"

**Cause identifiée** : le modèle associe fortement les tokens de marque/mots-clés suspects (login, bank, account, amazon, paypal) à la classe phishing, sans tenir compte du contexte du domaine officiel. C'est un **raccourci lexical** (shortcut learning).

## 6. Principaux faux négatifs (scores les plus bas)

Les phishing les moins bien détectés sont des URLs courtes, génériques, sans tokens suspects :
- `https://1skyvideo.com/article/live.html` (0.010)
- `https://filmbd.net` (0.030)
- `https://tv-journal.ru` (0.026)
- `https://docs.google.com/a/...` (0.039) — domaine légitime détourné

**Cause identifiée** : le modèle dépend fortement des tokens suspects. Les phishing sans ces tokens (URLs courtes, domaines génériques) passent sous le radar.

## 7. Diagnostic des causes

| Cause | Constat |
|---|---|
| Raccourci lexical (brand/token memorization) | Confirmé — les faux positifs contiennent des tokens de marque |
| Faiblesse des features structurelles | Confirmé — les URLs courtes sont mal classées |
| Biais de dataset (longueur) | Confirmé — phishing = paths longs, légitimes = racines courtes |
| Distribution shift (TLD) | Confirmé — cn, ar sous-représentés |
| Overfitting | Non confirmé — gap train/dev modéré |
| Mauvaise calibration | Partiel — ECE 0.0304 (acceptable) |
| Bruit de labels | À investiguer Phase C |

## 8. Recommandations pour les phases suivantes

1. **Phase B** : optimisation des seuils pour trouver un point d'opération avec Recall ≥ 0.85 et FPR minimale.
2. **Phase C** : analyse approfondie des faux positifs par feature.
3. **Phase D** : amélioration des features (domaine, structure) pour réduire la dépendance aux tokens.
4. **Phase E** : optimisation des hyperparamètres avec régularisation conservative.
5. **Phase F** : hard-negative mining sur les légitimes mal classés.
6. **Phase G** : tests de robustesse (perturbations).
7. **Phase H** : calibration (Platt / isotonic).

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Phase A (Diagnostic FPR).*
