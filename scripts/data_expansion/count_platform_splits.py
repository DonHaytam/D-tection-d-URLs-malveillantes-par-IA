import sys
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master/scripts/data_expansion")

import pandas as pd
from count_platform import p

R = "D:/openhands/projects/v2/phishing_ai_master"
for name, path in [("TRAIN", "data/splits/TRAIN.csv"),
                   ("EXT_TRAIN", "data/integrated/external_train.csv"),
                   ("EXT_TEST", "data/integrated/external_test.csv")]:
    df = pd.read_csv(f"{R}/{path}", usecols=["url", "label"])
    df["platform"] = df["url"].map(p)
    print(name)
    print(pd.crosstab(df.platform, df.label).to_string())
