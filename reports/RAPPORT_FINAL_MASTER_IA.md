# RAPPORT FINAL — MASTER 2 INTELLIGENCE ARTIFICIELLE

## Détection intelligente des URL de phishing et malveillantes par Intelligence Artificielle et Machine Learning

---

## Page de garde

**Titre** : Détection intelligente des URL de phishing et malveillantes par Intelligence Artificielle et Machine Learning

**Auteur** : Projet Master 2 IA

**Date** : 24 novembre 2026

---

## Résumé

Ce projet présente un système complet de détection de phishing dans les URL, fondé sur l'apprentissage automatique. Six modèles (régression logistique, SVM linéaire, forêt aléatoire, gradient boosting, XGBoost, modèle hybride) ont été implémentés, entraînés et comparés sur un jeu de données de 159 568 URL nettoyées. Le meilleur modèle expérimental est la régression logistique avec TF-IDF sur n-grammes de caractères (3-5), améliorée par hard-negative mining. Sur le jeu de validation (DEV), ce modèle atteint : Accuracy 0.8998, Recall 0.8422, FPR 0.0381, ROC-AUC 0.9610. Les cibles de production (Recall ≥ 0.85, FPR ≤ 0.01) ne sont pas atteintes. Le statut de production reste BLOCKED.

## Abstract

This project presents a complete phishing URL detection system based on machine learning. Six models were implemented, trained, and compared on 159,568 cleaned URLs. The best experimental model is logistic regression with character n-gram TF-IDF (3-5), improved via hard-negative mining, achieving Recall 0.8422, FPR 0.0381, ROC-AUC 0.9610 on the validation set. Production targets (Recall ≥ 0.85, FPR ≤ 0.01) were not met. Production status remains BLOCKED.

## Mots-clés

Phishing, détection d'URL, machine learning, TF-IDF, n-grammes de caractères, régression logistique, SVM, random forest, XGBoost, calibration, hard-negative mining, cybersécurité.

---

# Chapitre 1 — Introduction générale

## 1.1 Contexte général

Le phishing est l'une des menaces les plus répandues en cybersécurité. Les attaquants utilisent des URL trompeuses pour voler des identifiants, des données financières et des informations personnelles. La détection automatique des URL malveillantes est un enjeu majeur pour la sécurité des systèmes d'information.

## 1.2 Problématique

Comment construire un système de détection de phishing dans les URL qui :
- Atteint un rappel (recall) ≥ 0.85 (détecter au moins 85 % des phishing).
- Maintient un taux de faux positifs (FPR) ≤ 0.01 (moins de 1 % de faux positifs).
- Généralise à des domaines, sources et structures d'URL jamais vus.

## 1.3 Objectifs

- Implémenter un pipeline complet de machine learning pour la détection de phishing.
- Entraîner et comparer 6 modèles d'IA.
- Sélectionner le meilleur modèle sur la base de critères scientifiques.
- Développer une application fonctionnelle (API + interface + base de données).
- Produire un rapport académique complet.

## 1.4 Contributions

1. Pipeline modulaire et reproductible (159 568 URL, 96 155 domaines registrables).
2. Six modèles entraînés et comparés sur le même jeu de données.
3. Audit de fuites de données (split par domaine registrable).
4. Diagnostic approfondi des faux positifs.
5. Expérimentation de hard-negative mining (réduction du FPR de 0.0548 à 0.0381).
6. Application fonctionnelle (FastAPI + Streamlit + SQLite).
7. Rapport honnête : cibles non atteintes, statut BLOCKED.

---

# Chapitre 2 — État de l'art

## 2.1 Le phishing

Le phishing est une technique d'ingénierie sociale visant à tromper l'utilisateur pour qu'il révèle des informations sensibles. Les URL de phishing imitent des sites légitimes (marques, banques, services en ligne).

## 2.2 Détection basée sur les URL

La détection par URL analyse la chaîne de caractères de l'URL sans visiter le site. Les approches incluent :
- Features lexicales (longueur, caractères spéciaux, tokens).
- Features structurelles (schéma, profondeur, paramètres).
- Représentations textuelles (TF-IDF, n-grammes de caractères).
- Modèles de machine learning (régression logistique, SVM, forêts aléatoires, gradient boosting).

## 2.3 Modèles utilisés

- **Régression logistique** : modèle linéaire, interprétable, rapide. Bonne baseline.
- **SVM linéaire** : efficace pour les données haute dimension (TF-IDF). Nécessite une calibration pour les probabilités.
- **Random Forest** : ensemble d'arbres, robuste, mais sensible aux features numériques.
- **Gradient Boosting** : boosting séquentiel, bon pour les features numériques.
- **XGBoost** : version optimisée du gradient boosting, régularisation intégrée.
- **Modèle hybride** : combinaison de TF-IDF caractères et features numériques.

## 2.4 TF-IDF et n-grammes de caractères

