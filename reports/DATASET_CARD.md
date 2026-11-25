# DATASET CARD — Phishing URL detection project (framework — à compléter en Phase 2)

> *Rédaction en cours — Phases 2/3 (acquisition des données et exploration). Valeurs à remplacer par celles vérifiées.*

## Informations générales

- **Nom du dataset :** (à compléter)
- **Version :** (à compléter)
- **Dépôt de provenance / URL d'acquisition :** (à compléter)
- **Date de collecte :** (à compléter)
- **Licence / conditions d'utilisation :** (à compléter — compliance vérifiée)
- **Contact du dépositeur / auteur du dataset :** (à compléter, si applicable)

## Composition du dataset (sources vérifiées — Phase 2)

### Source principale — HuggingFace (ealvaradob/phishing-dataset, urls.json)

- **Fichier :** `data/raw/hf_phishing/urls.json`
- **Taille :** 73 157 496 octets
- **SHA-256 :** `32cfba42892c915b041a3f0ca6ffd0f484b2590c4c2ca91b13d3ea1330b2c9bd`
- **Enregistrements :** 835 697
- **Répartition :** 444 933 légitimes (label 0) / 390 764 phishing (label 1)
- **Schéma :** `{text: <url>, label: 0|1}`
- **Longueurs d'URL :** min 1, max 3 992, moyenne 47,48
- **Schémas :** 607 141 sans schéma, 143 316 https, 84 411 http, plus quelques anomalies (http dans query)
- **Licence :** à vérifier (repository HuggingFace — vérifier la licence du dataset avant usage académique)
- **Date d'acquisition :** 24 novembre 2026
- **Accès :** libre via `huggingface_hub` (pas de compte requis pour le téléchargement)

### Source légitime complémentaire — Tranco (tranco-list.eu)

- **Fichier :** `data/raw/tranco_top1m.csv.zip`
- **Taille :** 9 701 869 octets
- **SHA-256 :** `b812c6edbe5dd264c7a804de9546549b961fe176ad9be10a8a8f3ba90f7bc54c`
- **Contenu :** `top-1m.csv` (rank, domain) — 1 000 000 domaines
- **Licence :** CC BY 3.0 / 4.0 (Cisco Umbrella, Majestic, CrUX, Cloudflare Radar) — attribution requise

### Source phishing complémentaire — PhishTank (Zenodo, 10.5281/zenodo.8371046)

- **Fichier :** `data/raw/phishtank_offline_1.xlsx`
- **Taille :** 16 596 713 octets
- **SHA-256 :** `37c59dfa9b80018650c31e1ae380da48a3875f44551cf4fa5d9b9f8549eb4887`
- **Lignes :** 156 666 (149 188 "VALID PHISH", 129 367 uniques)
- **Problème de qualité :** ~105 750 URLs (71 %) sont tronquées avec "..." dans l'export Excel — **non utilisables telles quelles**
- **Décision :** conserver uniquement les 43 438 URLs non tronquées, OU utiliser comme source secondaire documentée

## Analyse exploratoire (EDA) — Phase 3 (résumé vérifié)

- **Enregistrements :** 835 697
- **URLs uniques :** 821 402
- **Hôtes uniques :** 448 803
- **Légitimes (label 0) :** 444 933
- **Phishing (label 1) :** 390 764
- **Longueur d'URL :** min 1, max 3 992, moyenne 47,48, médiane 37
- **Schéma :** 607 141 sans schéma, 143 316 https, 84 411 http
- **Top TLD :** com (486 714), org (70 023), cn (33 936), net (32 378), top (12 105), ca (11 621), edu (11 360), uk (11 296), (none/ip) (9 556), ru (8 619)

Figures générées : `reports/figures/eda/fig01_class_distribution.png` ... `fig04_scheme_distribution.png`.
Résumé JSON : `reports/tables/eda_summary.json`.

## Limitations connues à ce stade

1. Les données PhishTank datent de 2015 — risque de concept drift (Phase 11).
2. Les données Tranco sont des domaines (pas des URLs complètes) — construction des URLs légitimes à faire en Phase 4.
3. Le dataset HuggingFace a 607 141 URLs sans schéma — normalisation à faire en Phase 4.
4. Aucune source récente (2024-2025) n'est librement téléchargeable sans compte — documenté dans `reports/technical/DATASET_RESEARCH.md`.
5. Licence du dataset HuggingFace à vérifier avant usage académique.


## Domaine du problème

- **Type d'URL :** (avec/sans schéma, timeout, redirects autorisés ou non — NOT MEASURED si non vérifié)
- **Longueur maximale/minimale des URLs :** (à compléter)
- **Valeurs manquantes :** (à compléter)

## Prétraitement

- **Normalisation des URLs :** (décrire — exclusions de fragments, gestion du casing, etc.)
- **Filtrage des invalides :** (critères + effectué ou non — PAS inventé)
- **Deduplication :** (type de normalisation — ex: URL normalisée, sans fragment/casse)

## Biais connus (documentés selon Phase 3)

1. *(À compléter après EDA — ex: surreprésentation d'un TLD, un schéma HTTP vs HTTPS, absence de nouveaux domaines.)*

## Limitations

*(À compléter — biais non corrigés, manques de couverture géographique/temporelle, etc.)*

## Remerciements et crédits

*(À compléter — crédits à destination si applicable.)*

---

*Documentation générée par le pipeline du projet `phishing_ai_master` — Pipeline d'analyse des données (Phase 3). Les valeurs "À compléter" seront remplacées uniquement après vérification dans les données.*
