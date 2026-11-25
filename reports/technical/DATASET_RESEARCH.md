# Phase 2 — Recherche et acquisition de datasets (document de recherche)

*Statut : en cours. Mise à jour au fur et à mesure des vérifications réelles.*

## Sources candidates évaluées (24 novembre 2026)

| Source | Type d'URLs | Disponibilité vérifiée | Licence / Conditions | Accès programmatique | Verdict |
|---|---|---|---|---|---|
| Tranco (tranco-list.eu) | Légitime (top 1M domains) | Oui — téléchargement direct `top-1m.csv.zip` (9,7 Mo) | CC BY 3.0 / 4.0 (Cisco Umbrella, Majestic, CrUX, Cloudflare Radar) | Oui, sans compte | **RETENU (légtime)** |
| PhishTank (Zenodo, 10.5281/zenodo.8371046) | Phishing (XLSX, "Valid_Phishes_Offline") | Oui — téléchargement direct via API Zenodo (1 fichier XLSX = 16,6 Mo) | PhishTank Terms of Use (Cisco Talos) — usage recherche autorisé | Oui, sans compte (Zenodo) | **RETENU (phishing, en cours d'analyse)** |
| URL-Phish (Mendeley, 10.17632/65z9twcx3r.2) | Mixte (116 600 URLs, 16 600 phishing + 100 000 benign) | Vérifié (référence) — téléchargement bloqué (403) — compte Mendeley requis | CC BY 4.0 | Non (compte requis) | **NON RETENU pour l'instant (bloqué)** |
| PhiUSIIL (Kaggle) | Mixte (235 795 URLs) | Vérifié (référence) — compte Kaggle + API token requis | CC BY-SA 4.0 | Non (token requis) | **NON RETENU pour l'instant (bloqué)** |
| LegitPhish (Mendeley, 10.17632/hx4m73v2sf.2) | Mixte (URLhaus + phishing repos / StackOverflow + Wikipedia) | Vérifié (référence) — compte Mendeley requis | À vérifier | Non (compte requis) | **NON RETENU pour l'instant (bloqué)** |
| PhishTank live feed | Phishing (temps réel) | Vérifié (site actif) — compte + API key requis | PhishTank Terms of Use | Non (compte requis) | **NON RETENU pour l'instant (bloqué)** |
| OpenPhish | Phishing (temps réel) | Vérifié (site actif) — licence académique requise | OpenPhish Academic Use Program | Non (demande académique) | **NON RETENU pour l'instant (bloqué)** |
| URLhaus | Malicious URLs | Vérifié (site actif) — téléchargement CSV bloqué (410 Gone) — API key requise | abuse.ch | Non (API key requise) | **NON RETENU pour l'instant (bloqué)** |
| Zenodo ROR (10.5281/zenodo.6347574) | Domaines (organisations) | Vérifié (référence) — non pertinent directement (utilisé par URL-Phish pour les benign) | À vérifier | Oui | **NON RETENU (non pertinent directement)** |

## Téléchargements effectués (vérifiés)

1. **Tranco top-1m.csv.zip** → `data/raw/tranco_top1m.csv.zip` (9 701 869 octets, sha256 `b812c6edbe5dd264c7a804de9546549b961fe176ad9be10a8a8f3ba90f7bc54c`). Contenu : `top-1m.csv` (rank, domain). 1 000 000 domaines.
2. **PhishTank offline 1 (Zenodo)** → `data/raw/phishtank_offline_1.xlsx` (16 596 713 octets, sha256 `37c59dfa9b80018650c31e1ae380da48a3875f44551cf4fa5d9b9f8549eb4887`). Schéma à vérifier (lecture en cours).

## Décision provisoire (Phase 2)

- **Source légitime retenue pour l'instant :** Tranco (top-1m). Licence documentée (CC BY 3.0/4.0 selon les composantes). Attribution requise.
- **Source phishing retenue pour l'instant :** PhishTank (Zenodo offline 1). Licence PhishTank Terms of Use — usage recherche autorisé (Cisco Talos).
- **Bloqueurs pour Phase 3 :** Schéma des XLSX PhishTank à vérifier ; nombre d'URLs utilisables à confirmer ; déduplication et nettoyage (Phase 4).

## Prochaines étapes (Phase 3 — exploration des données)

1. Charger `phishtank_offline_1.xlsx` et extraire les URLs phishing.
2. Charger `tranco_top1m.csv.zip` et extraire les URLs/domaines légitimes.
3. Construire un manifest initial (url, label, source, collection_date, domain, registrable_domain, tld, scheme, path, query, fragment, dataset_version) dans `data/manifests/`.
4. EDA : comptages, TLDs, longueurs, sources, duplicats.

*Note : l'acquisition de sources additionnelles (URL-Phish, PhiUSIIL, LegitPhish) est possible si l'utilisateur fournit les comptes/licences requis. Documenter dans DATA_PROVENANCE.md.*

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Phase 2 (Recherche et acquisition de datasets).*