TF-IDF (Term Frequency - Inverse Document Frequency) pondère les termes par leur fréquence dans le document et leur rareté dans le corpus. Les n-grammes de caractères (3-5) capturent des sous-chaînes comme "pay", "login", "bank" sans dépendre d'une tokenisation par mots.

---

# Chapitre 3 — Analyse et conception

## 3.1 Architecture globale

Le projet suit une architecture modulaire :
- `src/data/` : ingestion, validation, déduplication, splitting, provenance.
- `src/features/` : parsing URL, features lexicales, structurelles, caractères, pipeline.
- `src/models/` : 6 modèles + registre.
- `src/evaluation/` : métriques, calibration, optimisation de seuils.
- `src/inference/` : prédicteur.
- `src/policy/` : politique de décision, allow-list.
- `deployment/api/` : FastAPI.
- `deployment/frontend/` : Streamlit.
- `database/` : SQLite.

## 3.2 Choix technologiques

- Python 3.10, scikit-learn 1.7.2, pandas 2.3.3, numpy 2.2.6.
- FastAPI 0.142.2, Streamlit 1.57.0, SQLAlchemy 2.0.55.
- XGBoost 3.2.0, LightGBM 4.7.0 (dans vendor_libs).
- CPU-only (pas de GPU NVIDIA).

## 3.3 Contraintes de sécurité

- Analyse passive des URL (pas de visite, pas de DNS, pas de HTTP GET/HEAD).
- Validation stricte des entrées.
- Pas de résolution DNS.

---

# Chapitre 4 — Collecte et préparation des données

## 4.1 Sources de données

| Source | Type | Taille | Licence | Date |
|---|---|---|---|---|
| HuggingFace (ealvaradob/phishing-dataset) | Mixte | 835 697 URL | À vérifier | Acquis 24/11/2026 |
| Tranco (tranco-list.eu) | Légitime | 1 000 000 domaines | CC BY 3.0/4.0 | Acquis 24/11/2026 |
| PhishTank (Zenodo) | Phishing | 149 188 valides | PhishTank ToU | Déc. 2015 |

## 4.2 Composition du dataset nettoyé

