"""Phase 3 — Exploratory Data Analysis (EDA) for phishing URL detection.

Loads the HuggingFace urls.json dataset, computes descriptive statistics and
saves figures to reports/figures/eda/.
"""
import json, os, re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
FIG = os.path.join(ROOT, "reports", "figures", "eda")
os.makedirs(FIG, exist_ok=True)

# ---- Load ----
with open(os.path.join(ROOT, "data", "raw", "hf_phishing", "urls.json"), "r", encoding="utf-8") as f:
    data = json.load(f)
df = pd.DataFrame(data).rename(columns={"text": "url"})
df["label"] = df["label"].astype(int)
df["label_name"] = df["label"].map({0: "LEGITIMATE", 1: "PHISHING"})

def host_of(u):
    u = str(u)
    if "://" in u:
        h = u.split("://", 1)[1]
    else:
        h = u
    h = h.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    h = h.split(":", 1)[0]
    return h.lower()

def tld_of(u):
    h = host_of(u)
    parts = h.split(".")
    return parts[-1].lower() if len(parts) >= 2 and parts[-1].isalpha() and len(parts[-1]) <= 6 else "(none/ip)"

df["host"] = df["url"].map(host_of)
df["tld"] = df["url"].map(tld_of)
df["url_len"] = df["url"].str.len()
df["host_len"] = df["host"].str.len()
df["has_scheme"] = df["url"].str.contains("://", regex=False)
df["n_dots"] = df["url"].str.count(r"\.")
df["n_slash"] = df["url"].str.count("/")

# ---- Stats ----
print("shape", df.shape)
print("labels", df["label_name"].value_counts().to_dict())
print("unique urls", df["url"].nunique())
print("unique hosts", df["host"].nunique())
print("url_len describe:\n", df["url_len"].describe().to_string())
print("top tlds:\n", df["tld"].value_counts().head(15).to_string())

# ---- Fig 1: class distribution ----
fig, ax = plt.subplots(figsize=(6, 4))
df["label_name"].value_counts().plot(kind="bar", ax=ax, color=["#4caf50", "#f44336"])
ax.set_title("Figure 1 — Distribution des classes (URLs)")
ax.set_xlabel("Classe"); ax.set_ylabel("Nombre d'URLs")
ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
for p in ax.patches:
    ax.annotate(f"{int(p.get_height()):,}", (p.get_x()+p.get_width()/2, p.get_height()), ha="center", va="bottom", fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig01_class_distribution.png")); plt.close(fig)

# ---- Fig 2: URL length distribution ----
fig, ax = plt.subplots(figsize=(7, 4))
for name, g in df.groupby("label_name"):
    ax.hist(g["url_len"].clip(upper=200), bins=60, alpha=0.6, label=name, density=True)
ax.set_title("Figure 2 — Distribution de la longueur des URLs")
ax.set_xlabel("Longueur de l'URL (tronquée à 200)"); ax.set_ylabel("Densité")
ax.legend()
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig02_url_length.png")); plt.close(fig)

# ---- Fig 3: TLD distribution (top 15) ----
top_tlds = df["tld"].value_counts().head(15)
fig, ax = plt.subplots(figsize=(8, 5))
top_tlds.plot(kind="barh", ax=ax, color="#2196f3")
ax.invert_yaxis()
ax.set_title("Figure 3 — Top 15 TLD")
ax.set_xlabel("Nombre d'URLs"); ax.set_ylabel("TLD")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig03_tld_distribution.png")); plt.close(fig)

# ---- Fig 4: scheme distribution ----
scheme = df["has_scheme"].map({True: "avec schéma", False: "sans schéma"})
fig, ax = plt.subplots(figsize=(6, 4))
scheme.value_counts().plot(kind="pie", ax=ax, autopct="%1.1f%%")
ax.set_title("Figure 4 — Présence du schéma (http/https)")
ax.set_ylabel("")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig04_scheme_distribution.png")); plt.close(fig)

# ---- Save EDA summary ----
summary = {
    "n_rows": int(len(df)),
    "n_unique_urls": int(df["url"].nunique()),
    "n_unique_hosts": int(df["host"].nunique()),
    "labels": {k: int(v) for k, v in df["label_name"].value_counts().to_dict().items()},
    "url_len": {k: float(v) for k, v in df["url_len"].describe().to_dict().items()},
    "top_tlds": {k: int(v) for k, v in df["tld"].value_counts().head(15).to_dict().items()},
    "has_scheme_true": int(df["has_scheme"].sum()),
    "has_scheme_false": int((~df["has_scheme"]).sum()),
}
import json as _j
with open(os.path.join(ROOT, "reports", "tables", "eda_summary.json"), "w", encoding="utf-8") as f:
    _j.dump(summary, f, indent=2, ensure_ascii=False)
print("EDA done. Figures in", FIG)
print("Summary saved.")
