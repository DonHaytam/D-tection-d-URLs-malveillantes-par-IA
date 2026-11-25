# Audit des données externes — 25 novembre 2026

## Périmètre

Audit passif des fichiers déposés manuellement dans `data/`. Aucune URL n'a été visitée, résolue, rendue ou exécutée. Les fichiers ont été lus comme des données non fiables.

## Fichiers audités

| Source | Fichier | Taille | SHA-256 | Lignes brutes | URLs valides | Labels |
|---|---|---:|---|---:|---:|---|
| `url_dataset_450k` | `URL dataset.csv` | 32 312 600 o | `accb2dfb…b466` | 450 176 | 449 750 | 345 738 légitimes / 104 012 phishing |
| `phishing_urls_54k` | `Phishing URLs.csv` | 4 196 046 o | `00762308…6041` | 54 807 | 54 804 | 54 804 phishing |
| `legitphish_v2` | `url_features_extracted1.csv` | 8 963 838 o | `8685e790…dbcd` | 101 219 | 101 218 | 37 540 légitimes / 63 678 phishing |

Mapping des labels :
- `URL dataset.csv` : `legitimate` → 0, `phishing` → 1.
- `Phishing URLs.csv` : `Phishing` → 1.
- `LegitPhish` : `ClassLabel=1` → légitime (0), `ClassLabel=0` → phishing (1).

## Dataset exclu

`data/Phishing Detection Dataset/.../Dataset.csv` (247 950 lignes) est **exclu** : il ne contient que des features précalculées, sans colonne URL. Il ne peut pas entrer dans le pipeline URL et aucune URL ne doit être reconstruite.

## URLs d'authentification

| Source | Légitimes avec chemin d'auth | Phishing avec chemin d'auth |
|---|---:|---:|
| `url_dataset_450k` | 111 | 7 553 |
| `phishing_urls_54k` | 0 | 993 |
| `legitphish_v2` | 0 | 205 |
| **Total pool** | **81** | **7 529** |

Le déséquilibre reste massif : 81 URLs légitimes d'authentification contre 7 529 URLs phishing d'authentification dans le pool externe. Les datasets manuels ne résolvent donc pas à eux seuls le biais `login = phishing`.

## Doublons, conflits et fuites

- Doublons normalisés supprimés : 526.
- Conflits de label entre sources : 0 (aucun groupe conservé en conflit).
- Conflit avec un split projet : 1 (quarantaine).
- Chevauchement exact avec un split projet : 2 485 URLs (2 307 + 24 + 154), exclues du pool externe.
- Chevauchement de domaine avec DEV/LOCKED_TEST/INDEPENDENT : 84 342 lignes, mises en quarantaine pour éviter la fuite.
- URLs invalides : 428.
- Label inconnu : 1.

## Pool externe éligible

| Élément | Valeur |
|---|---:|
| Lignes | 518 419 |
| Légitimes (0) | 325 671 |
| Phishing (1) | 192 748 |
| Domaines registrables uniques | 188 395 |

## Splits externes domain-disjoints

| Split | Lignes | Légitimes | Phishing | Domaines | Rôle |
|---|---:|---:|---:|---:|---|
| `EXTERNAL_TRAIN` | 312 614 | 229 992 | 82 622 | 61 807 | entraînement candidat |
| `EXTERNAL_DEV` | 62 767 | 31 931 | 30 836 | 42 196 | validation externe |
| `EXTERNAL_TEST` | 143 038 | 63 748 | 79 290 | 84 392 | test externe (non utilisé pour la sélection) |

Les domaines de `EXTERNAL_DEV` et `EXTERNAL_TEST` sont disjoints de tous les splits projet. `EXTERNAL_TRAIN` peut réutiliser des domaines de TRAIN, mais les URLs exactes ont été dédupliquées.

## Anomalie importante détectée dans l'expérience EXP027

L'ancien script `integrate_url_dataset.py` inversait les labels : il affectait `1` aux URLs légitimes et `0` aux URLs phishing, alors que la convention du projet est `0 = légitime`, `1 = phishing`. Les métriques dégradées d'EXP027 (FPR 0.1016) sont donc invalides et ne doivent pas être utilisées comme preuve que les données externes sont nuisibles. Les candidats de la nouvelle expérience utilisent le mapping corrigé.

## Fichiers produits

- `data/integrated/external_pool.csv`
- `data/integrated/external_train.csv`
- `data/integrated/external_dev.csv`
- `data/integrated/external_test.csv`
- `data/integrated/external_audit.json`
- `data/quarantine/external_quarantine.csv`

---
*Rapport généré par `scripts/data_expansion/audit_external.py` et `scripts/data_expansion/build_integrated.py`.*
