# SI-01: Software Requirements Specification (SRS)
**Project Name:** Fenrir — Computer-Use Agent
**Document Version:** 1.0
**Date:** 2026-03-12
**Standard:** ISO/IEC 29110 — SI Process

---

## 1. Introduction (บทนำ)

**Fenrir** คือ Computer-Use Agent สำหรับ Asgard AI Platform ทำหน้าที่ browser automation และ FHIR R4 integration เพื่อควบคุมระบบคลินิก (OpenEMR/Eir) ผ่าน natural language commands โดยทำงานเป็น MCP Server ให้ Bifrost Agent Runtime เชื่อมต่อ

---

## 2. Functional Requirements (ความต้องการด้านฟังก์ชัน)

| Req ID | Sprint | Requirement Description | Priority |
|:--|:--|:--|:--|
| REQ-001 | 1 | **MCP Server:** ระบบต้องให้บริการ JSON-RPC 2.0 endpoint (`POST /mcp`) รองรับ `initialize`, `tools/list`, `tools/call` ตามมาตรฐาน MCP Protocol | High |
| REQ-002 | 1 | **FHIR R4 Client:** ระบบต้องเชื่อมต่อ OpenEMR FHIR R4 API รองรับ Patient search/get/create และ Observation get | High |
| REQ-003 | 1 | **Browser Automation:** ระบบต้องรองรับ browser automation ผ่าน Browser Use + Playwright (navigate, extract, fill form, screenshot) | High |
| REQ-004 | 1 | **Task Router:** ระบบต้องตัดสินใจอัตโนมัติว่า task ควรใช้ FHIR API หรือ Browser automation (รองรับ Thai + English keywords) | Medium |
| REQ-005 | 1 | **Health Checks:** ระบบต้องมี liveness (`/healthz`) และ readiness (`/readyz`) endpoints ตรวจ Heimdall + OpenEMR connectivity | High |
| REQ-006 | 1 | **Configuration:** ระบบต้อง load settings จาก environment variables (pydantic-settings) | High |
| REQ-007 | 2 | **Browser Use + LLM:** ระบบต้องเชื่อม Browser Use กับ Heimdall LLM สำหรับ NL → browser action planning | High |
| REQ-008 | 2 | **OpenEMR Form Mapping:** ระบบต้อง map clinical forms (encounter, vitals, prescriptions) สำหรับ auto-fill | Medium |
| REQ-009 | 2 | **Persistent Browser Session:** ระบบต้องรองรับ browser session ที่ persist ข้าม tool calls | Medium |
| REQ-010 | 3 | **Bifrost Integration Test:** ระบบต้อง integration test กับ Bifrost MCP client จริง | High |

---

## 3. Non-Functional Requirements (ความต้องการด้านอื่นๆ)

- **Security:**
  - Patient data ต้องไม่ออกนอก localhost (URL validation: localhost/127.0.0.1 only)
  - LLM inference ผ่าน Heimdall (local Ollama/MLX) เท่านั้น — ห้ามส่ง patient data ไป cloud API
  - FHIR API ใช้ Bearer token authentication
  - Browser Use ทำงานใน isolated Playwright sandbox

- **Performance:**
  - MCP tool call response time < 5s (FHIR operations)
  - Browser automation response time < 30s (complex page interactions)
  - Health check response time < 1s

- **Reliability:**
  - ระบบต้อง graceful degradation เมื่อ Heimdall/OpenEMR ไม่พร้อม
  - Browser agent ต้อง timeout protection (15s per navigation)

- **Maintainability:**
  - ใช้ Python 3.11+ features (type hints, dataclass)
  - Modular architecture (api/, fhir/, browser/ packages)
  - Comprehensive test coverage (≥ 80%)

---

*บันทึกโดย: AI Assistant (ตามมาตรฐาน ISO/IEC 29110 หมวด SI-01)*
