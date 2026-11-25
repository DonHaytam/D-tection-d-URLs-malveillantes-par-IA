# PRODUCTION READINESS GATE — Phishing AI Master 2

## Statut

**STATUS = BLOCKED**

Aucun modèle ne satisfait simultanément Recall ≥ 0.85 ET FPR ≤ 0.01 sur le jeu DEV.

## Conditions obligatoires

| Condition | Statut | Détail |
|---|---|---|
| Jeu final indépendant existe | ❌ | Réservé (à acquérir Phase 13) |
| Jeu final jamais utilisé en développement | ✅ | Procédure respectée |
| Modèle gelé avant évaluation | ⏳ | Non gelé |
| Seuils gelés avant évaluation | ⏳ | Non gelés |
| Recall ≥ 0.85 | ❌ | Meilleur : M2 SVM = 0.8590 (brut) ; M1_HARDNEG = 0.8422 |
| FPR ≤ 0.01 | ❌ | Meilleur brut : M1 = 0.0548 ; avec hard-neg : 0.0381 ; avec allow-list : 0.0207 |
| Performance cross-source acceptable | ⏳ | Non mesuré |
| Performance domain-disjoint acceptable | ⏳ | Non mesuré |
| Calibration acceptable | ✅ | Isotonic : ECE 0.0000, Brier 0.0761 |
| Performance hard-negatives acceptable | ⚠️ | FPR réduit de 0.0548 à 0.0381 |
| Pas de fuite de données majeure | ✅ | Audit Phase 4-5 OK |
| Revue de sécurité complétée | ⏳ | Partielle |
| Tests end-to-end passent | ✅ | 7 tests passent, API fonctionnelle |
| Reproductibilité vérifiée | ✅ | Expériences EXP001-EXP011, hashes |

## Meilleur candidat expérimental

- **M1_LR** (Logistic Regression, char TF-IDF) : Recall 0.8478, FPR 0.0548, ROC-AUC 0.9593.
- **M1_LR_HARDNEG** (après hard-negative mining) : Recall 0.8422, FPR 0.0381, ROC-AUC 0.9610.

## Écart par rapport à la cible

- FPR : 0.0381 (meilleur) vs 0.01 (cible) → **3.8× au-dessus**.
- Recall : 0.8422 (meilleur post-hardneg) vs 0.85 (cible) → manque 0.0078.

## Facteurs limitants

1. **Raccourci lexical** : le modèle associe les tokens de marque (login, bank, amazon, paypal) à la classe phishing sans vérifier le contexte du domaine.
2. **Biais HTTP** : le schéma HTTP est sur-pondéré comme signal de phishing.
3. **Sous-représentation de TLDs** : .cn (FPR 0.549), .ar (FPR 0.417) ont des FPR très élevés.
4. **Données historiques** : PhishTank 2015 → risque de concept drift.
5. **Pas de données de réputation de domaine** : sans source externe, le modèle ne peut pas distinguer les domaines officiels des imitations.

## Directions d'optimisation futures

1. Intégrer des features de réputation de domaine (Tranco rank, âge du domaine).
2. Améliorer la représentation des domaines (embeddings de domaine).
3. Collecter des données de phishing récentes (2024-2025).
4. Utiliser une allow-list restrictive (top 10k Tranco) comme couche de politique.
5. Entraîner un modèle de second niveau (stacking) sur les prédictions de M1.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Phase 23 (Production-readiness gate).*


## Mise a jour finale (Phase 15)

Ensemble (soft voting M1+M2+M5): Recall 0.8698, FPR 0.0353, ROC-AUC 0.9741.
Meilleur FPR (M1_HARDNEG): 0.0381, Recall 0.8422.
Aucune configuration ne satisfait FPR <= 0.01.
STATUS = BLOCKED maintenu.
