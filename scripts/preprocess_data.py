import os
import pandas as pd
from sklearn.model_selection import train_test_split

BASE = "D:/openhands/projects/SI project"
RAW = os.path.join(BASE, "data", "raw", "PhiUSIIL_Phishing_URL_Dataset.csv")
PROCESSED = os.path.join(BASE, "data", "processed", "PhiUSIIL_phishing_url_processed.csv")
TRAIN = os.path.join(BASE, "data", "processed", "train.csv")
TEST = os.path.join(BASE, "data", "processed", "test.csv")

REPORT = os.path.join(BASE, "scripts", "preprocess_report.txt")

DROP_COLUMNS = ["FILENAME", "Title", "Domain", "TLD"]

df = pd.read_csv(RAW, low_memory=False)

data = df.drop(columns=[c for c in DROP_COLUMNS if c in df.columns]).copy()
data["URL"] = data["URL"].astype(str).str.strip()
data = data[data["URL"].str.len() > 0].copy()
data["label"] = data["label"].astype(int)
data = data[data["label"].isin([0, 1])].copy()

feature_cols = [c for c in data.columns if c not in ("URL", "label")]
for c in feature_cols:
    data[c] = pd.to_numeric(data[c], errors="coerce")

X = data[["URL"] + feature_cols]
y = data["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

train_df = pd.concat([X_train.reset_index(drop=True), y_train.reset_index(drop=True)], axis=1)
test_df = pd.concat([X_test.reset_index(drop=True), y_test.reset_index(drop=True)], axis=1)

train_df.to_csv(TRAIN, index=False)
test_df.to_csv(TEST, index=False)
data.to_csv(PROCESSED, index=False)

with open(REPORT, "w", encoding="utf-8") as f:
    f.write(f"Raw shape: {df.shape}\n")
    f.write(f"After cleaning: {data.shape}\n")
    f.write(f"Features: {feature_cols}\n")
    f.write("Label distribution:\n")
    f.write(str(data["label"].value_counts().to_string()) + "\n")
    f.write(f"Train shape: {train_df.shape}\n")
    f.write(f"Test shape: {test_df.shape}\n")

print("PROCESSED SHAPE:", data.shape)
print("TRAIN SHAPE:", train_df.shape)
print("TEST SHAPE:", test_df.shape)
