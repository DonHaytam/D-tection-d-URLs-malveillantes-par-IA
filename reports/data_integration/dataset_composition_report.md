# Dataset Composition Report — Phishing AI Master 2

## Current dataset (manifest_v1.csv)

- Total: 159 568 URL
- Légitimes: 79 842
- Phishing: 79 726
- Domaines registrables uniques: 96 155

## Legitimate URL type distribution

| Type | Count | Percentage |
|---|---:|---:|
| homepage | 25 518 | 43.83% |
| other | 31 928 | 54.84% |
| authentication | 184 | 0.32% |
| account | 56 | 0.10% |
| password_reset | 40 | 0.07% |
| security_verify | 30 | 0.05% |
| support | 188 | 0.32% |
| ecommerce | 138 | 0.24% |
| api_auth | 90 | 0.15% |
| dashboard | 47 | 0.08% |

## Authentication URL representation

- Legitimate auth URLs: 184 (0.32%)
- Phishing auth URLs: 2 707 (4.78%)

## Conclusion

Severe underrepresentation of legitimate authentication URLs (0.32%) vs phishing (4.78%). This is the root cause of the false positive problem.

---
*Documentation générée par le pipeline du projet `phishing_ai_master`.*