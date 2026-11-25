# Leakage Audit — Phishing AI Master 2

## Split integrity

- Split by registrable domain: no domain crosses partitions.
- 96 155 unique registrable domains.
- 591 cross-label domains removed from training.
- Hashes recorded in `data/splits/hashes/v1.json`.

## Duplicate audit

- Exact duplicates: 276 removed.
- Normalized duplicates: 0 additional.
- Near-duplicate detection: not performed (Phase 4).

## Source overlap

- HuggingFace: 99 634 records.
- Tranco: 29 980 records.
- PhishTank: 29 954 records.

## Conclusion

No major data leakage detected. Domain-disjoint split maintained.

---
*Documentation générée par le pipeline du projet `phishing_ai_master`.*