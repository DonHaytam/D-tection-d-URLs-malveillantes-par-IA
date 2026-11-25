# FEATURE ABLATION REPORT — Phishing AI Master 2 (Phase 3)

## 1. Résultats

| Configuration | Accuracy | Recall | FPR | ROC-AUC | ECE |
|---|---:|---:|---:|---:|---:|
| Char TF-IDF (URL complète) | 0.8947 | 0.8478 | 0.0548 | 0.9593 | 0.0304 |
| Char TF-IDF (sans schéma) | 0.8691 | 0.8365 | 0.0958 | 0.9436 | 0.0391 |
| Char TF-IDF (hôte seul) | 0.7614 | 0.7480 | 0.2242 | 0.8540 | 0.0246 |

## 2. Conclusions

1. **Le schéma (http/https) est un signal important** : sa suppression augmente le FPR de 0.0548 à 0.0958 et diminue l'AUC de 0.9593 à 0.9436.
2. **Le chemin et la query sont essentiels** : l'hôte seul donne FPR 0.2242 et AUC 0.8540, soit une dégradation majeure.
3. **La représentation complète (URL entière) est optimale** : tous les composants contribuent.

## 3. Implications

- Le modèle ne repose pas uniquement sur le domaine (ce qui serait un raccourci de mémorisation).
- Le chemin et la query portent un signal discriminant significatif.
- La suppression du schéma dégrade les performances, confirmant que le modèle utilise le schéma comme feature.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Phase 3 (Ablation des features).*