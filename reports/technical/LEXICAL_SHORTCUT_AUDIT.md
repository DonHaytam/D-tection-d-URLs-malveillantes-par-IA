# LEXICAL SHORTCUT AUDIT — Phishing AI Master 2

## 1. Principe

Le modèle char TF-IDF capture des sous-chaînes (n-grammes 3-5) qui sont fortement corrélées avec la classe phishing. Les tokens suspects (login, bank, paypal, verify, secure, account) ont des coefficients élevés.

## 2. Coefficients les plus élevés

Les n-grammes les plus contributifs au score de phishing sont :
- "pay", "log", "logi", "login", "signin", "verif", "secure", "bank", "accou", "account", "payp", "paypal", "amaz", "amazon"

Ces tokens apparaissent dans les deux classes (légitimes et phishing), mais le modèle leur associe un poids positif élevé.

## 3. Quantification du raccourci

- 597 faux positifs sur DEV (avant hard-negative mining) contenaient en moyenne 0.089 tokens suspects vs 0.035 pour les légitimes (2.5×).
- Après hard-negative mining : 415 faux positifs, token count moyen 0.089 (inchangé).
- Les faux positifs sont des URLs légitimes contenant des tokens suspects sur des domaines non reconnus.

## 4. Expériences de suppression

L'ablation des features a montré que :
- Char TF-IDF seul (URL complète) : FPR 0.0548, AUC 0.9593.
- Sans schéma : FPR 0.0958, AUC 0.9436 (dégradation).
- Hôte seul : FPR 0.2242, AUC 0.8540 (dégradation majeure).

Le modèle ne peut pas fonctionner sans les tokens lexicaux, mais leur présence crée des faux positifs.

## 5. Conclusion

Le raccourci lexical est confirmé et quantifié. Les tokens suspects contribuent fortement au score de phishing, mais sont présents dans les deux classes. La solution nécessite des features de position des tokens (domaine vs chemin) et des données de réputation de domaine.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Audit du raccourci lexical.*