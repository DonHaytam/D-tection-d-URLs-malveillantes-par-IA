# MODEL CARD — Phishing AI Master 2

## Modèle déployé

- **ID** : M1_LR_HARDNEG
- **Algorithme** : Régression logistique (scikit-learn)
- **Représentation** : TF-IDF sur n-grammes de caractères (3-5), avec hard-negative mining
- **Version** : M1_LR_HARDNEG (expérimental)
- **Artefact** : `models/versions/M1_LR_HARDNEG.joblib`

## Métriques (jeu DEV, seuil 0.5)

| Métrique | Valeur |
|---|---|
| Accuracy | 0.8998 |
| Precision | 0.9596 |
| Recall | 0.8422 |
| FPR | 0.0381 |
| F1 | 0.8970 |
| ROC-AUC | 0.9610 |
| PR-AUC | 0.9695 |
| Brier | 0.0770 |
| ECE | 0.0370 |

## Seuils de décision (gelés)

- `low` = 0.25 → LEGITIMATE
- `high` = 0.75 → PHISHING
- Entre les deux → NEEDS_REVIEW

## Statut de production

**BLOCKED** — ne satisfait pas simultanément Recall ≥ 0.85 et FPR ≤ 0.01.
Le rappel au seuil 0.5 est 0.8422 (< 0.85) et le FPR est 0.0381 (> 0.01).
Le point de fonctionnement à FPR ≤ 1% donne un rappel de 0.7440.

## Candidats documentés (non déployés)

| candidat | DEV recall @0.5 | DEV FPR @0.5 | DEV recall @FPR≤1% | EXTERNAL_TEST recall @0.5 | EXTERNAL_TEST FPR @0.5 |
|---|---:|---:|---:|---:|---:|
| M1_HYBRID_REP_V2 | 0.9348 | 0.0560 | 0.7657 | 0.9857 | 0.0711 |
| PLATFORM_MASK | 0.9550 | 0.0607 | 0.7651 | non évalué | non évalué |

`M1_HYBRID_REP_V2` améliore fortement le rappel et généralise sur
EXTERNAL_TEST (domaines disjoints), mais son FPR reste au-dessus de la cible.
Les variantes « plateforme » améliorent la zone de triage (3 classes) sans
franchir la porte stricte. Aucun candidat n'est câblé dans l'API ou le
frontend.

## Limites

- Données d'entraînement historiques (PhishTank 2015) → risque de concept drift.
- 607 141 URLs sans schéma dans le dataset source.
- 591 domaines registrables apparaissent avec les deux labels (phishing + légitime).
- 839 URLs phishing de DEV (7,2 %) sont hébergées sur des plateformes
  partagées (hébergeurs gratuits, raccourcisseurs, Google Forms/Docs, buckets
  cloud) dont la réputation de domaine ne décrit pas la page.
- Les données externes contiennent très peu d'URLs d'authentification
  légitimes (87 URLs strictes dans le pool) et presque aucune plateforme
  légitime de type documentaire ou raccourcisseur.
- L'audit EXP027 est invalidé (labels inversés) et ne doit pas être cité.

---

*Documentation générée par le pipeline du projet `phishing_ai_master`.*
