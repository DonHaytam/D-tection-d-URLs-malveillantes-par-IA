# Bias Reduction Report — Phishing AI Master 2

## Before optimization

| Metric | Value |
|---|---:|
| P(Phishing \| login) | 0.9766 |
| Legitimate auth URLs | 0.32% |
| Phishing auth URLs | 4.78% |

## After hard-negative mining (597 FPs)

| Metric | Value |
|---|---:|
| FPR | 0.0381 (was 0.0548) |
| Recall | 0.8422 (was 0.8478) |

## After constructed hard negatives (5k Tranco)

| Metric | Value |
|---|---:|
| FPR | 0.0584 (worse) |
| Recall | 0.8457 |
| Auth FP (paypal.com/signin) | 78.85% (was 96.18%) |

## Conclusion

Hard-negative mining from real FPs reduced FPR by 30%. Constructed hard negatives improved diagnostic URLs but degraded overall metrics. The root cause (dataset bias) requires real legitimate auth URLs.

---
*Documentation générée par le pipeline du projet `phishing_ai_master`.*