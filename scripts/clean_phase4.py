"""Phase 4 — Data cleaning, normalization, deduplication, manifest generation."""
import sys, os
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

import pandas as pd
from src.data.ingestion import load_hf_urls, load_tranco, load_phishtank_nontruncated
from src.data.validation import is_valid_url, normalize_url
from src.data.deduplication import exact_dedup, normalized_dedup
from src.data.provenance import build_manifest

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
OUT = os.path.join(ROOT, "data", "processed")
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(ROOT, "data", "interim"), exist_ok=True)

# ---- Load sources ----
hf = load_hf_urls()
# Stratified sample to keep memory/compute tractable on 8 GB RAM
hf = hf.groupby("label", group_keys=False).apply(lambda g: g.sample(n=min(len(g), 50000), random_state=42)).reset_index(drop=True)
print("HF sampled:", len(hf), hf["label"].value_counts().to_dict())

tranco = load_tranco(n=30000)
print("Tranco raw:", len(tranco))

pt = load_phishtank_nontruncated()
pt = pt.sample(n=min(len(pt), 30000), random_state=42).reset_index(drop=True)
print("PhishTank (non-truncated) sampled:", len(pt))

# ---- Combine ----
df = pd.concat([hf, tranco, pt], ignore_index=True)
print("Combined raw:", len(df), df["label"].value_counts().to_dict())

# ---- Validate ----
before = len(df)
df = df[df["url"].map(is_valid_url)].copy()
print("After validity filter:", len(df), "(dropped", before - len(df), ")")

# ---- Build manifest ----
manifest = build_manifest(df, dataset_version="v1")
print("Manifest shape:", manifest.shape)

# ---- Exact dedup ----
m1, n1 = exact_dedup(manifest, col="url")
print("Exact dedup dropped:", n1, "->", len(m1))

# ---- Normalized dedup ----
m2, n2 = normalized_dedup(m1, col="url")
print("Normalized dedup dropped:", n2, "->", len(m2))

# ---- Save ----
manifest_final = m2.reset_index(drop=True)
out_path = os.path.join(OUT, "manifest_v1.csv")
manifest_final.to_csv(out_path, index=False)
print("Saved:", out_path, manifest_final.shape)
print("Label counts:", manifest_final["label"].value_counts().to_dict())
print("Sources:", manifest_final["source"].value_counts().to_dict())

# ---- Leakage-ish checks: duplicates by registrable_domain across labels? ----
# Report cross-label domain overlap
dom_label = manifest_final.groupby("registrable_domain")["label"].nunique()
overlap = (dom_label > 1).sum()
print("Registrable domains appearing with BOTH labels:", overlap)
print("Total unique registrable domains:", manifest_final["registrable_domain"].nunique())

# Save dedup report
import json as _j
report = {
    "combined_raw": int(len(df) + n1 + n2),
    "after_validity": int(len(df)),
    "exact_dedup_dropped": int(n1),
    "normalized_dedup_dropped": int(n2),
    "final_rows": int(len(manifest_final)),
    "final_label_counts": {str(k): int(v) for k, v in manifest_final["label"].value_counts().to_dict().items()},
    "unique_registrable_domains": int(manifest_final["registrable_domain"].nunique()),
    "cross_label_domain_overlap": int(overlap),
}
with open(os.path.join(ROOT, "data", "interim", "dedup_report_v1.json"), "w", encoding="utf-8") as f:
    _j.dump(report, f, indent=2)
print("Dedup report saved.")
