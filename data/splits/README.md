# Splits — Phishing URL detection project (Phase 5)

## Files

- `TRAIN.csv` — 114 873 lignes (58 221 légitimes / 56 652 phishing) — entraînement.
- `DEV.csv` — 22 586 lignes (10 885 légitimes / 11 701 phishing) — validation, tuning, calibration, seuils.
- `LOCKED_TEST.csv` — 22 109 lignes (10 736 légitimes / 11 373 phishing) — **jamais utilisé pendant le développement**.
- `INDEPENDENT_FINAL_TEST.csv` — **réservé** (vide, à acquérir après le freeze du modèle — Phase 13).
- `hashes/v1.json` — hashes SHA-256 des splits.

## Procédure de split

Split **par domaine registrable** (domain-disjoint) : toutes les URLs d'un même `registrable_domain` restent dans le même ensemble. Aucun domaine ne traverse deux ensembles.

- Ratio : 70 % TRAIN / 15 % DEV / 15 % LOCKED_TEST.
- Graine aléatoire : 42 (stable, reproductible).
- Implémentation : `src/data/splitting.py::domain_disjoint_split`.

## Règles d'isolation (ABSOLUES)

- `LOCKED_TEST` et `INDEPENDENT_FINAL_TEST` ne sont **jamais** utilisés pour : entraînement, tuning, sélection de features, sélection de seuils, calibration, sélection de modèle, hard-negative mining, modifications pilotées par l'erreur, construction de datasets.
- `INDEPENDENT_FINAL_TEST` est acquis **après** le freeze du modèle (Phase 12).
- Hashes vérifiés avant toute évaluation finale (Phase 13).

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Phase 5 (Création des splits).*
