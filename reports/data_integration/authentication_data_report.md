# Authentication Data Report — Phishing AI Master 2

## Available authentication URLs

| Source | Legitimate auth | Phishing auth | Total |
|---|---:|---:|---:|
| HuggingFace | 184 | 2 707 | 2 891 |
| PhiUSIIL | 141 | 3 473+ | 3 614+ |
| Tranco (constructed) | 1 300 000 | 0 | 1 300 000 |
| Common Crawl | 3 | 0 | 3 |

## Verification status

- VERIFIED_LEGITIMATE_AUTH_URL: < 200 (from HuggingFace + PhiUSIIL, mostly false matches)
- VERIFIED_PHISHING_URL: ~6 000+ (from HuggingFace + PhiUSIIL)
- CONSTRUCTED (not verified): 1 300 000 (Tranco + auth paths)

## Conclusion

Insufficient verified legitimate authentication URLs. PILU-60K (20 000 real legit auth URLs) is needed.

---
*Documentation générée par le pipeline du projet `phishing_ai_master`.*