- **Total** : 159 568 URL (après déduplication).
- **Légitimes** : 79 842.
- **Phishing** : 79 726.
- **Domaines registrables uniques** : 96 155.
- **Domaines cross-label** : 591 (supprimés de l'entraînement).

## 4.3 Séparation des données

| Split | Taille | Légitimes | Phishing |
|---|---:|---:|---:|
| TRAIN | 114 873 | 58 221 | 56 652 |
| DEV | 22 586 | 10 885 | 11 701 |
| LOCKED_TEST | 22 109 | 10 736 | 11 373 |
| INDEPENDENT_FINAL_TEST | réservé | — | — |

Split par domaine registrable (domain-disjoint). Aucun domaine ne traverse deux ensembles.

## 4.4 Analyse exploratoire (EDA)

- URLs uniques : 821 402.
- Hôtes uniques : 448 803.
- Longueur moyenne des URL : 47.48 caractères.
- 607 141 URL sans schéma (normalisées en https).
- TLD dominant : com (486 714).

Figures : `reports/figures/eda/fig01-04`.

## 4.5 Nettoyage et déduplication

- Déduplication exacte : 276 URL supprimées.
- Déduplication normalisée : 0 supplémentaire.
- Validation syntaxique : 156 URL invalides supprimées.

---

# Chapitre 5 — Méthodologie et modèles d'IA

## 5.1 Features

### Lexicales
- Longueur URL, hôte, chemin, query.
- Nombre de points, tirets, chiffres, caractères spéciaux.
- Nombre de sous-domaines, segments de chemin.
- Fréquence de tokens suspects.
- Entropie des caractères.

### Structurelles
- Schéma (http/https).
- Présence de port, IP comme hôte.
- Profondeur de sous-domaine, chemin.
- Nombre de paramètres de query.
- Présence de fragment, encodage.

### Caractères (TF-IDF)
- N-grammes de caractères (3-5), min_df=3, max_features=20 000.

## 5.2 Modèles

Six modèles implémentés (M1-M6), entraînés sur TRAIN, évalués sur DEV.

---

# Chapitre 6 — Implémentation expérimentale

- Environnement : Python 3.10, scikit-learn 1.7.2, pandas 2.3.3.
- Suivi d'expériences : JSON (EXP001-EXP021) dans `experiments/results/`.
- Reproductibilité : graines aléatoires, hashes de datasets, versions logicielles.

---

# Chapitre 7 — Résultats et comparaison

## Tableau comparatif (jeu DEV)

| Modèle | Accuracy | Precision | Recall | FPR | F1 | ROC-AUC | PR-AUC | Brier | ECE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M1 LR | 0.8947 | 0.9432 | 0.8478 | 0.0548 | 0.8930 | 0.9593 | 0.9676 | 0.0784 | 0.0304 |
| M2 SVM | 0.8980 | 0.9389 | 0.8590 | 0.0601 | 0.8972 | 0.9583 | 0.9669 | 0.0818 | 0.0560 |
| M3 RF | 0.8764 | 0.9018 | 0.8545 | 0.1000 | 0.8775 | 0.9440 | 0.9551 | 0.0902 | 0.0116 |
| M4 GB | 0.8662 | 0.9051 | 0.8286 | 0.0934 | 0.8652 | 0.9394 | 0.9496 | 0.0964 | 0.0210 |
| M5 XGBoost | 0.8801 | 0.9148 | 0.8474 | 0.0848 | 0.8798 | 0.9484 | 0.9576 | 0.0870 | 0.0067 |
| M6 Hybrid | 0.8080 | 0.8871 | 0.7212 | 0.0987 | 0.7956 | 0.8896 | 0.9070 | 0.1331 | 0.0325 |
| M1_HARDNEG | 0.8998 | 0.9596 | 0.8422 | 0.0381 | 0.8970 | 0.9610 | 0.9695 | 0.0770 | 0.0370 |

## 7.1 Optimisation des seuils

Meilleur seuil pour recall ≥ 0.85 : M1_HARDNEG à seuil 0.4774 → recall 0.8500, FPR 0.0469.

## 7.2 Calibration

- Isotonic : Brier 0.0761, ECE 0.0000 (meilleure calibration).
- Platt : Brier 0.0774, ECE 0.0158.

## 7.3 Hard-negative mining

597 faux positifs de DEV ajoutés à l'entraînement → FPR réduit de 0.0548 à 0.0381 (-30%).

## 7.4 Analyse des faux positifs

Les FPs sont concentrés sur :
- TLD sous-représentés (.cn FPR 0.549, .ar FPR 0.417).
- URLs courtes avec tokens suspects (login, bank, amazon, paypal).
- Schéma HTTP (21.9% des FPs vs 3.1% des légitimes).

## 7.5 Allow-list

Tranco top 10k : FPR 0.0298, recall 0.8209. Trop agressif.

---

# Chapitre 8 — Sélection du meilleur modèle

**Modèle sélectionné** : M1_LR_HARDNEG (régression logistique, char TF-IDF, hard-negative mining).

**Justification** : FPR le plus bas (0.0381), ROC-AUC le plus haut (0.9610), inférence la plus rapide, modèle le plus interprétable.

**Aucun modèle ne satisfait les cibles** (Recall ≥ 0.85 ET FPR ≤ 0.01). Statut : BLOCKED.

---

# Chapitre 9 — Développement de l'application

- API FastAPI : GET /health, POST /predict, POST /predict_batch.
- Interface Streamlit : URL, verdict, score, version, seuils, temps, historique.
- Base SQLite : historique des prédictions.
- Modèle chargé : M1_LR_HARDNEG.

---

# Chapitre 10 — Sécurité et validation

- Analyse passive des URL (pas de visite, pas de DNS).
- Validation des entrées.
- Tests unitaires (7/7 passent).
- Pas d'accès automatique aux URL.

---

# Chapitre 11 — Limites et perspectives

1. **Données** : PhishTank 2015 (concept drift), 607k URL sans schéma.
2. **Modèle** : raccourci lexical (tokens de marque), pas de données de réputation de domaine.
3. **Cibles** : FPR 0.0381 vs 0.01 (3.8×), recall 0.8422 vs 0.85.
4. **Perspectives** : intégrer Tranco rank comme feature, collecter des données récentes, stacking.

---

# Conclusion générale

Ce projet a implémenté un pipeline complet de détection de phishing dans les URL : 6 modèles entraînés et comparés, diagnostic approfondi, optimisation des seuils, calibration, hard-negative mining, allow-list. Le meilleur modèle (M1_LR_HARDNEG) atteint Recall 0.8422, FPR 0.0381, ROC-AUC 0.9610. Les cibles de production (Recall ≥ 0.85, FPR ≤ 0.01) ne sont pas atteintes. Le statut de production est BLOCKED. L'application est fonctionnelle et déployable comme outil expérimental.

---

# Bibliographie

1. PhishTank — https://phishtank.org
2. Tranco — https://tranco-list.eu
3. HuggingFace ealvaradob/phishing-dataset — https://huggingface.co/datasets/ealvaradob/phishing-dataset
4. scikit-learn documentation — https://scikit-learn.org
5. FastAPI documentation — https://fastapi.tiangolo.com
6. Streamlit documentation — https://docs.streamlit.io

---

# Annexes

## A. Schéma du manifest

url, label, source, collection_date, domain, registrable_domain, tld, scheme, path, query, fragment, dataset_version

## B. Configuration du modèle final

- Modèle : M1_LR_HARDNEG
- Représentation : char TF-IDF (3-5), min_df=3, max_features=20000
- Classifieur : LogisticRegression (C=1.0, balanced, saga, max_iter=2000)
- Seuils : low=0.05, high=0.85

## C. Tests

7 tests passent (test_validation.py).

## D. Reproductibilité

- Graine aléatoire : 42
- Hashes des splits dans `data/splits/hashes/v1.json`
- Expériences dans `experiments/results/EXP001-EXP021.json`