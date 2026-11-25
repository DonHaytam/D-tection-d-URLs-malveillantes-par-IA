# Security Hardening Report — Phishing AI Master 2

Date: 2026-11-25
Project: `D:\openhands\projects\v2\phishing_ai_master`

## 1. Issues discovered

1. CORS configured with `allow_origins=["*"]` (wildcard) with credentials enabled.
2. FastAPI deprecated `@app.on_event("startup")` lifecycle.
3. Administrative endpoints (`/retraining/run`, `/retraining/approve`, `/retraining/schedule` POST) unprotected.
4. Explainability produced noisy, non-interpretable char n-gram fragments (disabled).
5. No `.env.example` documenting required environment variables.

## 2. Issues fixed

1. CORS replaced with explicit allowlist from `ALLOWED_ORIGINS` env var (default local origins); credentials disabled when wildcard present.
2. Migrated to FastAPI `lifespan` context manager; startup/shutdown behavior preserved.
3. Admin endpoints protected by `X-Admin-API-Key` header checked with `hmac.compare_digest` against `ADMIN_API_KEY` env var. Dev mode (no key) remains open for local use.
4. Explainability kept disabled in API/UI; module retained for future feature-based work.
5. Created `.env.example`.

## 3. Files modified

- `deployment/api/main.py` — lifespan, CORS allowlist, admin auth, version bump.
- `deployment/frontend/script.js` — admin key prompt for retraining (no secret in JS).
- `.env.example` — new.
- `tests/test_api_edge.py` — added CORS tests.

## 4. Authentication architecture

- Header: `X-Admin-API-Key`.
- Secret source: `ADMIN_API_KEY` environment variable (optionally via `.env`).
- Comparison: `hmac.compare_digest` (constant-time).
- Missing/invalid key → HTTP 401.
- Dev mode: if `ADMIN_API_KEY` unset, endpoints remain open (documented limitation).
- No secret returned in responses or logs.

## 5. CORS configuration

- Allowlist from `ALLOWED_ORIGINS` (comma-separated).
- Default: `http://localhost:8501,http://127.0.0.1:8501,http://localhost:8000,http://127.0.0.1:8000`.
- Methods restricted to `GET, POST, OPTIONS`.
- Headers restricted to `Content-Type, X-Admin-API-Key, Authorization`.
- Credentials enabled only when no wildcard.

## 6. Lifespan migration

- Replaced `@app.on_event("startup")` with `@asynccontextmanager lifespan`.
- Startup: `db.init_db()` + scheduler start.
- Shutdown: no-op (connections are per-call).
- No duplicate model loading or DB init.

## 7. Explainability status

- Disabled in API and UI (noisy char n-gram fragments).
- Module `src/inference/explainability.py` retained.
- Future: feature-based explanations with mathematical support only.

## 8. Security tests added

- `test_cors_allowed_origin`, `test_cors_preflight`, `test_cors_rejected_origin_not_credentialed`.
- Admin auth verified manually via `scripts/test_auth.py` (dev mode, missing key, wrong key, valid key, public access).

## 9. Full test results

```
python -m pytest tests/ -q
34 passed, 2 warnings in 2.83s
```

Model checksum preserved: `388d774e9c98f74b2036f6d0ccf5dc634c61f38750c7ed6e3b24c196a2e99202`.

## 10. Remaining risks

1. Admin auth is opt-in (dev mode open when key unset) — set `ADMIN_API_KEY` in production.
2. No role-based access control (single shared key).
3. Explainability disabled.
4. FastAPI lifespan migration complete; no other deprecations.
5. Git repository not initialized in this project — see GitHub section.

## 11. Deployment configuration instructions

1. Copy `.env.example` to `.env`.
2. Set `ADMIN_API_KEY` to a strong random value.
3. Set `ALLOWED_ORIGINS` to your production frontend origin(s).
4. Run `setup.bat` or start uvicorn manually.
5. Verify `/health` reports `admin_auth_enabled: true`.

## 12. GitHub status

No Git repository exists in `D:\openhands\projects\v2\phishing_ai_master` (only `D:\openhands\projects\SI project` has a `.git`). No remote is configured. GitHub push is therefore **BLOCKED** — the user must initialize a repository and configure a remote before pushing. See commands below.

### To enable GitHub push (run manually):

```bash
cd D:\openhands\projects\v2\phishing_ai_master
git init
git add <reviewed-files>
git commit -m "security: harden API and fix audit findings"
git remote add origin https://github.com/<user>/<repo>.git
git branch -M main
git push -u origin main
```

Do NOT commit `.env`, `*.db`, `.venv/`, `data/raw/`, `models/versions/*`, or `experiments/results/*` (already in `.gitignore`).
