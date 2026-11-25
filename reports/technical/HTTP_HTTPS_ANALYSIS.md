# HTTP/HTTPS ANALYSIS — Phishing AI Master 2

## 1. Observation

Dans le jeu DEV :
- URLs HTTP : 5 762 (94.19% sont phishing).
- URLs HTTPS : 16 820.
- Légitimes HTTP : 335, dont 131 (39.1%) sont des faux positifs.

## 2. Ablation

| Configuration | Recall | FPR | ROC-AUC |
|---|---:|---:|---:|
| Avec schéma | 0.8478 | 0.0548 | 0.9593 |
| Sans schéma | 0.8365 | 0.0958 | 0.9436 |
| Schéma masqué | 0.8386 | 0.0916 | 0.9454 |

## 3. Analyse

Le schéma HTTP est un fort prédicteur de phishing (94.19% des HTTP sont phishing). Sa suppression dégrade les performances (FPR 0.0548 → 0.0958). Cependant, il crée des faux positifs sur les légitimes HTTP (39.1%).

## 4. Conclusion

Le schéma est un signal utile mais crée un biais HTTP. La solution n'est pas de supprimer le schéma (ce qui dégrade les performances) mais d'ajouter des features de réputation de domaine pour les URLs HTTP légitimes.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Analyse HTTP/HTTPS.*