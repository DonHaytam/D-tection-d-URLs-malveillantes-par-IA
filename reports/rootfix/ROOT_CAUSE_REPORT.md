# ROOT CAUSE REPORT — Phishing AI Master 2

## 1. Why did paypal.com/signin receive 96.18%?

Because the token "paypal" and "signin" are strongly correlated with phishing in the training data:
- P(phishing | "login") = 0.9766 in TRAIN.
- P(phishing | "paypal") = 0.9939 in TRAIN.
- "login" appears in 0.15% of legitimate URLs vs 6.64% of phishing URLs.
- The model learned: "login" → phishing, "paypal" → phishing.

## 2. Why did dropbox.com/login receive 89.39%?

Same reason: "login" and "dropbox" are phishing-correlated tokens in TRAIN.
- P(phishing | "dropbox") = 0.9950.
- "login" appears in 0.15% of legitimate URLs.

## 3. Is login/signin/account/verify disproportionately associated with phishing in TRAIN?

YES. Confirmed quantitatively:
- login: 0.15% (legit) vs 6.64% (phishing) → ratio 44×.
- signin: 0.03% vs 0.59% → ratio 20×.
- account: 0.14% vs 1.83% → ratio 13×.
- verify: 0.01% vs 0.59% → ratio 59×.
- secure: 0.07% vs 1.87% → ratio 27×.

## 4. What percentage of legitimate TRAIN URLs are authentication URLs?

Only **0.32%** (184 out of 58 221). The legitimate class is 43.83% homepages and 54.84% "other".

## 5. What percentage of phishing TRAIN URLs contain authentication keywords?

- login: 6.64%
- account: 1.83%
- secure: 1.87%
- verify: 0.59%
- auth: 1.26%

## 6. Was there domain leakage?

No. Split by registrable domain. 591 cross-label domains removed from training.

## 7. Was there duplicate/near-duplicate leakage?

No. Exact dedup: 276 removed. Normalized dedup: 0 additional.

## 8. Did the legitimate class contain enough hard negatives?

No. Only 0.32% authentication URLs in the legitimate class. This is the ROOT CAUSE.

## 9. Which representation fixed the problem?

None of the tested representations fully fixed the problem:
- Char TF-IDF (baseline): FPR 0.0548.
- Hard-negative mining (597 FPs): FPR 0.0381 (-30%).
- Char TF-IDF + keyword position + brand impersonation: FPR 0.0910 (worse).
- Constructed hard negatives (Tranco): FPR 0.0584 (worse on DEV, but better on diagnostic URLs).
- Ensemble (soft voting): FPR 0.0353, Recall 0.8698.

## 10. Which model is now best?

M1_LR_HARDNEG (Logistic Regression, char TF-IDF, hard-negative mining from real FPs):
- Recall: 0.8422, FPR: 0.0381, ROC-AUC: 0.9610, ECE: 0.0370.

## 11. Does it satisfy Recall >= 0.85 and FPR <= 0.01?

**NO.** Recall 0.8422 < 0.85, FPR 0.0381 > 0.01.

## 12. Does it satisfy Authentication FPR <= 0.01?

No. Authentication URLs still have elevated FPR.

## 13. Does it generalize to unseen domains?

Partially. The model generalizes to unseen domains but still relies on lexical shortcuts for authentication vocabulary.

## Root cause

The dataset itself teaches "login = phishing" because legitimate URLs almost never contain authentication keywords (0.15% login) while phishing URLs frequently do (6.64% login). This is a **dataset construction bias**, not a model bug.

## Solution

The fix requires:
1. Collecting real legitimate authentication URLs from diverse sources.
2. Adding them to the training set (domain-disjoint).
3. Retraining the model.

Without real legitimate authentication data, no model can learn that authentication vocabulary appears on legitimate sites.

---
*Documentation générée par le pipeline du projet `phishing_ai_master` — Root cause report.*