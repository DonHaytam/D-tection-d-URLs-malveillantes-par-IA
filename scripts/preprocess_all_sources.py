import os
import pandas as pd
from sklearn.model_selection import train_test_split

BASE = "D:/openhands/projects/SI project"
RAW = os.path.join(BASE, "data", "raw")
PROC = os.path.join(BASE, "data", "processed")
os.makedirs(PROC, exist_ok=True)

# ---------- Source 1: PhiUSIIL (UCI) ----------
phi = pd.read_csv(os.path.join(RAW, "PhiUSIIL_Phishing_URL_Dataset.csv"), low_memory=False)
phi_p = pd.DataFrame({
    "url": phi["URL"].astype(str).str.strip(),
    "label": phi["label"].astype(int),
    "source": "PhiUSIIL_UCI",
})
phi_p = phi_p[phi_p["url"].str.len() > 0]
phi_p.to_csv(os.path.join(PROC, "phiUSIIL_processed.csv"), index=False)

# ---------- Source 2: imanoop7 (HuggingFace) ----------
hf = pd.read_csv(os.path.join(RAW, "imanoop7_phishing_url_classification.csv"), low_memory=False)
hf_p = pd.DataFrame({
    "url": hf["text"].astype(str).str.strip(),
    "label": hf["label"].astype(int),
    "source": "imanoop7_HF",
})
hf_p = hf_p[hf_p["url"].str.len() > 0]
hf_p.to_csv(os.path.join(PROC, "imanoop7_processed.csv"), index=False)

# ---------- Source 3: shreyagopal (GitHub) ----------
sh = pd.read_csv(os.path.join(RAW, "shreyagopal_urldata.csv"), low_memory=False)
sh_p = pd.DataFrame({
    "url": sh["Domain"].astype(str).str.strip(),
    "label": sh["Label"].astype(int),
    "source": "shreyagopal_GitHub",
})
sh_p = sh_p[sh_p["url"].str.len() > 0]
sh_features = sh.drop(columns=["Domain", "Label"]).copy()
sh_features.to_csv(os.path.join(PROC, "shreyagopal_features.csv"), index=False)
sh_p.to_csv(os.path.join(PROC, "shreyagopal_processed.csv"), index=False)

# ---------- Unified URL dataset ----------
unified = pd.concat([phi_p, hf_p, sh_p], ignore_index=True)
before = len(unified)
unified = unified.drop_duplicates(subset=["url"]).reset_index(drop=True)
after = len(unified)

unified.to_csv(os.path.join(PROC, "unified_urls.csv"), index=False)

# Stratified split by label+source to keep both balanced
strat_key = unified["label"].astype(str) + "_" + unified["source"].astype(str)
X_train, X_test, y_train, y_test = train_test_split(
    unified[["url", "source"]],
    unified["label"],
    test_size=0.2,
    random_state=42,
    stratify=strat_key,
)
train_df = pd.concat([X_train.reset_index(drop=True), y_train.reset_index(drop=True)], axis=1)
test_df = pd.concat([X_test.reset_index(drop=True), y_test.reset_index(drop=True)], axis=1)
train_df.to_csv(os.path.join(PROC, "unified_train.csv"), index=False)
test_df.to_csv(os.path.join(PROC, "unified_test.csv"), index=False)

# Report
report = []
report.append("=== Multi-Source Data Preprocessing Report ===")
report.append(f"PhiUSIIL: {len(phi_p)} rows (label: {phi_p['label'].value_counts().to_dict()})")
report.append(f"imanoop7: {len(hf_p)} rows (label: {hf_p['label'].value_counts().to_dict()})")
report.append(f"shreyagopal: {len(sh_p)} rows (label: {sh_p['label'].value_counts().to_dict()})")
report.append(f"Unified before dedup: {before} rows")
report.append(f"Unified after dedup: {after} rows")
report.append(f"Unified label counts: {unified['label'].value_counts().to_dict()}")
report.append(f"Unified source counts: {unified['source'].value_counts().to_dict()}")
report.append(f"Train: {len(train_df)} rows {train_df['label'].value_counts().to_dict()}")
report.append(f"Test: {len(test_df)} rows {test_df['label'].value_counts().to_dict()}")
report_text = "\n".join(report)
with open(os.path.join(BASE, "scripts", "preprocess_multisource_report.txt"), "w", encoding="utf-8") as f:
    f.write(report_text)

print(report_text)
