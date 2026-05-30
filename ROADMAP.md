# Fair Witness — Roadmap to AWS

Goal: take Fair Witness from "runs on my laptop" to a deployed, shareable web
app at **`fairwitness.orchestratorstudios.ai`** that David & Brian can bookmark
and use — mirroring the proven **TableThat** AWS stack (S3 + CloudFront frontend,
Elastic Beanstalk FastAPI backend).

---

## Decisions locked (2026-05-30)

| Decision | Choice |
|----------|--------|
| **Domain** | Frontend `fairwitness.orchestratorstudios.ai`, API `fairwitness-api.orchestratorstudios.ai` |
| **Product shape** | **Public, social fairness analyzer** seeded via Facebook. Everything is **public to view** (reports, feeds, About); the **passphrase is required only to *run* an analysis**, asked lazily at the moment of running and remembered (localStorage). No accounts, no rate-limit machinery — passphrase is the whole access model. |
| **Navigation** | Top nav on every page: **Analyze (home) · Recent · Highlights · About/FAQ**. |
| **Tracking** | Server-side **visit log**: each request records IP + timestamp + path / report id (what they viewed). Stored in the index table; no third-party analytics. |
| **Reports** | **Shareable links from day one** — every analysis gets a permanent public URL (no passphrase to view). This is the unit shared to Facebook. |
| **Datastore** | **Shared MariaDB `chatter` on RDS** (us-east-2) — the same instance TableThat/aftershoot use; new `fairwitness` schema. SQLAlchemy 2.0 async (aiomysql) + PyMySQL, mirroring aftershoot. **Reverses the earlier DynamoDB/S3-reports idea** (Cliff's call — stay consistent with the siblings). One store: a `reports` table (metadata + full report JSON) and a `visits` table. **No S3 report bucket** — S3/CloudFront is only for the static frontend. |
| **Discovery + dedup** | **Recent** = dynamic feed (newest first, from `reports`). **Highlights** = hand-curated fixed list of report ids. **Before running**, a precheck hashes the URL/text (with `utm_*`/`fbclid` stripping) and looks it up → offers the existing report instead of re-spending tokens. |
| **Region** | EB/ALB in `us-east-2` (match the existing `aftershoot` app in this zone); CloudFront cert in `us-east-1` (CloudFront requirement) |
| **Storage** | **No RDS.** Report JSON in a **private** S3 bucket, accessed via the EB instance role (blank AWS keys in prod → boto3 falls through to instance metadata). Clones aftershoot's storage pattern, minus images/presigned URLs |
| **Frontend CDN** | **OAC + private S3 bucket** (clone aftershoot, *not* TableThat's public website endpoint): public access blocked, CloudFront authenticates via Origin Access Control, SPA fallback (403/404→`/index.html` 200) at the CloudFront layer, compression + bucket versioning on |
| **Deploy/versioning** | **TableThat-style `deploy.ps1`** (richer than aftershoot's): auto-increment semver tag → stamp `VITE_APP_VERSION` + write `BUILD_VERSION` + GitHub release, powering the "new version, refresh" banner |

---

## Current state

**Backend** (`backend/`, FastAPI, port 8002)
- Clean services/routers/schemas/agents layout, mirrors TableThat conventions.
- Stateless. No DB, no auth. Only secret is `ANTHROPIC_API_KEY`.
- `GET /api/health` already returns `{status, version, ...}` ✅
- WSGI entrypoint is `main:app` (EB's `02_python.config` expects `application:application`).
- `SETTING_VERSION` is hardcoded `"0.1.0"` — no git-tag/BUILD_VERSION wiring.
- `CORS_ORIGINS = ["*"]` with `allow_credentials=True` — must be locked down for prod.

**Frontend** (`frontend/`, React + Vite + TS, port 5175)
- `productionSettings.apiUrl` is a placeholder `'/api-proxy'`.
- No `.env.production`, no `VITE_APP_VERSION`, no version-check hook.

**Missing entirely (all present in TableThat, to be ported):**
- `backend/application.py` shim, `Procfile`, `.ebextensions/`, `.platform/nginx/`, `.elasticbeanstalk/config.yml`
- `deploy.ps1`, `DEPLOYMENT.md`, `BRANCHING.md`
- Version tracking (git tag → `BUILD_VERSION` → `/api/health` → frontend banner)
- AWS infra: S3 bucket, CloudFront distribution, EB application/environment, ACM certs, Route53 records
- The two new features: **passphrase gate** + **shareable report storage**

---

## Target architecture (mirrors TableThat)

| Component | Stack | Where |
|-----------|-------|-------|
| Frontend | React/Vite static build | **private** S3 (OAC) → CloudFront → `fairwitness.orchestratorstudios.ai` |
| Backend | FastAPI (Gunicorn + Uvicorn workers) | Elastic Beanstalk (us-east-2) → `fairwitness-api.orchestratorstudios.ai` |
| Report store | JSON objects | **private** S3 bucket `fairwitness-reports` (us-east-2), accessed by the EB instance role |
| Secrets | `ANTHROPIC_API_KEY`, `FAIR_WITNESS_PASSPHRASE` | `.env.production` (deployed with bundle) + EB `ENVIRONMENT=production` |
| DNS / TLS | Route53 zone + ACM | **existing** `orchestratorstudios.ai` zone (`Z00390201C7YBLWGSOUMB`) — new cert only |

---

## Phased roadmap

### Phase 0 — AWS prerequisites  ✅ *mostly already in place*
**Verified 2026-05-30** (account `183944926635`, user `cmr`):
- The `orchestratorstudios.ai` hosted zone **already exists** (`Z00390201C7YBLWGSOUMB`) and is live — **no zone creation, no nameserver/propagation wait.**
- A **working twin app, `aftershoot`, is already deployed in this zone** in the exact target shape — clone its setup:
  - `aftershoot.orchestratorstudios.ai` → CloudFront `d12hym4ceugiuz.cloudfront.net`
  - `aftershoot-api.orchestratorstudios.ai` → EB ALB `awseb--awseb-xja4xusy2f7s-158506002.us-east-2.elb.amazonaws.com` (**`us-east-2`**)

Remaining prerequisites:
- [ ] **ACM cert for the frontend in `us-east-1`** covering `fairwitness.orchestratorstudios.ai` (CloudFront requires `us-east-1`). DNS-validate by adding the CNAME to the existing zone — fast, since you own it. There is **no** existing wildcard or fairwitness cert to reuse.
- [ ] **ACM cert for the API in `us-east-2`** covering `fairwitness-api.orchestratorstudios.ai`, for the EB ALB HTTPS listener (the ALB cert must live in the ALB's region). Same DNS-validation step.
- [ ] Confirm AWS CLI + EB CLI are configured locally (`aws sts get-caller-identity` ✅ already confirmed; `eb --version`).

**Gate:** both certs `ISSUED` before pointing `fairwitness.*` records at CloudFront/ALB.

### Phase 1 — Backend deploy-readiness  ✅ *done 2026-05-30 (verified import in dev + prod modes)*
- [x] `backend/application.py` exposes `application = app` (EB `WSGIPath: application:application`).
- [x] Added `Procfile`, `.ebextensions/{02_python,alb,deployment}.config`, `.platform/nginx/conf.d/timeout.conf` (300s timeouts + `proxy_buffering off` for SSE). Skipped aftershoot's `proxy.conf` (it was for image uploads — FW has none).
- [x] **Version wiring:** `SETTING_VERSION` now reads `BUILD_VERSION` → git tag → short SHA (ported from TableThat). Verified: falls to SHA `6ec270f` today.
- [x] **Two-file env strategy:** `ENVIRONMENT=production` → `.env.production`, else `.env`. `.env.production` + `BUILD_VERSION` are git-ignored but bundled via a new `.ebignore` (the 502-trap — handled).
- [x] **Locked down CORS:** prod → `["https://fairwitness.orchestratorstudios.ai"]`, dev → `["*"]`; `allow_credentials=False` (passphrase is a header, not a cookie). Verified both modes.
- [x] Added `gunicorn>=23` to `requirements.txt`; created `venv` + installed deps. Also pre-added Phase 2/3 settings fields (`APP_PASSWORD`, `AWS_*`, `REPORTS_BUCKET`) with safe dev defaults, and documented them in `.env.example`.

### Phase 2 — Access gate (shared passphrase)  ✅ *done 2026-05-30 (gate behavior verified via TestClient)*
> **Core rule:** the passphrase gates **generating a new analysis only**. **Viewing a bookmarked/shared report requires NO passphrase** — anyone with the link can open it. The gate protects token spend, not the reports.

- [x] `APP_PASSWORD` in settings/env (reused aftershoot's name — "empty = open, dev mode"). Documented in `.env.example`.
- [x] Backend: `security.require_app_password` dependency on **only** `POST /api/analysis/analyze` + `POST /api/analysis/stream` → 401 without it. **Public:** `/api/health` and `GET /api/reports/{id}`. Verified: no-pass→401, bad-pass→401, good-pass→reaches handler, report GET→404-not-401.
- [x] Frontend: `lib/passphrase.ts` (localStorage) + axios interceptor + SSE header; compact passphrase field on `AnalyzePage`; 401 → clear + re-prompt. `/r/:id` renders without ever touching the passphrase.
- [x] *Bonus fix:* the global `RequestValidationError` handler crashed (500) serializing Pydantic v2's `ctx` ValueError — fixed with `jsonable_encoder`, now returns a clean 422.

### Phase 3 — Shareable reports (day-one feature)  ✅ *done 2026-05-30*
> **Storage superseded:** originally built on S3 (boto3 `report_store`); now persisted to **MariaDB** (see Datastore decision + Phase 4.5). The user-facing pieces below stand; the storage backend changed.
- [x] Persist on completion in `analysis_service` (best-effort, never breaks analysis); unguessable `secrets.token_urlsafe(9)` id; stamps `report_id` + `created_at`.
- [x] `GET /api/reports/{id}` (public) with id-format validation; `BiasReport` gained `report_id`/`created_at`; mirrored in frontend types.
- [x] Frontend: `/r/:id` `ReportPage` (read-only, reuses `ReportView`, loading/404 states) + "Copy share link" bar on a finished analysis.
- [x] ~~S3 reports bucket + IAM~~ — **dropped**; storage is MariaDB. No reports bucket to provision.

### Phase 4 — Frontend deploy-readiness
- [x] Set `productionSettings.apiUrl = 'https://fairwitness-api.orchestratorstudios.ai'`.
- [ ] Add `.env.production` with `VITE_APP_VERSION=dev` (deploy script overwrites it).
- [ ] Port `useVersionCheck` hook + a "New version available — refresh" banner (polls `/api/health` every 60s).
- [ ] Confirm SSE streaming works cross-origin against the EB domain (it should, with CORS set in Phase 1).

### Phase 4.5 — Public site: navigation, discovery, dedup & tracking  *(the Facebook-engagement build)*
*No new AWS infra for the shell (nav/About/Highlights); Recent, dedup, and tracking need the DynamoDB index — built behind an `is_enabled()` gate like `report_store`, provisioned in Phase 5.*

**Frontend shell (no infra):**  ✅ *done 2026-05-30 (tsc + build clean)*
- [x] Top-nav layout (`NavBar` + `Layout` with `<Outlet/>`) on every page: **Analyze · Recent · Highlights · About** (+ brand → home). Routing restructured under a layout route.
- [x] **About/FAQ page** (`/about`) — methodology content moved out of the modal into a real page + an FAQ section; `MethodologyModal` deleted, its trigger removed from Analyze.
- [x] **Passphrase UX:** always-visible field retired; `PassphraseModal` prompts **at the moment of Analyze**, remembers it (localStorage), and re-opens with an error on 401.
- [x] **Highlights page** (`/highlights`) — renders the curated `lib/highlights.ts` id list as `ReportCard`s; empty state when none.
- [x] **Recent page** (`/recent`) — `ReportCard` feed via `GET /api/reports` (returns `[]` for now → clean empty state). Shared `ReportCard` + `ReportSummary` type added.

**Datastore, dedup & tracking (MariaDB):**  ✅ *code done + logic-verified 2026-05-30 (round-tripped on SQLite; endpoints via TestClient). Live `chatter` connection pending DB creds.*
- [x] `database.py` (async aiomysql engine + `init_db` create_all), `models.py` (`reports`, `visits`), `services/report_repository.py` (save / get+view-count / list_recent / find_by_content_hash / log_visit), `services/content_id.py` (URL/text hash, strips `utm_*`/`fbclid`). Mirrors aftershoot. **Replaced the S3 `report_store`**; `boto3` removed; reports now persist to MariaDB via the orchestrator.
- [x] **Dedup:** `POST /api/analysis/precheck` (public) → returns the existing report for the same URL/text. Frontend offers "View existing / Analyze again" before spending tokens.
- [x] **Recent feed:** `GET /api/reports` → newest-N summaries (public; `[]` when DB off).
- [x] **Visit tracking:** `POST /api/track` beacon (fired on every route change in `Layout`) + auto-log on report open, recording IP (`X-Forwarded-For`) + path + referrer + UA to `visits`.
- [x] **Provisioning + live local verification (2026-05-30):** `fairwitness` schema created on `chatter` (admin creds, separate from `table-that`); `.env` configured; tables auto-created on startup. Ran a real analysis end-to-end → persisted (score 15 "Heavily Biased"), appeared in Recent, dedup precheck matched on re-submit, public fetch incremented `view_count`, and `/about` + report-open visits logged (Facebook referrer captured). Both servers running locally (FE :5175, API :8002).
- [ ] *(Prod follow-up)* Optionally create a scoped `fairwitness_user` for prod instead of `admin`; decide whether prod uses a separate schema from dev.

### Phase 5 — Provision AWS infra  ✅ **LIVE 2026-05-30** (verified end-to-end in prod)
- [x] **ACM certs:** `fairwitness.orchestratorstudios.ai` (us-east-1, CloudFront) + `fairwitness-api.orchestratorstudios.ai` (us-east-2, ALB) — both ISSUED, DNS-validated via the zone automatically.
- [x] **S3 (frontend):** bucket `fairwitness.orchestratorstudios.ai` (us-east-2), all public-access blocks ON, versioning on, OAC `E3RP5DF2NPR2FQ`, bucket policy scoped to the distribution.
- [x] **CloudFront:** dist **`E2PFE6RT5IDOCG`** (`djmt8o0y58rad.cloudfront.net`) — OAC REST origin, redirect-to-HTTPS, compression, SPA 403/404→`/index.html` (200), us-east-1 cert, PriceClass_100. Deployed.
- [x] **Database:** prod uses the same `fairwitness` schema on `chatter` (admin creds in `.env.production`). EB→MariaDB verified live (Recent feed returns data). No S3 reports bucket / no S3 IAM.
- [x] **Elastic Beanstalk:** app `fair-witness-app` + env `fair-witness-env` (Python 3.14 / AL2023, us-east-2), `ENVIRONMENT=production`, ALB with HTTPS:443 (us-east-2 cert via `.ebextensions/https.config`) + idle timeout 300s. Status Ready/Green. (`eb` CLI installed in isolated `.ebcli-venv`.)
- [x] **Route53:** `fairwitness.orchestratorstudios.ai` (A+AAAA) → CloudFront; `fairwitness-api.orchestratorstudios.ai` (A) → EB ALB. Both resolving.
- [x] **Secrets:** `ANTHROPIC_API_KEY`, `APP_PASSWORD`, `DB_*` in `backend/.env.production` (bundled via `.ebignore`).
- [ ] **Loose ends:** (1) `APP_PASSWORD` is the temporary `witness-2026` — change before circulating. (2) prod `/api/health` shows version `0.1.0` (no git tag yet — Phase 6 deploy.ps1 fixes this). (3) optional: 80→443 redirect; dedicated `fairwitness_user`; separate prod schema from dev.

### Phase 6 — Deploy automation & docs
- [ ] Port **TableThat's** `deploy.ps1` (the richer one — aftershoot's stripped its versioning, we keep it). Substitute resources: `S3_BUCKET = "fairwitness.orchestratorstudios.ai"`, `CF_DISTRIBUTION_ID = <new fairwitness id>`, API/frontend URLs, `eb deploy` env `fair-witness-env`. Keep: main-branch guard, dirty-tree guard, auto patch-bump semver tag, `VITE_APP_VERSION` stamping, `BUILD_VERSION` write, S3 sync `--delete`, CloudFront invalidation, `eb deploy`, GitHub release.
- [ ] Write `DEPLOYMENT.md` + `BRANCHING.md` (main = prod, develop = work) adapted to Fair Witness.
- [ ] Decide branching: adopt TableThat's main/develop, or stay single-branch `main` for a 3-person app (simpler — recommended to start).

### Phase 7 — Launch & verify
- [ ] First deploy: `.\deploy.ps1`.
- [ ] Verify: frontend loads over HTTPS; `…-api…/api/health` returns healthy + correct version; an end-to-end analysis runs; share link opens in an incognito window (no passphrase) and renders.
- [ ] Confirm passphrase gate blocks analysis without the secret.
- [ ] **Hand the bookmark to David & Brian** + share the passphrase out-of-band.

---

## Risks & open questions
- ~~New DNS zone is the long pole~~ — **resolved:** the zone exists and a twin app (`aftershoot`) is already live in it. Only the two ACM certs are net-new, and DNS validation is quick since you own the zone. Phase 0 is no longer the bottleneck.
- **Region split:** EB/ALB go in `us-east-2` (match aftershoot), but the CloudFront cert must be in `us-east-1` — don't request both certs in the same region.
- **Cost / abuse:** the passphrase gate is the only spend guard. Consider a cheap backstop later — a per-day analysis count cap and/or `MAX_ARTICLE_CHARS` enforcement (already in settings) to bound token spend.
- **Model choice:** prod still defaults to `claude-sonnet-4-20250514`. Decide whether to bump to a current model (e.g. Sonnet 4.6) for quality/cost before launch.
- **EB instance role:** must be granted S3 access to the reports bucket (Phase 3) or report saving 500s in prod.
- **Share-link privacy:** report ids should be unguessable (random short id), since shared reports are unauthenticated-readable by design.

## Suggested sequencing
Phase 0 is now just "request two certs" (minutes to validate, since the zone is ours).
Phases 1→4 are code and run in parallel. Phase 5 needs the certs `ISSUED`. Phases 6–7
close it out. Because the `aftershoot` twin already proves the whole path in this account
and zone, the realistic order is: **0** (request certs) → **1–4** (~1 sitting of code,
cloning aftershoot's EB scaffolding) → **5** (infra, mirroring aftershoot) →
**6–7** (deploy script + first deploy). No DNS wait gates the work.
