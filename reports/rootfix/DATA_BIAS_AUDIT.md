# DATA BIAS AUDIT — Phishing AI Master 2 (Rootfix)

## 1. Dataset composition

- TRAIN: 114 873 URL (58 221 légitimes / 56 652 phishing).
- DEV: 22 586 URL (10 885 légitimes / 11 701 phishing).

## 2. URL type distribution (TRAIN)

### Légitimes
- homepage: 43.83%
- other: 54.84%
- authentication: 0.32%
- account: 0.10%
- password_reset: 0.07%
- security_verify: 0.05%

### Phishing
- other: 53.12%
- homepage: 38.21%
- authentication: 4.78%
- dashboard: 1.94%
- account: 0.67%
- security_verify: 0.54%

## 3. Token frequency bias

| Token | P(phishing\|token) | Légitimes | Phishing |
|---|---:|---:|---:|
| login | 0.9766 | 0.15% | 6.64% |
| signin | 0.9542 | 0.03% | 0.59% |
| account | 0.9275 | 0.14% | 1.83% |
| verify | 0.9881 | 0.01% | 0.59% |
| secure | 0.9611 | 0.07% | 1.87% |
| paypal | 0.9939 | 0.01% | 2.29% |
| dropbox | 0.9950 | 0.01% | 2.10% |
| amazon | 0.3518 | 1.25% | 0.70% |
| google | 0.7930 | 0.38% | 1.48% |

## 4. Conclusion

La classe légitime est dominée par des homepages (43.83%) et des URLs "other" (54.84%). Seulement 0.32% sont des URLs d'authentification. La classe phishing contient 4.78% d'URLs d'authentification. Cette asymétrie crée un raccourci : "login" → phishing.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Audit du biais des données.*