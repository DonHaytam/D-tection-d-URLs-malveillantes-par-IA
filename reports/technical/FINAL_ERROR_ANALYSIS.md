# FINAL ERROR ANALYSIS — Phishing AI Master 2

## 1. Final model: M1_LR_HARDNEG

- Recall = 0.8422, FPR = 0.0381, Precision = 0.9596, ROC-AUC = 0.9610.

## 2. Remaining false positives

After hard-negative mining, FPR reduced from 0.0548 to 0.0381 (30% reduction). Remaining FPs are concentrated in:
- TLDs sous-représentés (.cn, .ar, .jp, .it).
- URLs courtes avec tokens suspects sur domaines non officiels.
- Domaines de marques sur TLDs non standard (paypal.me, amazon.cn).

## 3. Remaining false negatives

- URLs phishing courtes sans tokens suspects (domaines génériques).
- Phishing sur domaines légitimes détournés (docs.google.com/forms).
- URLs avec peu de caractères distinctifs.

## 4. Root cause summary

Le modèle repose sur des n-grammes de caractères qui capturent les patterns de tokens suspects. Sans données de réputation de domaine, il ne peut pas distinguer les domaines officiels des imitations. L'amélioration des features (brand position, Tranco rank) n'a pas réduit le FPR car le signal char TF-IDF domine.

## 5. Why targets were not achieved

- FPR 0.0381 vs 0.01 : écart de 3.8×. Les faux positifs résiduels sont des URLs légitimes contenant des tokens suspects sur des domaines non reconnus.
- Recall 0.8422 vs 0.85 : écart de 0.0078. Les faux négatifs sont des phishing sans tokens suspects.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Phase finale.*
