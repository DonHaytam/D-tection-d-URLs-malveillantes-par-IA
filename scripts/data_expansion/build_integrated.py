"""Build domain-disjoint external TRAIN/DEV/TEST splits from the audited pool.

Rules:
- External splits are domain-disjoint from each other.
- External DEV/TEST domains are also disjoint from every project split
  (TRAIN/DEV/LOCKED_TEST/INDEPENDENT_FINAL_TEST) so they measure unseen-domain
  generalisation.
- External TRAIN may reuse project TRAIN domains (additional URLs), but exact
  normalized duplicates were already removed by the audit.
- No URL is fetched or reconstructed.
"""
import csv
import json
import os
import random
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")
sys.path.insert(0, "D:/openhands/projects/v2/vendor_libs")

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
INTEG = os.path.join(ROOT, "data", "integrated")
REPORT = os.path.join(ROOT, "reports", "data_expansion_public")

def load_csv(path):
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        return list(csv.DictReader(f))

def split_domains(name):
    rows = load_csv(os.path.join(ROOT, "data", "splits", f"{name}.csv"))
    doms = set()
    for r in rows:
        d = (r.get("registrable_domain") or "").strip().lower()
        if d:
            doms.add(d)
    return doms

project_domains = {s: split_domains(s) for s in ["TRAIN", "DEV", "LOCKED_TEST", "INDEPENDENT_FINAL_TEST"]}
eval_domains = project_domains["DEV"] | project_domains["LOCKED_TEST"] | project_domains["INDEPENDENT_FINAL_TEST"]
all_project_domains = eval_domains | project_domains["TRAIN"]

pool = load_csv(os.path.join(INTEG, "external_pool.csv"))
print(f"Pool rows: {len(pool)}")

# Group by registrable domain. Records with empty registrable_domain are quarantined.
valid = [r for r in pool if r.get("registrable_domain")]
empty_domain = len(pool) - len(valid)
by_domain = defaultdict(list)
for r in valid:
    by_domain[r["registrable_domain"]].append(r)

# Domains that may be used for external TRAIN: not in project eval splits.
train_candidate_domains = sorted(d for d in by_domain if d not in eval_domains)
# Domains for external DEV/TEST: not in any project split (truly unseen).
unseen_domains = sorted(d for d in by_domain if d not in all_project_domains)

rng = random.Random(42)
rng.shuffle(unseen_domains)
n = len(unseen_domains)
n_test = int(n * 0.5)
n_dev = int(n * 0.25)
test_domains = set(unseen_domains[:n_test])
dev_domains = set(unseen_domains[n_test:n_test + n_dev])
# External train uses all remaining candidate domains (including project TRAIN domains).
train_domains = set(train_candidate_domains) - test_domains - dev_domains

splits = {"EXTERNAL_TRAIN": [], "EXTERNAL_DEV": [], "EXTERNAL_TEST": []}
for d in train_domains:
    splits["EXTERNAL_TRAIN"].extend(by_domain[d])
for d in dev_domains:
    splits["EXTERNAL_DEV"].extend(by_domain[d])
for d in test_domains:
    splits["EXTERNAL_TEST"].extend(by_domain[d])

# Safety: enforce domain-disjointness.
def domains_of(rows):
    return {r["registrable_domain"] for r in rows}
assert not (domains_of(splits["EXTERNAL_TRAIN"]) & domains_of(splits["EXTERNAL_DEV"]))
assert not (domains_of(splits["EXTERNAL_TRAIN"]) & domains_of(splits["EXTERNAL_TEST"]))
assert not (domains_of(splits["EXTERNAL_DEV"]) & domains_of(splits["EXTERNAL_TEST"]))
assert not (domains_of(splits["EXTERNAL_DEV"]) & eval_domains)
assert not (domains_of(splits["EXTERNAL_TEST"]) & all_project_domains)

fields = list(pool[0].keys())
summary = {
    "pool_rows": len(pool),
    "empty_registrable_domain": empty_domain,
    "domains": {
        "train_candidates": len(train_candidate_domains),
        "unseen_for_dev_test": n,
        "external_train": len(train_domains),
        "external_dev": len(dev_domains),
        "external_test": len(test_domains),
    },
    "splits": {},
}
for name, rows in splits.items():
    labels = Counter(r["label"] for r in rows)
    auth = Counter((r["label"], r["is_auth_path"]) for r in rows)
    sources = Counter(r["source"] for r in rows)
    summary["splits"][name] = {
        "rows": len(rows),
        "labels": dict(labels),
        "sources": dict(sources),
        "auth_path": {f"label={k[0]},auth={k[1]}": v for k, v in sorted(auth.items())},
        "unique_domains": len(domains_of(rows)),
    }
    out = os.path.join(INTEG, f"{name.lower()}.csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})
    print(f"{name}: {len(rows)} rows, {len(domains_of(rows))} domains -> {out}")

with open(os.path.join(INTEG, "external_splits.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
