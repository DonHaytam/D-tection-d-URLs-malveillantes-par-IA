# Expériences modèles — données externes corrigées

## Contexte

L'expérience EXP027 avait intégré le dataset 450K avec des **labels inversés** (légitime=1, phishing=0 au lieu de 0/1). Ses métriques (FPR 0.1016) sont donc invalides. Les expériences EXP028–EXP034 utilisent le mapping corrigé et des splits externes domain-disjoints.

## Configuration

- Représentation : TF-IDF caractères 3–5, `min_df=3`, `max_features=20000`, `sublinear_tf=True`.
- Classifieur : régression logistique, `class_weight="balanced"`, `saga`, `max_iter=2000`, graine 42.
- `EXTERNAL_TRAIN` : 312 614 lignes (229 992 légitimes / 82 622 phishing).
- `EXTERNAL_DEV` : 62 767 lignes (31 931 / 30 836), domaines disjoints de tous les splits projet.
- `DEV` projet : 22 586 lignes (10 885 / 11 701), inchangé.

## Résultats sur DEV (sélection)

| Candidat | Recall@0.5 | FPR@0.5 | ROC-AUC | Recall@FPR≤1% | FPR@FPR≤1% |
|---|---:|---:|---:|---:|---:|
| `M1_LR_HARDNEG` (déployé) | 0.8422 | 0.0381 | 0.9610 | **0.7440** | 0.0099 |
| `CLEAN_TRAIN_ONLY` (EXP028) | 0.8477 | 0.0548 | 0.9593 | 0.7139 | 0.0099 |
| `EXT_RANDOM_40K` (EXP029) | 0.8459 | 0.0573 | 0.9563 | 0.7068 | 0.0099 |
| `EXT_RANDOM_80K` (EXP030) | 0.8457 | 0.0617 | 0.9539 | 0.7016 | 0.0098 |
| `EXT_RANDOM_160K` (EXP031) | 0.8470 | 0.0682 | 0.9511 | 0.6990 | 0.0099 |
| `EXT_HARD_20K` (EXP032) | 0.8445 | 0.0597 | 0.9552 | 0.7080 | 0.0099 |
| `EXT_HARD_40K` (EXP033) | 0.8449 | 0.0627 | 0.9543 | 0.7072 | 0.0099 |
| `EXT_RANDOM_160K_W0.5` (EXP034) | 0.8455 | 0.0621 | 0.9536 | 0.7009 | 0.0099 |

**Aucun candidat externe ne bat le modèle déployé sur DEV.** Les données externes augmentent le FPR et diminuent le recall à FPR ≤ 1%. Le modèle déployé reste le meilleur sur le jeu de validation projet.

## Résultats sur EXTERNAL_DEV (validation externe)

| Candidat | Recall@0.5 | FPR@0.5 | ROC-AUC | Recall@FPR≤1% |
|---|---:|---:|---:|---:|
| `M1_LR_HARDNEG` | 0.9464 | 0.0488 | 0.9858 | 0.9198 |
| `CLEAN_TRAIN_ONLY` | 0.9478 | 0.0567 | 0.9852 | 0.9175 |
| `EXT_RANDOM_40K` | 0.9623 | 0.0065 | 0.9963 | 0.9675 |
| `EXT_RANDOM_80K` | 0.9654 | 0.0038 | 0.9972 | 0.9770 |
| `EXT_RANDOM_160K` | 0.9680 | 0.0025 | 0.9977 | 0.9831 |
| `EXT_HARD_20K` | 0.9662 | 0.0027 | 0.9975 | 0.9810 |
| `EXT_HARD_40K` | 0.9662 | 0.0024 | 0.9977 | 0.9830 |

Les candidats entraînés avec des données externes généralisent mieux sur la distribution externe, ce qui est attendu (ils ont vu cette distribution). Cela ne se traduit pas par une amélioration sur DEV.

## Interprétation

1. Les données externes sont **plus faciles** que DEV : le modèle de base atteint déjà 0.946 de recall et 0.0488 de FPR sur `EXTERNAL_DEV`.
2. Le dataset 450K contient très peu d'URLs légitimes d'authentification (81 dans tout le pool), donc il ne corrige pas le biais principal.
3. Les URLs légitimes externes sont majoritairement des pages d'accueil ; elles n'apprennent pas au modèle à reconnaître les chemins d'authentification légitimes.
4. Le modèle déployé, entraîné sur DEV hard negatives, reste meilleur sur DEV mais ses métriques DEV sont optimistes (fuite DEV → TRAIN lors du hard-negative mining initial).

## Conclusion

Les nouvelles données ne permettent pas de lever le verrou de production sur DEV. Elles sont utiles pour mesurer la robustesse cross-source, mais ne doivent pas remplacer le modèle déployé sans preuve d'amélioration sur DEV.

---
*Rapport généré par `scripts/data_expansion/train_external_candidates.py`.*
