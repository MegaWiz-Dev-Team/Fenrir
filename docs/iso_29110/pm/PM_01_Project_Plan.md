# PM-01: Project Plan — Fenrir
**Project Name:** Fenrir — Computer-Use Agent
**Document Version:** 1.0
**Date:** 2026-03-12
**Standard:** ISO/IEC 29110 — PM Process

---

## 1. Project Scope & Objectives

### เป้าหมาย
AI-powered computer-use agent ที่ทำ browser automation และ FHIR R4 integration สำหรับ clinic management systems โดยเฉพาะ Eir (OpenEMR) เป็น MCP server ให้ Bifrost เชื่อมต่อได้

### Tech Stack
| Layer | Technology |
|:--|:--|
| Runtime | Python 3.11+ |
| Web framework | FastAPI + Uvicorn |
| HTTP client | httpx (async) |
| Browser engine | Browser Use + Playwright |
| Config | pydantic-settings |
| Testing | pytest + pytest-asyncio |

---

## 2. Sprint Schedule

### Sprint 1: Foundation (Mar 12, 2026) — ✅ COMPLETED
| Deliverable | Status |
|:--|:--|
| Project scaffold (pyproject.toml, package structure) | ✅ Done |
| Config module (pydantic-settings) | ✅ Done |
| Health endpoints (/healthz, /readyz) | ✅ Done |
| MCP server (JSON-RPC 2.0, 5 tools) | ✅ Done |
| FHIR R4 client (Patient CRUD + Observation) | ✅ Done |
| FHIR models (Pydantic) | ✅ Done |
| Browser Use agent (navigate, extract, fill, screenshot) | ✅ Done |
| Task router (API vs Browser, Thai+EN keywords) | ✅ Done |
| Localhost-only URL validation (security) | ✅ Done |
| Tests | ✅ Done (35 passed, 0 failed) |

---

*บันทึกโดย: AI Assistant (ตามมาตรฐาน ISO/IEC 29110 หมวด PM-01)*

- **Sprint 31: Mimir Hybrid Search & MCP Server Foundation** [Planned]
  - True Vector Integration, Parallel Tree Search, Neo4j Graph, Ensemble Retrieval, and Rust MCP Server.
- **Sprint 32: Asgard/Bifrost MCP Adapter & Dynamic Tenants** [Planned]
  - Auto-discover tools from MCP servers, Dynamic Context Isolation (X-Tenant-ID), Agent-to-Agent via JSON-RPC.
- **Sprint 33: Ecosystem Gateway Sidecars** [Planned]
  - Yggdrasil & Eir Universal Go Sidecars to expose auth and medical tools to Asgard.
- **Sprint 34: Platform Automation (Testing, Browsing & Security)** [Planned]
  - Deploy MCP across Fenrir, Forseti, Ratatoskr, Huginn, Muninn, and Heimdall.
