# CURRENT MODEL DEEP AUDIT — Phishing AI Master 2 (Phase 1)

## 1. Project Structure

- Root: `D:\openhands\projects\v2\phishing_ai_master\`
- 21 experiments (EXP001-EXP021) in `experiments/results/`
- 18 model artifacts in `models/versions/`
- 22 tests (7 validation + 15 decision policy), all passing
- DEV: 22 586 URL, TRAIN: 114 873 URL, LOCKED_TEST: 22 109 URL

## 2. Current Model Architecture

- **Model**: M1_LR (Logistic Regression, char TF-IDF 3-5)
- **Representation**: TfidfVectorizer(analyzer="char", ngram_range=(3,5), min_df=3, max_features=20000)
- **Classifier**: LogisticRegression(C=1.0, class_weight="balanced", solver="saga", max_iter=2000)
- **Hard-negative mining**: 597 legitimate FPs from DEV added to TRAIN → M1_LR_HARDNEG
- **Final selected**: FINAL_LR_C1.0 (identical to M1_LR_HARDNEG)

## 3. Preprocessing Pipeline

1. URL validation (syntactic, no network access).
2. Normalization (add https:// if no scheme, lowercase host, remove default ports).
3. Manifest creation (domain, registrable_domain, tld, scheme, path, query, fragment).
4. Exact + normalized deduplication.
5. Domain-disjoint split (TRAIN/DEV/LOCKED_TEST).

## 4. Dataset Provenance

| Source | Type | Size | License |
|---|---|---|---|
| HuggingFace (ealvaradob) | Mixte | 835 697 URL | À vérifier |
| Tranco (tranco-list.eu) | Légitime | 1 000 000 domaines | CC BY 3.0/4.0 |
| PhishTank (Zenodo) | Phishing | 149 188 valides | PhishTank ToU |

Nettoyé : 159 568 URL (79 842 légitimes / 79 726 phishing). 96 155 domaines registrables. 591 domaines cross-label supprimés de l'entraînement.

## 5. Feature Extraction

- **Lexicales** : 18 features (longueur, caractères, tokens suspects, entropie, ratios).
- **Structurelles** : 18 features (schéma, port, IP, sous-domaines, query, fragment, etc.).
- **Char TF-IDF** : 20 000 features (n-grammes 3-5).
- **Enhanced** : brand position (5 features) + Tranco rank (1 feature).

## 6. Model Coefficients (top features)

Le modèle char TF-IDF capture des patterns de sous-chaînes. Les coefficients les plus élevés correspondent à des tokens suspects (login, bank, paypal, etc.) présents dans les phishing.

## 7. Error Analysis Summary

- **Faux positifs** : 597 sur DEV (M1, seuil 0.5). Concentrés sur TLD sous-représentés (.cn, .ar) et URLs courtes avec tokens suspects.
- **Faux négatifs** : 1 781 sur DEV. Phishing sans tokens suspects, URLs courtes génériques.
- **Raccourci lexical confirmé** : le modèle associe les tokens de marque à la classe phishing sans vérifier le contexte du domaine.

## 8. Domain Leakage Audit

- Split par domaine registrable : aucun domaine ne traverse deux ensembles.
- 591 domaines cross-label identifiés et supprimés de l'entraînement.
- Hashes SHA-256 des splits enregistrés.

## 9. Evaluation Isolation

- TRAIN : entraînement et sélection de features.
- DEV : tuning, calibration, seuils.
- LOCKED_TEST : jamais utilisé (réservé).
- INDEPENDENT_FINAL_TEST : réservé.

## 10. Conclusion de l'audit

Le système est bien structuré et reproductible. Le principal problème est le raccourci lexical : le modèle ne distingue pas les domaines officiels des imitations. L'amélioration des features (brand position, Tranco rank) n'a pas réduit le FPR car le signal char TF-IDF domine. Les cibles (Recall ≥ 0.85, FPR ≤ 0.01) ne sont pas atteintes.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Phase 1 (Audit complet).*