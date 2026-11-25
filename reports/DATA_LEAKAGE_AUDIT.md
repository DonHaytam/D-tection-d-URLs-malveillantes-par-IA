# DATA LEAKAGE AUDIT — Phishing URL detection project (framework — à remplir en Phase 4)

> *Méthodologie d'audit de fuites de données et procédures de sécurité. Ce document doit contenir des vérifications effectuées et résultats de tests — pas des promesses.*

## METHODOLOGIE D'AUDIT (à suivre — Phase 4)

1. **Horizon chronologique :** Documenter les dates de collecte des données sources vs dates d'acquisition/entraînement. Confirmer absence de données futures utilisées en passé.
2. **Hashes des datasets :** Compute via `scripts/verify_data_hashes.py` — hashes de TRAIN, DEV, LOCKED_TEST, INDEPENDENT_FINAL_TEST (sha256) — enregistrés ici et dans `data/splits/hashes/v1.json`.
3. **Vérification LOCKED_TEST :** Script vérifiant que LOCKED_TEST n'apparaît ni dans TRAIN ni DEV, que LOCKED_TEST n'a pas été utilisé en features/tuning. Exécution en Phase 13.
4. **Vérification INDEPENDENT_FINAL_TEST :** Script vérifiant que le jeu final est préexistant et ajouté après freeze du projet (Phase 13).
5. **Vérification de proximité (Near-duplicate audit):** Entre l'ensemble de développement et l'ensemble de test — flag des quasi-doublons à corriger ou documenter (Phase 4).
6. **Check de domaines :** Domains de DEV vs LOCKED_TEST/INDEPENDENT — le début de la liste à vérifier en Phase 5.

## RÉSULTATS D'AUDIT (Phase 4-5 — vérifiés)

### Vérification 1 — Jeux disjoints par domaine
- `check_status: vérifié`
- Split par `registrable_domain` : TRAIN 114 873 / DEV 22 586 / LOCKED_TEST 22 109.
- Domaines registrables uniques : 96 155.
- Aucun domaine ne traverse deux ensembles (garanti par `domain_disjoint_split`).
- Domaines apparaissant avec les deux labels (phishing + légitime) : 591 (à surveiller — possible leakage par domaine).

### Vérification 2 — Pas d'utilisation de LOCKED_TEST avant Phase 13
- `check_status: vérifié (procédure)`
- LOCKED_TEST et INDEPENDENT_FINAL_TEST non chargés dans aucun script d'entraînement/tuning. Seuls TRAIN et DEV sont utilisés dans les phases 6-11.

### Vérification 3 — INDEPENDENT_FINAL_TEST réservé
- `check_status: en attente (Phase 13)`
- Fichier `data/splits/INDEPENDENT_FINAL_TEST.csv` créé vide (en-têtes uniquement). À acquérir après le freeze du modèle.

### Vérification 4 — Hashes
- `check_status: vérifié`
- Hashes SHA-256 enregistrés dans `data/splits/hashes/v1.json` :
  - TRAIN : `2b2cfeaeba788df2f27b789a76a442d83978d2e593c03785e2894ffb69d5ca99`
  - DEV : `d18ffdc7cbb4179a7fbd77e4fee78dfc9c5e57659397d35cc0e9d1740458d1bc`
  - LOCKED_TEST : `e9807d679711052da21be04a285a9a2173925ba31d86ad172c00304e75344d0a`

### Vérification 5 — Doublons / fuites observées
- URLs exactes dupliquées supprimées : 276.
- URLs normalisées dupliquées supprimées : 0.
- 591 domaines registrables apparaissent avec les deux labels (phishing et légitime) — à analyser en Phase 10 (cross-source / domain generalization).

## PROVENANCE ASSURÉE POUR L'ÉVALUATION FINALE (Phase 13)

Le jeu INDEPENDENT_FINAL_TEST doit être :
1. Collecté/acquis après Phase 12 (freeze).
2. Jamais passé par les étapes de dev (analyse EDA, cleaning, splits, tuning).
3. Haché et archivé dans `data/splits/` avant tout usage pour prédiction.

Vérification de satisfaction : `(STATUS: OK/BLOCKED — Phase 13)`.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Audit des fuites de données (Phase 4/13).*
