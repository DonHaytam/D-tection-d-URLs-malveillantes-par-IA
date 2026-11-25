# INSTALLATION — Phishing AI Master 2

## Prérequis

- Windows 10/11
- Python 3.10
- ~10 Go d'espace disque libre (disque D: recommandé)

## Installation

```powershell
cd D:\openhands\projects\v2\phishing_ai_master
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Les packages optionnels (xgboost, lightgbm, seaborn) sont installés dans `vendor_libs/`. Ajouter au PYTHONPATH :

```powershell
$env:PYTHONPATH = "D:\openhands\projects\v2\vendor_libs;D:\openhands\projects\v2\phishing_ai_master"
```

## Exécution

### API

```powershell
cd D:\openhands\projects\v2\phishing_ai_master
python -m uvicorn deployment.api.main:app --host 127.0.0.1 --port 8000
```

### Interface Streamlit

```powershell
cd D:\openhands\projects\v2\phishing_ai_master
streamlit run deployment/frontend/app.py
```

### Tests

```powershell
cd D:\openhands\projects\v2\phishing_ai_master
python -m pytest tests/ -q
```

## Données

Les données brutes sont dans `data/raw/` (non versionnées). Voir `reports/DATASET_CARD.md` et `reports/DATA_PROVENANCE.md`.

## Statut

Phase 1-7 amorcées. Modèles non encore entraînés (Phase 8). Application fonctionnelle en mode "model not loaded" jusqu'à l'entraînement.
