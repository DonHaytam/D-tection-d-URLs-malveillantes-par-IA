# DATA SOURCES AUDIT — Phishing AI Master 2

## 1. Sources investigated

| Source | Type | Size | License | Access | Legitimate auth URLs? | Verdict |
|---|---|---|---|---|---|---|
| HuggingFace (ealvaradob/phishing-dataset) | Mixte | 835 697 | À vérifier | Libre | 0.32% (184/58221) | RETENU (principal) |
| Tranco (tranco-list.eu) | Légitime | 1 000 000 | CC BY 3.0/4.0 | Libre | 0 (domaines uniquement) | RETENU (domaines) |
| PhishTank (Zenodo) | Phishing | 149 188 | PhishTank ToU | Libre | N/A (phishing) | RETENU (phishing) |
| PhiUSIIL (UCI) | Mixte | 235 795 | CC BY-SA 4.0 | Libre | 141 (dont faux positifs) | Non retenu (même biais) |
| PILU-60K (Unileón) | Mixte | 60 000 | CC BY 4.0 | Sur demande (email) | 20 000 (réels) | NON DISPONIBLE (email requis) |
| Common Crawl CDX | Web index | Billions | Libre | API (instable) | 3 URLs collectées | NON FIABLE |
| darkknight25 (HuggingFace) | Synthétique | 1 000 | Non spécifié | Libre | 0 (synthétique) | Non retenu |
| URL-Phish (Mendeley) | Mixte | 116 600 | CC BY 4.0 | Compte requis | Non vérifié | Bloqué |
| PhiUSIIL (Kaggle) | Mixte | 235 795 | CC BY-SA 4.0 | Compte requis | Non vérifié | Bloqué |
| LegitPhish (Mendeley) | Mixte | — | À vérifier | Compte requis | Non vérifié | Bloqué |
| OpenPhish | Phishing | Temps réel | Licence académique | Sur demande | N/A | Bloqué |
| URLhaus | Malicious | Temps réel | abuse.ch | API key requise | N/A | Bloqué |

## 2. Key finding

**Aucune source librement accessible ne fournit de URLs légitimes d'authentification en quantité suffisante.**

Le seul dataset connu avec 20 000 URLs légitimes d'authentification réelles est PILU-60K (Sánchez-Paniagua et al., 2022), disponible sur demande par email à gvis@unileon.es.

## 3. Dataset bias confirmed

| Métrique | Légitimes | Phishing |
|---|---:|---:|
| URLs d'authentification | 0.32% | 4.78% |
| P(phishing \| login) | — | 0.9766 |
| P(phishing \| paypal) | — | 0.9939 |
| P(phishing \| dropbox) | — | 0.9950 |

## 4. Conclusion

Le dataset actuel est biaisé : les URLs légitimes sont dominées par des homepages (43.83%) et des URLs "other" (54.84%), avec seulement 0.32% d'URLs d'authentification. Ce biais est la cause racine des faux positifs.

La solution nécessite des URLs légitimes d'authentification réelles, disponibles dans PILU-60K (sur demande) ou à collecter manuellement.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Audit des sources de données.*