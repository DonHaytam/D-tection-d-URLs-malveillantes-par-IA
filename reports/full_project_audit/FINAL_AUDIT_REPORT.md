# FINAL AUDIT REPORT — Phishing AI Master 2

Date: 2026-11-25
Auditor: Senior AI/ML + MLOps + Full-Stack QA (autonomous)
Project root: `D:\openhands\projects\v2\phishing_ai_master`

## A. Executive Summary

- Overall project status: **FUNCTIONAL — production-ready for local/academic use, with documented residual risks.**
- Bugs discovered: **6** (2 medium, 3 low, 1 informational).
- Bugs fixed: **4** (DOM null-reference guard, batch >200 silent truncation, explainability removal, health ensemble lazy-load).
- Unresolved issues: **2** (CORS `*` for production hardening, unauthenticated admin/retraining endpoints — documented, not blocking for local use).
- Tests: **31 passed, 0 failed** (18 original + 13 new API edge tests).
- Deployed model checksum unchanged: `388d774e9c98f74b2036f6d0ccf5dc634c61f38750c7ed6e3b24c196a2e99202`.
- LOCKED_TEST / INDEPENDENT: not modified.

## B. Architecture Audit

Actual architecture (verified against source):

```
Browser (index.html + script.js)
   | HTTP (CORS *)
   v
FastAPI main.py (port 8000)
   |-- Predictor (M1_LR_HARDNEG joblib)  -> verdict/score
   |-- EnsemblePredictor (M1+M2+M5)      -> A/B variant
   |-- src/storage/db.py (SQLite WAL)     -> predictions/feedback/runs/events
   |-- src/retraining/pipeline.py          -> candidate training on TRAIN+feedback
   |-- src/inference/explainability.py     -> DISABLED in API/UI
   v
SQLite database/predictions.db
```

Data flow verified:
Frontend → `/predict` → `_predict()` → `assign_variant()` → `Predictor.predict_one()` or `EnsemblePredictor.predict_one()` → `db.save_prediction()` → SQLite. Feedback → `db.set_feedback()`. Monitoring/active-learning/retraining read from SQLite.

Integration problems found:
- `on_event("startup")` deprecated (FastAPI lifespan) — cosmetic, non-blocking.
- `/retraining/run` previously created a duplicate run row — fixed earlier.

## C. Bug Register

| ID | Severity | Component | Bug | Root Cause | Fix | Test |
|---|---|---|---|---|---|---|
| B1 | MEDIUM | Frontend | `Cannot set properties of null (setting 'innerHTML')` | Stale cached HTML + unguarded DOM access | Null guards in `showResult`/`renderExplanation`/`renderChips`; no-cache meta tags | `tests/test_api_edge.py` (frontend id-check script) |
| B2 | MEDIUM | API | `/predict_batch` silently truncated >200 URLs | `req.urls[:200]` without validation | Reject >200 with HTTP 400 | `test_predict_batch_over_limit` |
| B3 | LOW | API | `/health` reported `ensemble_loaded=false` on fresh start | Read `_ensemble` global before lazy load | Call `get_ensemble()` in health | `test_health` |
| B4 | LOW | Frontend | Explainability n-gram fragments not interpretable | Char n-gram contributions noisy for long URLs | Disabled explainability in API/UI; module retained | manual verification |
| B5 | LOW | API | `/retraining/run` duplicate run row | Created placeholder run then pipeline created another | Reuse single run_id | smoke test |
| B6 | INFO | Frontend | Stale browser cache after updates | No cache headers | Added no-cache meta tags | manual (Ctrl+F5) |

## D. Security Findings

- CORS `allow_origins=["*"]` — acceptable for local/academic; **flag for production hardening** (restrict to frontend origin).
- No authentication on admin/retraining endpoints — documented as future idea; not blocking for local use.
- SQL queries use parameterized placeholders — no SQL injection found.
- Frontend uses `escapeHtml` for URL rendering — no XSS found.
- CSV export uses `csv.DictWriter` — formula injection not present (values are plain strings/numbers).
- No secrets/credentials in source code (verified by search).
- URLs treated as text only — no fetching/resolving/rendering anywhere.
- `debug` mode not enabled.

