# BRAND IMPERSONATION REPORT — Phishing AI Master 2

## 1. Principe

Les features d'impersonation de marque détectent si un token de marque apparaît dans le sous-domaine ou le chemin mais PAS dans le domaine registrable. Cela indique une tentative d'impersonation.

## 2. Features implémentées

- `brand_in_regdomain` : marque dans le domaine registrable (officiel).
- `brand_in_subdomain` : marque dans le sous-domaine (impersonation potentielle).
- `brand_in_path` : marque dans le chemin.
- `brand_mismatch` : marque dans sous-domaine/chemin mais PAS dans le domaine registrable.
- `brand_official` : marque dans le domaine registrable sans mismatch.
- `num_brand_tokens` : nombre de tokens de marque.

## 3. Résultats

Testé dans le modèle KP_BI (keyword position + brand impersonation) :
- FPR : 0.0910 (vs 0.0381 pour M1_HARDNEG).
- Recall : 0.7265 (vs 0.8422).
- ROC-AUC : 0.8935 (vs 0.9610).

Les features d'impersonation n'ont pas amélioré les performances car le signal char TF-IDF domine et les features numériques ajoutent du bruit.

## 4. Conclusion

Les features d'impersonation de marque sont conceptuellement utiles mais ne suffisent pas à elles seules. Elles pourraient être utiles dans un modèle hybride avec une meilleure pondération.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Brand impersonation.*