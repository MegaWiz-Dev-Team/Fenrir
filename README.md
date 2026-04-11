# 🐺 Fenrir — Computer Use Agent

> *The great wolf — AI-powered browser automation and clinic system integration for the Asgard ecosystem*

**Fenrir** is the computer-use component of the [Asgard AI Platform](https://github.com/MegaWiz-Dev-Team/Asgard). It takes natural language commands and executes browser automation tasks, with a primary focus on **Eir (OpenEMR)** clinic management integration.

### 🏥 Role in Multi-Agent Ecosystem

> **Computer Use Agent (ผู้ช่วยธุรการ)** — AI Agent ที่สั่ง Browser ด้วย LLM สำหรับงานที่ไม่มี API เช่น กรอก e-Claim, ส่ง Rezept ผ่าน Web Portal — ใช้ 🐿️ **Ratatoskr** เป็น Browser Engine ด้านล่าง
>
> **Security:** รันใน **Docker Sandbox** แยก Container ต่อ Task เพื่อป้องกันการเข้าถึง DB โดยตรง
>
> 📖 [Full Architecture →](https://github.com/MegaWiz-Dev-Team/Asgard/blob/main/docs/roadmap/MultiAgent_Architecture_Plan.md) | [Sprint Plan →](https://github.com/MegaWiz-Dev-Team/Asgard/blob/main/docs/roadmap/MultiAgent_Sprint_Plan.md)

---

## 🏗️ Architecture

```mermaid
graph TB
    subgraph input["📩 Input Channels"]
        Mimir["🧠 Mimir<br/>RAG + Agent"]
        Bifrost["⚡ Bifrost<br/>Agent Runtime"]
        MsgCenter["💬 OpenEMR<br/>Message Center"]
    end

    subgraph fenrir["🐺 Fenrir — MCP Server + Message Poller"]
        Router["🔀 Task Router<br/>API-able? → FHIR<br/>UI-only? → Browser"]
        Poller["📨 Message Poller<br/>Poll → Bifrost → Reply"]
        FHIR["🏥 FHIR R4 Client<br/>Patient · Encounter · Observation"]
        BrowserUse["🌐 Browser Use<br/>Playwright + LLM"]
    end

    subgraph target["🎯 Target Systems"]
        OpenEMR["🏥 OpenEMR<br/>(localhost)"]
        WebApps["🌐 Other Web Apps"]
    end

    Mimir --> Bifrost
    Bifrost --> |"MCP"| Router
    MsgCenter --> |"poll"| Poller
    Poller --> |"invoke"| Bifrost
    Router --> FHIR
    Router --> BrowserUse
    FHIR --> OpenEMR
    BrowserUse --> OpenEMR
    BrowserUse --> WebApps
    Poller --> |"reply"| OpenEMR

    style fenrir fill:#1c1917,stroke:#a8a29e,color:#e7e5e4
    style input fill:transparent,stroke:#94a3b8
    style target fill:transparent,stroke:#94a3b8
```

---

## 📦 Tech Stack

| Component | Technology | Purpose |
|:--|:--|:--|
| **MCP Server** | Python (FastAPI) | Tool interface for Bifrost |
| **Browser Automation** | [Browser Use](https://github.com/browser-use/browser-use) | Natural language → browser actions |
| **Browser Engine** | Playwright | Headless/headed browser control |
| **API Integration** | FHIR R4 Client (`fhirclient`) | Direct OpenEMR data operations |
| **Message Poller** | asyncio + httpx | Poll OpenEMR Message Center, relay to Bifrost |
| **LLM Backend** | Heimdall Gateway | Local LLM inference (Ollama/MLX) |

---

## 🎯 Use Cases

### Clinic Management (OpenEMR)

| Task | Method | Example |
|:--|:--|:--|
| Register patient | **FHIR API** | "ลงทะเบียนคนไข้ใหม่ นายสมชาย อายุ 45 ปี" |
| Record vitals | **FHIR API** | "บันทึก BP 120/80 HR 72 Temp 36.5" |
| Create encounter | **FHIR API** | "สร้าง visit ใหม่สำหรับ HN 12345" |
| Fill complex forms | **Browser Use** | "กรอกแบบฟอร์มส่งตัวผู้ป่วย" |
| Generate reports | **Browser Use** | "พิมพ์ใบสรุปการรักษา" |

### OpenEMR Messaging (AI Assistant)

| Task | Method | Example |
|:--|:--|:--|
| Chat with AI | **Message Center** | ส่งข้อความถึง `fenrir-ai` ใน OpenEMR |
| Get patient info | **Message → Bifrost** | "ขอดูข้อมูลคนไข้ HN 12345" |
| Ask clinical Q | **Message → Bifrost** | "ยา Metformin ควรให้ dose เท่าไหร่" |

### General Browser Automation

- Web scraping and data extraction
- Form filling across any web application
- Automated testing and QA

---

## 🔒 Security

> [!CAUTION]
> **Patient data must never leave the local machine.**

| Security Measure | Description |
|:--|:--|
| **Localhost only** | Fenrir listens on `127.0.0.1:8200` only |
| **Local LLM** | All inference via Heimdall → Ollama/MLX (no cloud API for patient data) |
| **FHIR Auth** | OAuth2 + OpenID Connect for OpenEMR API |
| **Sandbox** | Browser Use runs in isolated workspace |
| **No external data** | Patient information never sent to external APIs |

---

## 🔧 Configuration

| Setting | Default | Description |
|:--|:--|:--|
| `FENRIR_PORT` | `8200` | MCP server port |
| `OPENEMR_URL` | `http://localhost:80` | OpenEMR base URL |
| `OPENEMR_FHIR_URL` | `http://localhost:80/apis/default/fhir` | FHIR R4 endpoint |
| `HEIMDALL_URL` | `http://localhost:8080` | LLM Gateway |
| `BROWSER_HEADLESS` | `true` | Run browser in headless mode |
| `MESSAGE_ENABLED` | `true` | Enable OpenEMR message polling |
| `MESSAGE_POLL_INTERVAL` | `30` | Poll interval (seconds) |
| `FENRIR_USERNAME` | `fenrir-ai` | OpenEMR AI user account |

---

## 🗺️ Roadmap

- [x] Project scaffold (FastAPI + MCP Server)
- [x] FHIR R4 client for OpenEMR (Patient CRUD)
- [x] Browser Use integration (natural language → browser actions)
- [x] MCP tool definitions (browser_navigate, form_fill, fhir_search_patient, etc.)
- [x] OpenEMR Message Center integration (AI chat via messaging)
- [x] Docker Compose integration
- [ ] Browser Use + Heimdall LLM
- [ ] OpenEMR form mapping (encounter, vitals, prescriptions)
- [ ] Yggdrasil JWT auth
- [ ] Integration testing with Bifrost

---

## 📚 Related

- [Asgard AI Platform](https://github.com/MegaWiz-Dev-Team/Asgard) — Ecosystem overview
- [Heimdall](https://github.com/MegaWiz-Dev-Team/Heimdall) — LLM Gateway
- [Mimir](https://github.com/MegaWiz-Dev-Team/Mimir) — RAG + Agent Builder
- [Bifrost](https://github.com/MegaWiz-Dev-Team/Bifrost) — Agent Runtime
- [Browser Use](https://github.com/browser-use/browser-use) — Browser automation framework
- [OpenEMR](https://www.open-emr.org/) — Open-source clinic management

---

## 📄 License

**AGPL-3.0** — See [LICENSE](LICENSE)

© 2026 MegaWiz
