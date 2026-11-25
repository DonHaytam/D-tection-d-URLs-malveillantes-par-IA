# ERROR ANALYSIS ADVANCED — Phishing AI Master 2 (Phase 2)

## 1. Résumé

- Modèle évalué : M1_LR_HARDNEG (seuil 0.5).
- Jeu DEV : 22 586 URL.
- Faux positifs (FP) : 415 (FPR = 0.0381).
- Faux négatifs (FN) : 1 847 (FNR = 0.1578).
- Corrects : 20 324.

## 2. FPR par TLD

| TLD | n (légitimes) | FP | FPR |
|---|---:|---:|---:|
| com | 6 943 | 198 | 0.0285 |
| org | 650 | 10 | 0.0154 |
| net | 613 | 19 | 0.0310 |
| edu | 235 | 0 | 0.0000 |
| uk | 188 | 12 | 0.0638 |
| ru | 140 | 7 | 0.0500 |
| in | 138 | 5 | 0.0362 |
| ca | 132 | 0 | 0.0000 |
| io | 112 | 0 | 0.0000 |
| gov | 108 | 0 | 0.0000 |

Les TLD .uk, .ru présentent les FPR les plus élevés. Les TLD .edu, .ca, .io, .gov ont FPR = 0 (bien représentés, moins ambigus).

## 3. Erreurs par source

| Source | n | FP | FN | FPR |
|---|---:|---:|---:|---:|
| huggingface_ealvaradob | 13 588 | 226 | 1 827 | 0.0362 |
| tranco_top1m | 4 645 | 189 | 0 | 0.0407 |
| phishtank_zenodo_8371046 | 4 353 | 0 | 20 | — |

- Tranco : 189 FP (4.07%) — domaines légitimes mal classés (tokens suspects).
- HuggingFace : 226 FP (3.62%) + 1 827 FN (15.6%) — déséquilibre dans les deux sens.
- PhishTank : 0 FP, 20 FN — phishing très bien détectés (tokens suspects présents).

## 4. FNR par longueur d'URL

| Bucket | n | FN | FNR |
|---|---:|---:|---:|
| 0-30 | 3 728 | 1 170 | 0.3138 |
| 31-50 | 5 753 | 453 | 0.0787 |
| 51-80 | 1 218 | 133 | 0.1092 |
| 81-120 | 543 | 69 | 0.1271 |
| 121-200 | 296 | 20 | 0.0676 |
| 200+ | 163 | 2 | 0.0123 |

**Conclusion** : les URL phishing courtes (0-30 caractères) ont un FNR de 31.4%. Le modèle dépend fortement des tokens suspects qui sont absents des URL courtes.

## 5. Raccourci lexical confirmé

Le modèle associe les tokens suspects (login, bank, amazon, paypal) à la classe phishing. Les faux positifs sont des URLs légitimes contenant ces tokens sur des domaines non reconnus.

## 6. Limites fondamentales

1. **Pas de données de réputation de domaine** : le modèle ne peut pas distinguer les domaines officiels des imitations.
2. **Données historiques** : PhishTank 2015 → concept drift.
3. **Déséquilibre** : les URL phishing courtes sont sous-représentées.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Phase 2 (Analyse avancée des erreurs).*