# GENERALIZATION REPORT — Phishing AI Master 2

## 1. Domain-disjoint evaluation

- Split par domaine registrable : aucun domaine ne traverse deux ensembles.
- 96 155 domaines registrables uniques.
- 591 domaines cross-label supprimés de l'entraînement.

## 2. Cross-source evaluation

- HuggingFace : FPR 0.0362, Recall ~0.84.
- Tranco : FPR 0.0407.
- Les deux sources ont des FPR comparables.

## 3. Temporal evaluation

- PhishTank data date de 2015 → risque de concept drift.
- Pas de données récentes disponibles pour évaluation temporelle.

## 4. Hard-negative evaluation

- FPR réduit de 0.0548 à 0.0381 (-30%) après hard-negative mining.
- Les hard negatives sont des légitimes avec tokens suspects.

## 5. Conclusion

Le modèle généralise raisonnablement bien sur les sources testées. Le principal risque est le concept drift (données PhishTank 2015).

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Généralisation.*