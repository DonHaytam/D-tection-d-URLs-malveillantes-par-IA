# HARD NEGATIVE MINING REPORT — Phishing AI Master 2

## 1. Procédure

- Source : faux positifs de M1 sur DEV (légitimes classés phishing, score ≥ 0.5).
- Nombre : 597 hard negatives.
- Ajoutés au TRAIN → 115 470 URL (+597).
- Ré-entraînement : char TF-IDF (3-5) + Logistic Regression (C=1.0, balanced).

## 2. Résultats

| Métrique | M1 (original) | M1_HARDNEG |
|---|---:|---:|
| Accuracy | 0.8947 | 0.8998 |
| Recall | 0.8478 | 0.8422 |
| FPR | 0.0548 | 0.0381 |
| Precision | 0.9432 | 0.9596 |
| F1 | 0.8930 | 0.8970 |
| ROC-AUC | 0.9593 | 0.9610 |
| ECE | 0.0304 | 0.0370 |

## 3. Impact

- FPR réduit de 0.0548 à 0.0381 (-30%).
- Recall légèrement réduit (0.8478 → 0.8422).
- ROC-AUC amélioré (0.9593 → 0.9610).
- ECE légèrement dégradé (0.0304 → 0.0370).

## 4. Hard-negative groups

- HN_AUTH : URLs d'authentification légitimes.
- HN_ACCOUNT : URLs de gestion de compte.
- HN_PAYMENT : URLs de paiement.
- HN_SECURITY : URLs de sécurité.
- HN_VERIFY : URLs de vérification.
- HN_LOGIN : URLs de connexion.
- HN_BRAND : URLs de marques (paypal, amazon, etc.).
- HN_LONG_LEGITIMATE : URLs légitimes longues.
- HN_COMPLEX_QUERY : URLs avec query complexes.

## 5. Conclusion

Le hard-negative mining réduit significativement le FPR (-30%) au prix d'une légère baisse du recall. C'est la technique la plus efficace testée.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Hard-negative mining.*