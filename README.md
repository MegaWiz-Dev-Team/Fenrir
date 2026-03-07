# 🐺 Fenrir — Computer-Use Agent

> *"The great wolf of immense power"*
>
> Fenrir is a computer-use agent service that enables AI agents to control the Mac Mini — browsing the web, filling forms, extracting data, running shell commands, and automating workflows. Part of the [🏰 Asgard AI Platform](https://github.com/megacare-dev/Asgard).

| Component | Link |
|:--|:--|
| 🏰 Asgard | [Ecosystem Overview](https://github.com/megacare-dev/Asgard) |
| 🧠 Mimir | [RAG + Agent Builder](https://github.com/megacare-dev/Mimir) |
| 🛡️ Heimdall | [LLM Gateway](https://github.com/megacare-dev/Heimdall) |
| ⚡ Bifrost | [Agent Runtime](https://github.com/megacare-dev/Bifrost) |
| 🐺 Fenrir | **This repo** |

---

## Overview

Fenrir provides **computer-use capabilities** as an MCP (Model Context Protocol) server. Bifrost (or any MCP-compatible client) can call Fenrir to interact with the physical machine.

```
Bifrost (Agent Runtime)
    │
    │ MCP Protocol
    ▼
Fenrir (Computer Use)
    ├── 🌐 Browser Control (navigate, click, extract, screenshot)
    ├── 💻 Shell Execution (run commands, scripts)
    ├── 📁 File Management (read, write, search)
    ├── 🖥️ Screen Capture (CGWindowListCreateImage)
    └── ⌨️ Input Control (keyboard, mouse via CGEvent)
```

---

## Architecture

Based on [ZeroClaw](https://github.com/zeroclaw-labs/zeroclaw) — a lightweight Rust agent runtime optimized for efficiency and security.

### Why ZeroClaw?

| Feature | ZeroClaw | OpenClaw |
|:--|:--|:--|
| **Language** | **Rust** ✅ (matches Heimdall/Mimir) | Node.js |
| **Memory** | **< 5MB RAM** | 1GB+ |
| **Startup** | **Milliseconds** | Seconds |
| **Security** | **Sandbox + allowlist** | Requires careful config |
| **Binary size** | **~4MB** | Heavy |

### Customizations from ZeroClaw

| Area | Change |
|:--|:--|
| **LLM Provider** | → Heimdall API |
| **Interface** | + MCP Server protocol |
| **Browser** | + Playwright/Chromium |
| **Screen** | + macOS Accessibility APIs |
| **Security** | Tuned allowlists for our use cases |

---

## MCP Tools

Fenrir exposes these tools via MCP protocol:

### Browser Tools
| Tool | Description |
|:--|:--|
| `browser_navigate` | Navigate to a URL |
| `browser_click` | Click an element by selector |
| `browser_type` | Type text into an input |
| `browser_extract` | Extract text/data from page |
| `browser_screenshot` | Capture page screenshot |
| `browser_fill_form` | Fill form fields from JSON |

### Shell Tools
| Tool | Description |
|:--|:--|
| `run_shell` | Execute a shell command |
| `run_script` | Execute a script file |

### File Tools
| Tool | Description |
|:--|:--|
| `file_read` | Read file contents |
| `file_write` | Write content to file |
| `file_search` | Search for files by pattern |
| `file_list` | List directory contents |

### Screen Tools (Phase 3)
| Tool | Description |
|:--|:--|
| `screen_capture` | Capture screen region |
| `input_click` | Click at coordinates |
| `input_type` | Type text via keyboard |
| `input_key` | Press key combination |

---

## Use Cases

| Use Case | Tools Used |
|:--|:--|
| **Web data extraction** | `browser_navigate` → `browser_extract` |
| **Patient record creation** | `browser_navigate` → `browser_fill_form` → `browser_click` |
| **Ragnarok Online automation** | `screen_capture` → `input_click` → `input_key` |
| **System administration** | `run_shell` → `file_read` → `file_write` |

---

## Configuration

```bash
# ─── Fenrir Server ───────────────────────────────────────
FENRIR_HOST=127.0.0.1       # Local only by default
FENRIR_PORT=8200
FENRIR_LOG_LEVEL=info

# ─── Heimdall (LLM) ─────────────────────────────────────
HEIMDALL_BASE_URL=http://localhost:8080/v1/
HEIMDALL_API_KEY=your-key

# ─── Security ───────────────────────────────────────────
ALLOWED_DOMAINS=*.megacare.co,localhost,*.github.com
ALLOWED_SHELL_COMMANDS=ls,cat,grep,find,curl,python3
WORKSPACE_DIR=/Users/mimir/workspace
SANDBOX_ENABLED=true

# ─── Browser ────────────────────────────────────────────
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30
```

---

## Quick Start

```bash
git clone https://github.com/megacare-dev/Fenrir.git
cd Fenrir
cargo build --release
cp .env.example .env
./target/release/fenrir
```

---

## Roadmap

### Phase 1: Foundation
- [ ] Fork ZeroClaw base
- [ ] Configure Heimdall as LLM provider
- [ ] MCP server interface
- [ ] Basic tools: shell, file, web fetch

### Phase 2: Browser Control
- [ ] Playwright/Chromium integration
- [ ] Navigate, extract, screenshot
- [ ] Form filling automation
- [ ] Cookie/session management

### Phase 3: Screen & Input Control
- [ ] macOS Accessibility API
- [ ] Screen capture (CGWindowListCreateImage)
- [ ] Keyboard/mouse simulation (CGEvent)
- [ ] Game automation support

---

## Security

Fenrir runs with **strict security by default**:

- 🔒 **Localhost-only binding** — not exposed to network
- 🔒 **Domain allowlist** — browser can only visit approved domains
- 🔒 **Command allowlist** — only whitelisted shell commands
- 🔒 **Workspace scoping** — file access restricted to defined directories
- 🔒 **Sandbox mode** — all operations run in constrained environment

---

<p align="center">
  <strong>🐺 Fenrir</strong> — Part of the <a href="https://github.com/megacare-dev/Asgard">🏰 Asgard AI Platform</a>
  <br/>
  <em>The great wolf that does the heavy lifting.</em>
</p>
