# DATA PROVENANCE — Phishing URL detection project (framework — à compléter en Phases 2-4)

> *Rédaction en cours — Suivi de la provenance de toutes les données utilisées par le projet. Suivi obligatoire par Phase 4 (Nettoyage et audit de fuites).*

## Sources primaires (acquisition vérifiée — Phase 2)

## Sources primaires (acquisition vérifiée — Phase 2)

| Source | Type | Licence / Conditions | Date de collecte | Date d'accès (provenance légale) | Type d'URL | Vérifiée par |
|---|---|---|---|---|---|---|
| PhishTank (Zenodo, 10.5281/zenodo.8371046) | Phishing URLs | PhishTank Terms of Use (Cisco Talos) — usage recherche autorisé | Décembre 2015 (données historiques) | 24 novembre 2026 | Phishing | Téléchargement direct via API Zenodo (sha256 `37c59dfa...`) |
| Tranco (tranco-list.eu) | Domaines légitimes (top 1M) | CC BY 3.0 / 4.0 (Cisco Umbrella, Majestic, CrUX, Cloudflare Radar) — attribution requise | Liste courante (top-1m) | 24 novembre 2026 | Légitime | Téléchargement direct `top-1m.csv.zip` (sha256 `b812c6ed...`) |

*À compléter avec les lignes correspondant aux datasets réellement utilisés. Ne pas ajouter de lignes pour des datasets non utilisés.*

## Pilotes de vérification de provenance (Phase 2)

1. **Vérification de disponibilité :** `data/manifests/manifest_<source>_v<version>.json` — contient URL, label, source, collection_date, domain, registrable_domain, tld, scheme, path, query, fragment, dataset_version.
2. **Audit de licence :** Licence dans `reports/licenses/<source>_license.md` — droits documentés (usage commercial, research, attribution, etc.).
3. **Date de collecte :** Dispo dans le manifest et dans `reports/DATASET_CARD.md`.

## Transformation et lineage (Phase 4)

- **Déduplication exacte :** Savegarde dans `data/interim/dedup_report_v1.json` (clés hashées de l'URL, comptages avant/après).
- **Déduplication normalisée :** Savegarde dans `data/interim/dedup_normalized_v1.json`.
- **Extraction de registrable_domain :** Serveur — `src/data/deduplication.py` + tests.
- **Manifest des splits :** `data/splits/TRAIN.json`, `data/splits/DEV.json`, `data/splits/LOCKED_TEST.json`, `data/splits/INDEPENDENT_FINAL_TEST.json` (procédure documentée dans `DATA_LEAKAGE_AUDIT.md`).
- **Hashes des datasets :** Compute via `scripts/verify_data_hashes.py` — enregistrés dans `data/splits/hashes/v1.json` et référencés dans les expériences (`experiments/results/*.json`).

## Datasets externes (Phase 2-3)

| Nom | Type | Description | Source / URL | Licence | Date d'acquisition | Indicateurs d'utilisation |
|---|---|---|---|---|---|---|
| (ex: CSV FromCMSElectric...) | (ex: CSV / JSON / pcap) | (à compléter) | (URL) | (licence) | (à compléter) | (à compléter) |

*Pour les datasets copiés localement : remplacer la ligne web par la localisation fichier.*

## Liens utiles

- [DATASET_CARD.md](DATASET_CARD.md)
- [DATA_LEAKAGE_AUDIT.md](DATA_LEAKAGE_AUDIT.md)

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Suivi de la provenance des données (Phases 2-4).*
