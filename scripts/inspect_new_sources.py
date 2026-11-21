import os
import pandas as pd

base = "D:/openhands/projects/SI project/data/raw"

for f in ["imanoop7_phishing_url_classification.csv", "shreyagopal_urldata.csv"]:
    p = os.path.join(base, f)
    df = pd.read_csv(p, low_memory=False)
    print("=" * 80)
    print("FILE:", f)
    print("Shape:", df.shape)
    print("Columns:", list(df.columns))
    print(df.head(5).to_string())
    print("Dtypes:")
    print(df.dtypes)
    print("Nulls:", df.isnull().sum().to_dict())
    if "label" in df.columns:
        print("label counts:", df["label"].value_counts().to_dict())
    elif "Target" in df.columns:
        print("Target counts:", df["Target"].value_counts().to_dict())
    elif "Result" in df.columns:
        print("Result counts:", df["Result"].value_counts().to_dict())
    print()
