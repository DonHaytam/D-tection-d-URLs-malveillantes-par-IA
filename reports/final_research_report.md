# FINAL RESEARCH REPORT — Phishing AI Master 2

## 1. Summary

This project implemented a complete phishing URL detection system with 6 ML models, extensive optimization, and honest evaluation.

## 2. Root cause identified

The dataset teaches "login = phishing" because legitimate URLs contain authentication keywords in only 0.32% of cases vs 4.78% for phishing. This is a dataset construction bias.

## 3. Best model

M1_LR_HARDNEG (Logistic Regression, char TF-IDF, hard-negative mining):
- Recall: 0.8422 (binary) / 0.7383 (three-class at 0.25/0.75)
- FPR: 0.0381 (binary) / 0.0087 (three-class at 0.25/0.75)
- ROC-AUC: 0.9610
- ECE: 0.0370

## 4. Production status

**BLOCKED** — targets not met (Recall < 0.85, FPR > 0.01 in binary mode).

## 5. Solution required

Collect real legitimate authentication URLs (e.g., from PILU-60K, available on request) and retrain with domain-disjoint splits.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Rapport de recherche final.*