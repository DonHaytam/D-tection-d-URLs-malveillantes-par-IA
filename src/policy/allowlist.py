"""Allow-list policy layer (separate from ML model)."""
import os
import sys
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")

TRanco_PATH = "D:/openhands/projects/v2/phishing_ai_master/data/raw/tranco_top1m.csv.zip"


class AllowList:
    def __init__(self, domains=None, tranco_path=None, top_n=100000):
        self.domains = set()
        if domains:
            self.domains.update(d.lower().strip() for d in domains)
        if tranco_path:
            import zipfile, pandas as pd
            with zipfile.ZipFile(tranco_path) as z:
                with z.open("top-1m.csv") as f:
                    df = pd.read_csv(f, header=None, names=["rank", "domain"])
            for d in df["domain"].head(top_n).astype(str):
                self.domains.add(d.lower().strip())

    def is_allowed(self, url):
        host = url.split("://")[-1].split("/")[0].split(":")[0].lower() if "://" in url else url.split("/")[0].split(":")[0].lower()
        # check exact host and registrable domain (last 2 labels)
        if host in self.domains:
            return True
        parts = host.split(".")
        if len(parts) >= 2:
            reg = ".".join(parts[-2:])
            if reg in self.domains:
                return True
        return False
