# Rapport d'environnement — 24 novembre 2026 (Phase 1)

*Informations système vérifiées sur la machine locale avant le démarrage du projet.*

## Système d'exploitation

|Champ|Valeur vérifiée|
|---|---|
|Système|Microsoft Windows 11 Famille|
|Version|10.0.26200|
|Architecture|64 bits|

## Matériel

|Champ|Valeur vérifiée|
|---|---|
|CPU|8 cœurs logiques (`os.cpu_count()` = 8)|
|RAM visible|≈ 8 Go (81 830 944 Ko ≈ 7,9 GiB)|
|GPU|Intel(R) Iris(R) Xe Graphics, 2 Go (pas de GPU NVIDIA, Torch en mode CPU)|

## Stockage

|Lecteur|Total|Utilisé|Libre|
|---|---|---|---|
|D:|≈ 96,0 Go|≈ 86,9 Go|≈ 9,0 Go|

## Versions logicielles (Python cible : 3.10)

|Composant|Version vérifiée|
|---|---|
|Python|3.10.0|

## Packages Python vérifiés (sélection)

|Package|Version|
|---|---|
|numpy|2.2.6|
|pandas|2.3.3|
|scipy|1.15.3|
|matplotlib|3.10.9|
|scikit-learn|1.7.2|
|joblib|1.5.3|
|mlflow|3.17.2|
|torch|2.12.0+cpu|
|transformers|4.45.2|
|sentence-transformers|5.5.1|
|fastapi|0.142.2|
|uvicorn|0.47.0|
|streamlit|1.57.0|
|pytest|9.1.1|
|SQLAlchemy|2.0.55|
|httpx|0.28.1|
|IPython|(présent)|

## Packages non installés au démarrage (Phase 1)

|Package|Statut|Conséquence|
|---|---|---|
|xgboost|Non installé au démarrage|Installé dans `vendor_libs/` → M5 activable|
|lightgbm|Non installé au démarrage|Installé dans `vendor_libs/` → alternative M4 activable|
|seaborn|Non installé au démarrage|Installé dans `vendor_libs/` → figures publication-quality|
|plotly|Non installé au démarrage|Installé plus tard via `pip install plotly` si besoin (échec disk C:) → figs interactives optionnelles|

Installations effectuées :
- `python -m pip install --target "D:\openhands\projects\v2\vendor_libs" xgboost lightgbm seaborn` (C: pratiquement saturé).
- Versions vérifiées dans `vendor_libs/` : xgboost 3.2.0, lightgbm 4.7.0, seaborn 0.13.2.
- plotly 7.1.0 installé dans site-packages (vérifié par `import plotly`).

Voir [vendor_libs/README.txt](../vendor_libs/README.txt).

## Limitations connues

- Pipeline conçu CPU-compatible. Le calcul sur GPU utilise Torch uniquement si disponible (`torch.cuda.is_available()` = False à ce stade).
-ession RAM à surveiller pour les Vectorisation (TF-IDF char) avec corpus modéré.
