# Release Notes — Fenrir

## v0.3.0 — JWT Auth + Message Center (2026-03-15)

### 🔒 Security
- **JWT Auth Middleware** via Yggdrasil — Yggdrasil-issued token validation
- Public paths: `/healthz`, `/readyz`, `/docs`
- `AUTH_ENABLED=false` dev bypass
- Depends on: `yggdrasil>=0.1.0`, `PyJWT>=2.0`

### 💬 OpenEMR Message Center
- Message poller: polls OpenEMR inbox for new messages
- Bifrost forwarding: AI processes messages and replies
- OAuth2 token refresh for OpenEMR API
- Feature flag: `MESSAGE_ENABLED=true`

### 📊 Stats
- **63 tests**, all passing (0.24s)
- Sprint 3 complete (ISO 29110 PM-02-04)

---

## v0.2.0 — Docker & Compose (2026-03-13)

### 🐳 Infrastructure
- Dockerfile rewritten: single-stage build, hatchling compatibility
- `.dockerignore` added (includes README.md for hatchling)
- Integrated into Asgard unified Docker Compose (:8200)
- Health endpoint operational at `/health`

### 📊 Stats
- **35 tests**, all passing
- Sprint 2 complete

---

## v0.1.0 — Scaffold (2026-03-12)

> Asgard เป็นของทุกคนแล้ว — Asgard belongs to everyone.

### ✨ New Features
- **MCP Server** — JSON-RPC 2.0 endpoint (POST /mcp) with 5 tool definitions
- **FHIR R4 Client** — async httpx client for Patient search/get/create, Observation get
- **Browser Agent** — Playwright-based automation with localhost-only URL security
- **Task Router** — API-first strategy with Thai + English keyword matching
- **Health Checks** — /healthz (liveness) + /readyz (upstream connectivity)
- **FastAPI app** with CORS, lifespan management
- **Dockerfile** for Docker Compose integration

### 🔒 Security
- Localhost-only URL validation (blocks all non-local URLs)
- Bearer token authentication for FHIR API
- Browser automation in isolated Playwright sandbox

### 📊 Stats
- **35 tests**, all passing
- 9 source modules
- ISO 29110 documentation (PM×3 + SI×4)
