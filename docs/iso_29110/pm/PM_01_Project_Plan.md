# PM-01: Project Plan (แผนโครงการ)
**Project Name:** Project Fenrir — Computer-Use Agent
**Document Version:** 1.0
**Date:** 2026-03-07
**Standard:** ISO/IEC 29110 — PM Process

---

## 1. Project Scope & Objectives (ขอบเขตและวัตถุประสงค์)

### เป้าหมาย
พัฒนา Computer-Use Agent ที่ควบคุม browser, shell, และ screen ผ่าน MCP protocol เพื่อให้ AI agents ใน Asgard ecosystem สามารถทำงานอัตโนมัติบนหน้าจอคอมพิวเตอร์ได้

### ขอบเขต
- **Browser Automation** — Navigate, click, type, screenshot, extract data
- **Shell Execution** — Run commands, capture output, file management
- **Screen Control** — Mouse/keyboard control, screen capture, OCR
- **MCP Server** — Expose capabilities as MCP tools for Bifrost to call
- **Safety Guardrails** — Sandboxed execution, command whitelist, confirmation prompts

### Tech Stack
| Layer | Technology |
|:--|:--|
| Language | Rust |
| Browser Engine | ZeroClaw (headless Chromium) |
| Screen Control | CoreGraphics (macOS) / X11 (Linux) |
| Protocol | MCP (Model Context Protocol) server |
| Container | Docker |

### Part of Asgard Ecosystem
| Connection | Protocol | Description |
|:--|:--|:--|
| Bifrost → Fenrir | MCP | Tool calling (browser, shell, screen) |
| Fenrir → Yggdrasil | OIDC | Authentication for restricted operations |

---

## 2. Project Organization & Resources (โครงสร้างทีมและทรัพยากร)

| Role | Person/Team |
|:--|:--|
| **Project Manager** | Paripol (MegaWiz) |
| **Developer** | AI-assisted (Antigravity) |
| **Contact** | paripol@megawiz.co |

---

## 3. Project Schedule & Milestones (ตารางเวลาและจุดส่งมอบ)

### Sprint 1: Browser Core (Target: 2026-07)
- [ ] Rust project structure with Docker
- [ ] Headless Chromium integration (ZeroClaw)
- [ ] Navigate, click, type, screenshot functions
- [ ] MCP server (expose browser tools)
- [ ] Unit tests (10+ tests)

### Sprint 2: Shell & Screen (Target: 2026-08)
- [ ] Shell command execution (sandboxed)
- [ ] File system operations (read/write/list)
- [ ] Screen capture & OCR
- [ ] Mouse/keyboard control
- [ ] Safety guardrails (command whitelist)

### Sprint 3: Integration (Target: 2026-09)
- [ ] Bifrost MCP client integration test
- [ ] Multi-step workflow execution
- [ ] Error recovery & retry
- [ ] Structured logging
- [ ] E2E tests with Bifrost + Heimdall

---

## 4. Risk Management (การจัดการความเสี่ยง)

| Risk | Impact | Mitigation |
|:--|:--|:--|
| **Unsafe command execution** | Critical | Sandboxed environment; command whitelist; confirmation prompts |
| **Browser automation detection** | Medium | Stealth mode; realistic timing |
| **Screen resolution differences** | Low | Coordinate normalization; responsive selectors |
| **Headless Chrome instability** | Medium | Crash recovery; session management |
| **Docker container escape** | Critical | Minimal privileges; network isolation; seccomp profiles |

---

*บันทึกโดย: AI Assistant (ตามมาตรฐาน ISO/IEC 29110 หมวด PM-01)*
