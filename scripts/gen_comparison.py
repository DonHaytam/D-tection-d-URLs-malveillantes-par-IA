"""Regenerate reports/MODEL_COMPARISON.md from experiment JSONs."""
import sys, os, json
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
exp_dir = os.path.join(ROOT, "experiments/results")
rows = []
for fn in sorted(os.listdir(exp_dir)):
    if not fn.endswith(".json"):
        continue
    e = json.load(open(os.path.join(exp_dir, fn)))
    m = e["metrics_dev"]
    rows.append({
        "Model": e["model_name"],
        "Accuracy": f"{m['accuracy']:.4f}",
        "Precision": f"{m['precision']:.4f}",
        "Recall": f"{m['recall']:.4f}",
        "FPR": f"{m['fpr']:.4f}",
        "F1": f"{m['f1']:.4f}",
        "ROC-AUC": f"{m['roc_auc']:.4f}",
        "PR-AUC": f"{m['pr_auc']:.4f}",
        "Brier": f"{m['brier']:.4f}",
        "ECE": f"{m['ece']:.4f}",
        "Latency (ms)": f"{e.get('inference_latency_ms_per_url', 0):.3f}",
    })

name_map = {
    "M1_LR": "Logistic Regression",
    "M2_SVM": "Linear SVM",
    "M3_RF": "Random Forest",
    "M4_GB": "Gradient Boosting",
    "M5_XGBOOST": "XGBoost",
    "M6_HYBRID": "Hybrid",
}

lines = ["# MODEL COMPARISON — Phishing URL detection (Phase 9)\n",
         "Résultats sur DEV (jeu de validation). Toutes les valeurs proviennent des artefacts d'expérience.\n",
         "| Model | Accuracy | Precision | Recall | FPR | F1 | ROC-AUC | PR-AUC | Brier | ECE | Latency (ms) |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    lines.append(f"| {name_map.get(r['Model'], r['Model'])} | {r['Accuracy']} | {r['Precision']} | {r['Recall']} | {r['FPR']} | {r['F1']} | {r['ROC-AUC']} | {r['PR-AUC']} | {r['Brier']} | {r['ECE']} | {r['Latency (ms)']} |")

lines.append("\n---\n*Documentation générée par le pipeline du projet `phishing_ai_master` — Phase 9 (Comparaison des modèles).*\n")

out = os.path.join(ROOT, "reports/MODEL_COMPARISON.md")
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("Written", out)
print("\n".join(lines))
