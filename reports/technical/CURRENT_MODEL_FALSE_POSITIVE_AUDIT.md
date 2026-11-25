# CURRENT MODEL FALSE POSITIVE AUDIT — Phishing AI Master 2

## 1. Current architecture

- Model: Logistic Regression (char TF-IDF 3-5, min_df=3, max_features=20000)
- Class weights: balanced
- Solver: saga, max_iter=2000
- Thresholds: 0.25 / 0.75 (after optimization)
- Hard-negative mining: 597 legitimate FPs added to training

## 2. Current features

- Char TF-IDF: 20 000 features (n-grammes 3-5)
- Lexical: 18 features
- Structural: 18 features
- Enhanced: 5 brand position + 1 Tranco rank (tested, not used in final model)

## 3. Data distribution

- TRAIN: 114 873 (58 221 legit / 56 652 phishing)
- DEV: 22 586 (10 885 legit / 11 701 phishing)
- 96 155 domaines registrables uniques
- 591 domaines cross-label supprimés

## 4. Suspected lexical shortcuts

1. **Tokens de marque** (paypal, amazon, bank, login, verify, secure, account) → coefficient élevé dans le modèle.
2. **Schéma HTTP** → 94.19% des URL HTTP dans DEV sont phishing → HTTP est un fort prédicteur.
3. **URLs courtes** → les phishing sont souvent des URLs courtes avec tokens suspects.

## 5. Top features (coefficients)

Les n-grammes de caractères les plus contributifs sont : "pay", "login", "verify", "bank", "secure", "account". Ces tokens apparaissent à la fois dans les phishing et les légitimes (faux positifs).

## 6. Exemples de faux positifs

| URL | Score | Cause |
|---|---:|---|
| https://www.paypal.com/signin | 0.96 | Token "paypal" + "signin" |
| https://www.dropbox.com/login | 0.89 | Token "login" |
| https://github.com/login | 0.69 | Token "login" |
| https://accounts.google.com/signin | 0.53 | Token "signin" |
| https://www.amazon.com/ap/signin | 0.68 | Token "amazon" + "signin" |

## 7. Exemples de vrais positifs

| URL | Score |
|---|---:|
| paypal-login-example.com/signin | 0.9984 |
| amazon-account-example.net/verify | 0.9958 |
| secure-login-example.com/account | 0.9965 |

## 8. Hypothèses

1. Le modèle ne distingue pas les domaines officiels des imitations (pas de données de réputation).
2. Le schéma HTTP est un fort prédicteur mais crée des faux positifs sur les légitimes HTTP.
3. Les tokens suspects sont présents dans les deux classes (légitimes et phishing).
4. Les données PhishTank datent de 2015 (concept drift).

## 9. HTTP/HTTPS ablation

| Configuration | Recall | FPR | AUC |
|---|---:|---:|---:|
| Avec schéma | 0.8478 | 0.0548 | 0.9593 |
| Sans schéma | 0.8365 | 0.0958 | 0.9436 |
| Schéma masqué | 0.8386 | 0.0916 | 0.9454 |

Le schéma est un signal utile mais crée un biais HTTP (39.1% des légitimes HTTP sont des faux positifs).

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Audit des faux positifs.*