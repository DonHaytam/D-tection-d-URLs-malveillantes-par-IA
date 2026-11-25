"""Collect real legitimate auth URLs from Common Crawl CDX index."""
import sys, os, json, time, urllib.request, urllib.parse
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")

ROOT = "D:/openhands/projects/v2/phishing_ai_master"
OUT = os.path.join(ROOT, "data/interim/cc_auth_urls.json")

# Load Tranco top domains
import zipfile, pandas as pd
with zipfile.ZipFile(os.path.join(ROOT, "data/raw/tranco_top1m.csv.zip")) as z:
    with z.open("top-1m.csv") as f:
        tranco = pd.read_csv(f, header=None, names=["rank", "domain"])

# Auth path patterns to search
AUTH_PATHS = ["/login", "/signin", "/sign-in", "/auth", "/account", "/accounts"]

# Collect URLs
collected = set()
domains = tranco["domain"].head(200).astype(str).tolist()  # start with top 200
errors = 0

for i, domain in enumerate(domains):
    for path in AUTH_PATHS:
        url_pattern = f"{domain}{path}*"
        cdx_url = f"https://index.commoncrawl.org/CC-MAIN-2024-10-index?url={urllib.parse.quote(url_pattern)}&output=json&limit=3"
        try:
            with urllib.request.urlopen(cdx_url, timeout=15) as r:
                for line in r:
                    try:
                        obj = json.loads(line.decode("utf-8"))
                        u = obj.get("url", "")
                        if u and u.startswith("http"):
                            collected.add(u)
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            errors += 1
            if errors > 50:
                print(f"Too many errors, stopping. Collected so far: {len(collected)}")
                break
    if i % 20 == 0:
        print(f"Processed {i+1}/{len(domains)} domains, collected {len(collected)} URLs")
    time.sleep(0.5)  # rate limit

print(f"\nTotal collected: {len(collected)}")

# Save
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(sorted(collected), f, indent=2)
print(f"Saved to {OUT}")

# Show samples
for u in sorted(collected)[:20]:
    print(u)
