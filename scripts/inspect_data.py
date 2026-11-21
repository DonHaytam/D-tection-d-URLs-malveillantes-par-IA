import os
import pandas as pd

BASE = "D:/openhands/projects/SI project"
CSV = os.path.join(BASE, "data", "raw", "PhiUSIIL_Phishing_URL_Dataset.csv")

df = pd.read_csv(CSV, low_memory=False)
print("Shape:", df.shape)
print("Columns:", list(df.columns))
with open(os.path.join(BASE, "scripts", "inspect_out.txt"), "w", encoding="utf-8") as f:
    f.write(f"Shape: {df.shape}\n")
    f.write(f"Columns: {list(df.columns)}\n")
    f.write(str(df.head(10)) + "\n")
    f.write(str(df.dtypes) + "\n")
    f.write("Class distribution:\n")
    f.write(str(df["label"].value_counts()) + "\n")
    f.write(str(df["label"].value_counts(normalize=True)) + "\n")
    f.write("Null counts:\n")
    f.write(str(df.isnull().sum().to_string()) + "\n")
print("OK - see scripts/inspect_out.txt")
