"""Audit the manually downloaded external URL datasets.

Passive only: no URL is fetched, resolved, rendered or executed.
Builds a validated external pool plus a quarantine file, with provenance,
label mapping, duplicate/conflict detection and domain-overlap checks.
"""
import csv
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

from src.data.validation import is_valid_url, normalize_url, extract_components
from src.data.provenance import registrable_domain, tld_of

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
OUT_DATA = os.path.join(ROOT, "data", "integrated")
OUT_QUAR = os.path.join(ROOT, "data", "quarantine")
OUT_REPORT = os.path.join(ROOT, "reports", "data_expansion_public")
os.makedirs(OUT_DATA, exist_ok=True)
os.makedirs(OUT_QUAR, exist_ok=True)
os.makedirs(OUT_REPORT, exist_ok=True)

AUTH_RE = re.compile(
    r"(?:^|/)(login|signin|sign-in|sign_in|auth|account|accounts|verify|verification|"
    r"password|oauth|register|signup|sign-up|security|checkout|payment|billing|"
    r"wp-login\.php|login\.php|signin\.php)(?:/|$|[.?])",
    re.I,
)

def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def load_split(name):
    path = os.path.join(ROOT, "data", "splits", f"{name}.csv")
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows

def norm_for_compare(u):
    return normalize_url(u) or ""

def auth_path(url):
    try:
        p = url.split("://", 1)[1]
        path = p.split("/", 1)[1] if "/" in p else ""
        return bool(AUTH_RE.search("/" + path.split("?")[0]))
    except Exception:
        return False

def url_sha(u):
    return hashlib.sha256(u.encode("utf-8")).hexdigest()

# ---------------------------------------------------------------- project splits
split_rows = {s: load_split(s) for s in ["TRAIN", "DEV", "LOCKED_TEST", "INDEPENDENT_FINAL_TEST"]}
project_norm = defaultdict(dict)  # normalized url -> {split: label}
project_domains = defaultdict(set)
for split, rows in split_rows.items():
    for r in rows:
        u = norm_for_compare(r.get("url", ""))
        if u:
            project_norm[u][split] = int(float(r.get("label", 0)))
        rd = (r.get("registrable_domain") or "").strip().lower()
        if not rd:
            rd = registrable_domain(extract_components(u)["host"])
        if rd:
            project_domains[split].add(rd)

# ---------------------------------------------------------------- source specs
SOURCES = [
    {
        "source": "url_dataset_450k",
        "path": os.path.join(ROOT, "data", "Phishing URL dataset", "Phishing URL dataset", "URL dataset.csv"),
        "url_col": "url",
        "label_col": "type",
        "label_map": {"legitimate": 0, "phishing": 1},
        "collection_date": "unknown (Mendeley Phishing URL Dataset 450K; no per-record date)",
        "license": "CC BY 4.0 (per Mendeley landing page; verify before redistribution)",
    },
    {
        "source": "phishing_urls_54k",
        "path": os.path.join(ROOT, "data", "Phishing URL dataset", "Phishing URL dataset", "Phishing URLs.csv"),
        "url_col": "url",
        "label_col": "Type",
        "label_map": {"phishing": 1, "legitimate": 0},
        "collection_date": "unknown (Mendeley Phishing URL Dataset; no per-record date)",
        "license": "CC BY 4.0 (per Mendeley landing page; verify before redistribution)",
    },
    {
        "source": "legitphish_v2",
        "path": os.path.join(ROOT, "data", "LegitPhish Dataset", "LegitPhish Dataset", "url_features_extracted1.csv"),
        "url_col": "URL",
        "label_col": "ClassLabel",
        "label_map": {"1": 0, "1.0": 0, "0": 1, "0.0": 1},  # 1=legitimate, 0=phishing
        "collection_date": "unknown (LegitPhish V2; no per-record date)",
        "license": "CC BY 4.0 (per Mendeley landing page; verify before redistribution)",
    },
]

# feature-only source is documented but excluded from the URL pipeline
EXCLUDED_FEATURE_ONLY = {
    "source": "phishing_detection_247k",
    "path": os.path.join(ROOT, "data", "Phishing Detection Dataset", "Phishing Detection Dataset", "Dataset.csv"),
    "reason": "Feature-only CSV (no URL column); cannot enter the raw-URL pipeline and must not be reconstructed.",
}

pool = []
quarantine = []
source_stats = {}

