"""Inspect and integrate newly downloaded datasets."""
import sys, os, csv, json
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")

ROOT = "D:/openhands/projects/v2/phishing_ai_master"

# 1. Phishing URL dataset (URL dataset.csv) - 450,176 raw URLs
print("=== Phishing URL dataset (URL dataset.csv) ===")
path1 = os.path.join(ROOT, "data/Phishing URL dataset/Phishing URL dataset/URL dataset.csv")
with open(path1, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows1 = list(reader)
print(f"Rows: {len(rows1)}")
from collections import Counter
print(f"Type dist: {Counter(r['type'] for r in rows1)}")

# Check auth URLs
auth_kws = ['login', 'signin', 'account', 'auth', 'verify', 'password', 'secure']
for kw in auth_kws:
    legit = sum(1 for r in rows1 if kw in r['url'].lower() and r['type']=='legitimate')
    phish = sum(1 for r in rows1 if kw in r['url'].lower() and r['type']=='phishing')
    print(f"  {kw}: legit={legit}, phish={phish}")

# Check unique domains
domains1 = set()
for r in rows1:
    u = r['url']
    host = u.split('://')[-1].split('/')[0].split(':')[0].lower() if '://' in u else u.split('/')[0].split(':')[0].lower()
    parts = host.split('.')
    rd = '.'.join(parts[-2:]) if len(parts) >= 2 else host
    domains1.add(rd)
print(f"Unique registered domains: {len(domains1)}")

# 2. LegitPhish dataset
print("\n=== LegitPhish (url_features_extracted1.csv) ===")
path2 = os.path.join(ROOT, "data/LegitPhish Dataset/LegitPhish Dataset/url_features_extracted1.csv")
with open(path2, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows2 = list(reader)
print(f"Rows: {len(rows2)}")
print(f"Labels: {Counter(r['ClassLabel'] for r in rows2)}")
for kw in auth_kws:
    legit = sum(1 for r in rows2 if kw in r['URL'].lower() and r['ClassLabel']=='1')
    phish = sum(1 for r in rows2 if kw in r['URL'].lower() and r['ClassLabel']=='0')
    print(f"  {kw}: legit={legit}, phish={phish}")

domains2 = set()
for r in rows2:
    u = r['URL']
    host = u.split('://')[-1].split('/')[0].split(':')[0].lower() if '://' in u else u.split('/')[0].split(':')[0].lower()
    parts = host.split('.')
    rd = '.'.join(parts[-2:]) if len(parts) >= 2 else host
    domains2.add(rd)
print(f"Unique registered domains: {len(domains2)}")

# 3. Check overlap with existing TRAIN
print("\n=== Domain overlap with existing TRAIN ===")
train = pd.read_csv(os.path.join(ROOT, "data/splits/TRAIN.csv")) if False else None
import csv as c
with open(os.path.join(ROOT, "data/splits/TRAIN.csv"), 'r') as f:
    train_rows = list(c.DictReader(f))
train_domains = set()
for r in train_rows:
    u = r['url']
    host = u.split('://')[-1].split('/')[0].split(':')[0].lower() if '://' in u else u.split('/')[0].split(':')[0].lower()
    parts = host.split('.')
    rd = '.'.join(parts[-2:]) if len(parts) >= 2 else host
    train_domains.add(rd)
print(f"TRAIN domains: {len(train_domains)}")
print(f"Overlap URLdataset-TRAIN: {len(domains1 & train_domains)}")
print(f"Overlap LegitPhish-TRAIN: {len(domains2 & train_domains)}")
print(f"Overlap URLdataset-LegitPhish: {len(domains1 & domains2)}")
