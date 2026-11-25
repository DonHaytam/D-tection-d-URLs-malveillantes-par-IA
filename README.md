# Phishing AI Master 2 — Detection intelligente des URL de phishing et malveillantes

Détection intelligente des URL de phishing et malveillantes par Intelligence Artificielle et Machine Learning.

Projet de Master 2 Intelligence Artificielle — Cybersécurité.

## Vue d'ensemble

Ce projet implémente un pipeline de machine learning complet pour la détection de phishing dans les URL : exploration des données, ingénierie de features (lexicales, structurelles, caractéristiques caractères), entraînement de 6 modèles, comparaison rigoureuse, sélection d'un modèle, évaluation sur des jeux de données bloqués et indépendants, et déploiement d'une application locale (API FastAPI + interface Streamlit + base SQLite).

## Installation

Voir [INSTALLATION.md](INSTALLATION.md).

## Structure du projet

```
phishing_ai_master/
├── data/
│   ├── raw/            # Jeux de données bruts (brut d'acquisition)
│   ├── interim/        # Données nettoyées, intermédiaires
│   ├── processed/      # Données prétraitées
│   ├── splits/         # TRAIN / DEV / LOCKED_TEST / INDEPENDENT_FINAL_TEST
│   ├── manifests/      # Manifests de données (provenance)
│   └── external/       # Données externes (Tranco, Common Crawl, etc.)
├── notebooks/          # 01_data_exploration ... 06_final_evaluation
├── src/                # Code modulaire (data, features, models, evaluation, inference, policy, utils)
├── models/versions/    # Artifacts de modèles versionnés
├── experiments/        # Résultats et configurations d'expériences (EXPxxx.json)
├── reports/            # Rapports et figures (dossier de l'analyse)
├── deployment/         # api/ et frontend/
├── database/           # Historique des prédictions (SQLite)
├── tests/              # Tests unitaires et d'intégration
├── configs/            # Fichiers de configuration
├── scripts/            # Scripts utilitaires
├── requirements.txt
└── README.md
```

## Langues

Le code est en anglais (pratique professionnelle), les rapports et documents techniques du projet sont en français (exigence du Master 2).

## Workflow critique

1. Phases 1-5 : Environnement, données, exploration, nettoyage, splits (TRAIN/DEV/LOCKED_TEST).
2. Phases 6-8 : Features, modèles, entraînement/tuning sur TRAIN + DEV uniquement.
3. Phases 9-11 : Comparaison, généralisation, sélection (coûts de sécurité).
4. Phases 12-13 : Vérouillage du modèle + évaluation finale indépendante (une seule fois).
5. Phases 14-17 : Application, tests, rapport final, audit.

## Statut du projet

Voir [reports/RAPPORT_FINAL_MASTER_IA.md](reports/RAPPORT_FINAL_MASTER_IA.md) à la fin du projet.