for spec in SOURCES:
    path = spec["path"]
    stats = {
        "source": spec["source"],
        "path": path,
        "exists": os.path.exists(path),
        "bytes": os.path.getsize(path) if os.path.exists(path) else 0,
        "sha256": sha256_file(path) if os.path.exists(path) else None,
        "collection_date": spec["collection_date"],
        "license": spec["license"],
        "rows_raw": 0,
        "invalid_url": 0,
        "unknown_label": 0,
        "label_counts": Counter(),
        "auth_path": Counter(),
        "project_url_overlap": 0,
        "project_domain_overlap": Counter(),
    }
    if not stats["exists"]:
        source_stats[spec["source"]] = stats
        continue
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stats["rows_raw"] += 1
            raw = (row.get(spec["url_col"]) or "").strip()
            raw_label = (row.get(spec["label_col"]) or "").strip()
            if not is_valid_url(raw):
                stats["invalid_url"] += 1
                quarantine.append({
                    "source": spec["source"], "original_url": raw, "original_label": raw_label,
                    "normalized_url": "", "label": "", "reason": "invalid_url",
                })
                continue
            label = spec["label_map"].get(raw_label.lower())
            if label is None:
                stats["unknown_label"] += 1
                quarantine.append({
                    "source": spec["source"], "original_url": raw, "original_label": raw_label,
                    "normalized_url": normalize_url(raw) or "", "label": "", "reason": "unknown_label",
                })
                continue
            norm = normalize_url(raw)
            try:
                comp = extract_components(norm)
            except Exception as exc:
                stats["invalid_url"] += 1
                quarantine.append({
                    "source": spec["source"], "original_url": raw, "original_label": raw_label,
                    "normalized_url": norm or "", "label": "", "reason": f"unparseable_url:{type(exc).__name__}",
                })
                continue
            host = comp["host"]
            rd = registrable_domain(host)
            rec = {
                "url": norm,
                "original_url": raw,
                "label": label,
                "original_label": raw_label,
                "source": spec["source"],
                "collection_date": spec["collection_date"],
                "license": spec["license"],
                "domain": host,
                "registrable_domain": rd,
                "tld": tld_of(host),
                "scheme": comp["scheme"],
                "path": comp["path"],
                "query": comp["query"],
                "fragment": comp["fragment"],
                "is_auth_path": int(auth_path(norm)),
                "url_sha256": url_sha(norm),
            }
            stats["label_counts"][str(label)] += 1
            stats["auth_path"][str(label)] += int(rec["is_auth_path"])
            if norm in project_norm:
                stats["project_url_overlap"] += 1
                p_labels = set(project_norm[norm].values())
                if p_labels != {label}:
                    quarantine.append({**rec, "reason": "label_conflict_with_project_split"})
                    continue
                # same label already present in project: do not duplicate into external pool
                continue
            if rd in project_domains["DEV"] or rd in project_domains["LOCKED_TEST"] or rd in project_domains["INDEPENDENT_FINAL_TEST"]:
                stats["project_domain_overlap"]["DEV/LOCKED/INDEPENDENT"] += 1
                quarantine.append({**rec, "reason": "domain_overlap_with_eval_split"})
                continue
            pool.append(rec)
    source_stats[spec["source"]] = stats

# ---------------------------------------------------------------- cross-source conflicts
by_norm = defaultdict(list)
for rec in pool:
    by_norm[rec["url"]].append(rec)
conflict_norms = {u for u, recs in by_norm.items() if len({r["label"] for r in recs}) > 1}
if conflict_norms:
    kept = []
    for rec in pool:
        if rec["url"] in conflict_norms:
            quarantine.append({**rec, "reason": "cross_source_label_conflict"})
        else:
            kept.append(rec)
    pool = kept

# deduplicate same-label duplicates across sources, keep first by source order
seen = set()
deduped = []
for rec in pool:
    if rec["url"] in seen:
        quarantine.append({**rec, "reason": "duplicate_normalized_url"})
        continue
    seen.add(rec["url"])
    deduped.append(rec)
pool = deduped

# ---------------------------------------------------------------- stats
pool_labels = Counter(str(r["label"]) for r in pool)
pool_auth = Counter((str(r["label"]), r["is_auth_path"]) for r in pool)
pool_domains = len({r["registrable_domain"] for r in pool if r["registrable_domain"]})
quar_reasons = Counter(r["reason"] for r in quarantine)

audit = {
    "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
    "passive_only": True,
    "project_splits": {
        s: {
            "rows": len(split_rows[s]),
            "unique_normalized_urls": len({norm_for_compare(r.get("url", "")) for r in split_rows[s] if r.get("url")}),
            "unique_registrable_domains": len(project_domains[s]),
        } for s in split_rows
    },
    "sources": source_stats,
    "excluded_feature_only": EXCLUDED_FEATURE_ONLY,
    "pool": {
        "rows": len(pool),
        "label_counts": dict(pool_labels),
        "unique_registrable_domains": pool_domains,
        "auth_path_counts": {f"label={k[0]},auth={k[1]}": v for k, v in sorted(pool_auth.items())},
        "sources": dict(Counter(r["source"] for r in pool)),
    },
    "quarantine": {
        "rows": len(quarantine),
        "reasons": dict(quar_reasons),
    },
}

with open(os.path.join(OUT_DATA, "external_audit.json"), "w", encoding="utf-8") as f:
    json.dump(audit, f, indent=2, default=str)

pool_fields = ["url", "original_url", "label", "original_label", "source", "collection_date", "license",
               "domain", "registrable_domain", "tld", "scheme", "path", "query", "fragment",
               "is_auth_path", "url_sha256"]
with open(os.path.join(OUT_DATA, "external_pool.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=pool_fields)
    w.writeheader()
    for rec in pool:
        w.writerow({k: rec[k] for k in pool_fields})

quar_fields = pool_fields + ["reason"]
with open(os.path.join(OUT_QUAR, "external_quarantine.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=quar_fields, extrasaction="ignore")
    w.writeheader()
    for rec in quarantine:
        w.writerow({k: rec.get(k, "") for k in quar_fields})

print("=== EXTERNAL AUDIT ===")
for s, st in source_stats.items():
    print(f"{s}: raw={st['rows_raw']} invalid={st['invalid_url']} unknown_label={st['unknown_label']} "
          f"labels={dict(st['label_counts'])} auth={dict(st['auth_path'])} "
          f"project_url_overlap={st['project_url_overlap']} domain_overlap={dict(st['project_domain_overlap'])}")
print(f"Pool rows: {len(pool)} labels={dict(pool_labels)} domains={pool_domains}")
print(f"Auth path counts: {dict(pool_auth)}")
print(f"Quarantine rows: {len(quarantine)} reasons={dict(quar_reasons)}")
print(f"Saved: {OUT_DATA}/external_pool.csv")
print(f"Saved: {OUT_DATA}/external_audit.json")
print(f"Saved: {OUT_QUAR}/external_quarantine.csv")
