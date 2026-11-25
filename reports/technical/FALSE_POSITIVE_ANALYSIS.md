# FALSE POSITIVE ANALYSIS — Phishing AI Master 2 (Phase C)

## 1. Résumé

597 faux positifs sur DEV (M1, seuil 0.5). FPR = 0.0548.

## 2. Caractéristiques distinctives des faux positifs

| Feature | Moyenne FP | Moyenne légitimes | Différence |
|---|---:|---:|---:|
| url_length | 33.91 | 39.60 | -5.69 |
| host_length | 15.99 | 14.10 | +1.89 |
| path_length | 9.62 | 16.96 | -7.33 |
| n_subdomains | 0.53 | 0.26 | +0.28 |
| suspicious_token_count | 0.089 | 0.035 | +0.054 |
| scheme_http | 0.219 | 0.031 | +0.188 |
| has_query | 0.028 | 0.063 | -0.035 |

## 3. Causes identifiées

1. **Raccourci lexical (brand tokens)** : les FPs contiennent 2.5× plus de tokens suspects (login, bank, amazon, paypal). Le modèle associe ces tokens à la classe phishing sans vérifier si le domaine est officiel.
2. **Biais HTTP** : 21.9 % des FPs sont en HTTP vs 3.1 % des légitimes. Le schéma HTTP est sur-pondéré comme signal de phishing.
3. **URLs courtes** : les FPs sont plus courtes (33.9 vs 39.6) avec des chemins plus courts (9.6 vs 17.0). Le modèle sur-réagit aux URLs courtes.
4. **Sous-domaines** : les FPs ont plus de sous-domaines (0.53 vs 0.26), souvent des sous-domaines de marques sur des domaines génériques.
5. **TLD sous-représentés** : .cn (FPR 0.549), .ar (FPR 0.417) ont des FPR très élevés.

## 4. Exemples de faux positifs (scores les plus élevés)

| Score | URL | Cause probable |
|---|---:|---|
| 0.998 | http://dapeco.com.om | TLD .om sous-représenté |
| 0.996 | http://thd.org.tr | TLD .tr sous-représenté |
| 0.988 | https://paypal.me | Token "paypal" |
| 0.963 | https://www.sunpass.com/.../accountLogin.do | Tokens "account", "login" |
| 0.963 | http://www.bankofbeirut.com/... | Token "bank" |
| 0.951 | https://www.amazon.cn/ | Token "amazon" + TLD .cn |

## 5. Impact de la couche allow-list (policy layer)

| Configuration | Recall | FPR | Precision |
|---|---:|---:|---:|
| Modèle brut (seuil 0.5) | 0.8478 | 0.0548 | 0.9432 |
| + Allow-list (seuil 0.5) | 0.7951 | 0.0207 | 0.9764 |
| + Allow-list (seuil 0.4937) | 0.7970 | 0.0213 | 0.9757 |

L'allow-list réduit le FPR de 0.0548 à 0.0207 (2.6×) mais au prix d'une baisse de recall (0.8478 → 0.7951). L'allow-list est trop agressive (35.5 % des URLs DEV sont sur des domaines Tranco).

## 6. Recommandations

1. **Amélioration des features** : ajouter des features de position des tokens de marque (déjà testé en M7, mais la représentation char TF-IDF reste supérieure).
2. **Hard-negative mining** : ajouter des légitimes avec tokens de marque à l'entraînement.
3. **Calibration** : isotonic améliore ECE (0.0000) et Brier (0.0761).
4. **Allow-list restrictive** : limiter l'allow-list aux domaines les plus populaires (top 10k Tranco) pour réduire les faux négatifs.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Phase C (Analyse des faux positifs).*
