import json
data = json.load(open("D:/openhands/projects/v2/phishing_ai_master/reports/tables/all_thresholds_extended.json"))
targets = [(0.05,0.95),(0.10,0.90),(0.15,0.85),(0.20,0.80),(0.05,0.90),(0.10,0.85),(0.15,0.80),(0.20,0.75),(0.05,0.80),(0.10,0.70)]
for low, high in targets:
    r = [x for x in data if x["low"]==low and x["high"]==high]
    if r:
        r = r[0]
        print("low=%.2f high=%.2f: Recall=%.4f FPR=%.4f F1=%.4f Prec=%.4f Spec=%.4f LEG=%d REV=%d PHI=%d review=%.2f%%" % (
            low, high, r["recall"], r["fpr"], r["f1"], r["precision"], r["specificity"],
            r["n_LEGITIMATE"], r["n_NEEDS_REVIEW"], r["n_PHISHING"], r["review_rate"]*100))