## E. ML and Data Integrity Findings

- Deployed model `M1_LR_HARDNEG` loaded correctly; metadata matches artifact (version, thresholds 0.25/0.75).
- Label convention 0=legitimate, 1=phishing respected throughout.
- Three-class policy verified: `<0.25` LEGITIMATE, `0.25–0.75` NEEDS_REVIEW, `≥0.75` PHISHING.
- Displayed risk score = probability used by decision policy (verified in smoke test).
- Ensemble weights 0.5/0.3/0.2 normalized correctly; A/B assignment stable by client_id hash.
- LOCKED_TEST and INDEPENDENT not used for tuning (verified by code inspection of retraining pipeline — only TRAIN/DEV).
- Candidate artifacts isolated under `models/versions/candidates/`.
- Retraining never overwrites deployed model automatically (status `pending_approval`).

## F. API and Frontend Validation

- All 15 documented endpoints present and functional.
- Edge cases tested: empty URL (400), missing URL (422), empty batch (400), >200 batch (400), invalid feedback (400), not-found prediction (404), stable A/B assignment.
- Frontend: all referenced DOM ids exist (52/52); null guards added.
- Ports consistent: API 8000, frontend 8501.

## G. Database and MLOps Validation

- SQLite integrity_check: **ok**.
- WAL mode enabled; indexes present on timestamp/score/variant/feedback.
- Transactions committed; connections closed.
- Retraining pipeline: validation → dedup → train → DEV eval → candidate → manual approval. Verified via smoke run (insufficient_data path, no deployment).
- Scheduler daemon thread runs every 5 min; `_is_due` guards against frequent runs.

## H. Test Results

```
python -m pytest tests/ -q
31 passed, 2 warnings in 2.96s
```

Warnings: FastAPI `on_event` deprecation (cosmetic).

Manual verification:
- `/health` → ok, model loaded, ensemble loaded.
- `/predict` (google.com) → LEGITIMATE, 0.0687.
- `/predict` (phishing URL) → PHISHING, 0.9998.
- `/feedback`, `/active-learning`, `/monitoring`, `/ab-test`, `/retraining/status`, `/feedback/export` → all 200.

## I. Files Modified

- `deployment/api/main.py` — explainability disabled; batch >200 validation; health ensemble lazy-load.
- `deployment/frontend/script.js` — null guards; removed explain call; window.onerror; explain removal.
- `deployment/frontend/index.html` — removed explain section; no-cache meta tags.
- `deployment/frontend/style.css` — (prior work, unchanged in this audit).
- `tests/test_api_edge.py` — new (13 tests).
- `scripts/audit_db.py`, `scripts/check_ids.js` — audit helpers.
- `setup.bat` — auto-run (prior work).

## J. Remaining Risks

1. CORS `*` — restrict before exposing beyond localhost.
2. No auth on admin endpoints — add role-based access for production.
3. Char n-gram explainability disabled — future feature-based explainability needed.
4. Retraining uses unverified feedback as ground truth heuristically — document and optionally gate by confidence.
5. FastAPI `on_event` deprecation — migrate to lifespan handlers.

## K. Production Readiness Assessment

| Criterion | Status |
|---|---|
| Backend API functional | PASS |
| All documented routes | PASS |
| ML inference correct | PASS |
| Three-class policy | PASS |
| A/B testing | PASS |
| Active learning | PASS |
| Monitoring | PASS |
| Retraining safety | PASS |
| Database integrity | PASS |
| Frontend (no null errors) | PASS |
| Security (local scope) | PARTIAL (CORS/auth) |
| Test coverage | PASS (31 tests) |

**Verdict: READY for local/academic/demo use. For production: implement CORS restriction and authentication first.**
