import csv, os
ROOT = "D:/openhands/projects/v2/phishing_ai_master"

# Read TRAIN with utf-8
train_domains = set()
with open(os.path.join(ROOT, "data/splits/TRAIN.csv"), 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        u = r['url']
        host = u.split('://')[-1].split('/')[0].split(':')[0].lower() if '://' in u else u.split('/')[0].split(':')[0].lower()
        parts = host.split('.')
        rd = '.'.join(parts[-2:]) if len(parts) >= 2 else host
        train_domains.add(rd)
print(f"TRAIN domains: {len(train_domains)}")

# URL dataset domains
url_domains = set()
with open(os.path.join(ROOT, "data/Phishing URL dataset/Phishing URL dataset/URL dataset.csv"), 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        u = r['url']
        host = u.split('://')[-1].split('/')[0].split(':')[0].lower() if '://' in u else u.split('/')[0].split(':')[0].lower()
        parts = host.split('.')
        rd = '.'.join(parts[-2:]) if len(parts) >= 2 else host
        url_domains.add(rd)
print(f"URL dataset domains: {len(url_domains)}")
print(f"Overlap URL-TRAIN: {len(url_domains & train_domains)}")

# LegitPhish domains
lp_domains = set()
with open(os.path.join(ROOT, "data/LegitPhish Dataset/LegitPhish Dataset/url_features_extracted1.csv"), 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        u = r['URL']
        host = u.split('://')[-1].split('/')[0].split(':')[0].lower() if '://' in u else u.split('/')[0].split(':')[0].lower()
        parts = host.split('.')
        rd = '.'.join(parts[-2:]) if len(parts) >= 2 else host
        lp_domains.add(rd)
print(f"LegitPhish domains: {len(lp_domains)}")
print(f"Overlap LP-TRAIN: {len(lp_domains & train_domains)}")
print(f"Overlap URL-LP: {len(url_domains & lp_domains)}")

# Check legit auth URLs in URL dataset
legit_auth = 0
with open(os.path.join(ROOT, "data/Phishing URL dataset/Phishing URL dataset/URL dataset.csv"), 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        if r['type'] == 'legitimate' and any(kw in r['url'].lower() for kw in ['login','signin','account','auth','verify']):
            legit_auth += 1
print(f"\nLegit auth URLs in URL dataset: {legit_auth}")

# Check legit auth URLs in LegitPhish
legit_auth2 = 0
with open(os.path.join(ROOT, "data/LegitPhish Dataset/LegitPhish Dataset/url_features_extracted1.csv"), 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        if r['ClassLabel'] == '1' and any(kw in r['URL'].lower() for kw in ['login','signin','account','auth','verify']):
            legit_auth2 += 1
print(f"Legit auth URLs in LegitPhish: {legit_auth2}")
