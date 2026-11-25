# FINAL DATA EXPANSION REPORT V5 — Phishing AI Master 2

## Executive Summary

Investigation of 7 additional datasets. **None were freely downloadable without authentication.** All Mendeley datasets (CompPhish, Suspicious Phishing, PWD2021, URL-Phish, Phishing URL 450K, Phishing URL 2026) return HTTP 403. PhishStorm requires registration. GramBeddings requires a Google Form.

## Dataset Acquisition Status

| Dataset | Status | Records | License | Blocker |
|---|---|---:|---|---|
| GramBeddings | REQUEST_REQUIRED | 800 000 | Non spécifié | Google Form |
| LegitPhish V2 | ACCOUNT_REQUIRED | 101 219 | CC BY 4.0 | Mendeley 403 |
| PhishStorm | ACCOUNT_REQUIRED | 96 018 | Non spécifié | Mendeley 403 |
| PWD2021 | ACCOUNT_REQUIRED | 80 000 | CC BY 4.0 | Mendeley 403 |
| URL-Phish V2 | ACCOUNT_REQUIRED | 116 600 | CC BY 4.0 | Mendeley 403 |
| Phishing URL 450K | ACCOUNT_REQUIRED | 450 176 | CC BY 4.0 | Mendeley 403 |
| Phishing URL 2026 | ACCOUNT_REQUIRED | 149 726 | CC BY 4.0 | Mendeley 403 |

## Total freely available datasets (already in project)

| Dataset | Records | Legit auth URLs |
|---|---:|---:|
| HuggingFace | 835 697 | 184 (0.02%) |
| Tranco | 1 000 000 | 0 (domains) |
| PhishTank | 149 188 | N/A (phishing) |
| PhiUSIIL | 235 795 | 141 (0.06%) |

## Key finding

**No freely accessible source provides verified legitimate authentication URLs in sufficient quantity.** The only known source is PILU-60K (20 000 real legit auth URLs), available on request by email to gvis@unileon.es.

## Root cause (unchanged)

The dataset teaches "login = phishing" because legitimate URLs contain authentication keywords in only 0.32% of cases vs 4.78% for phishing.

## Production status

**STATUS = BLOCKED** — cibles non atteintes. Solution requise : collecter des URLs légitimes d'authentification réelles.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Rapport final d'expansion V5.*