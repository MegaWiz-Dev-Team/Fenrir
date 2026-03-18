"""Browser Agent — Ratatoskr API wrapper for browser automation.

Wraps the shared Ratatoskr browser service to provide structured browser
automation that can be called from MCP tool handlers.

Security: Only allows navigation to localhost URLs by default.

Migration: Replaced direct Playwright usage with Ratatoskr HTTP API
to centralize browser instances and reduce RAM usage.
"""

import logging
import os
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("fenrir.browser")

RATATOSKR_URL = os.getenv("RATATOSKR_URL", "http://ratatoskr:9200")

# Allowed URL patterns for security (patient data must stay local)
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "host.docker.internal",
]


def is_allowed_url(url: str) -> bool:
    """Check if a URL is allowed (localhost-only for security)."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        return hostname in ALLOWED_HOSTS or hostname.endswith(".local")
    except Exception:
        return False


class BrowserAgent:
    """Browser automation agent wrapping Ratatoskr.

    Provides structured methods for browser interaction while enforcing
    security constraints (localhost-only navigation).
    All browser operations go through the shared Ratatoskr service.
    """

    def __init__(self, headless: bool = True, heimdall_url: str = ""):
        self.headless = headless
        self.heimdall_url = heimdall_url
        self.ratatoskr_url = RATATOSKR_URL

    async def navigate(self, url: str) -> str:
        """Navigate to a URL and return page title + content summary.

        Only allows localhost URLs for security.
        Uses Ratatoskr /api/v1/scrape for JS-rendered content.
        """
        if not is_allowed_url(url):
            return f"BLOCKED: URL '{url}' is not allowed. Only localhost URLs are permitted for security."

        logger.info(f"Browser navigate via Ratatoskr: {url}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.ratatoskr_url}/api/v1/scrape",
                    json={"url": url, "extract_text": True},
                )
                resp.raise_for_status()
                data = resp.json()

                title = data.get("title", "")
                content = (data.get("text", "") or "")[:2000]

                return f"Title: {title}\n\nContent:\n{content}"
        except httpx.ConnectError:
            return "ERROR: Ratatoskr not available. Ensure the service is running."
        except Exception as e:
            logger.error(f"Browser navigate error: {e}")
            return f"ERROR: Navigation failed: {e}"

    async def extract(self, selector: str) -> str:
        """Extract text from current page using CSS selector.

        NOTE: For MVP, this creates a fresh browser session.
        Future: maintain persistent browser context.
        """
        logger.info(f"Browser extract: {selector}")
        return "Extract requires an active page. Use browser_navigate first, then extract."

    async def fill_form(self, url: str, fields: dict[str, str]) -> str:
        """Fill a form on a page via Ratatoskr /api/v1/interact.

        Args:
            url: Page URL to navigate to
            fields: Dict of CSS selector → value to fill
        """
        if not is_allowed_url(url):
            return f"BLOCKED: URL '{url}' is not allowed."

        logger.info(f"Browser fill_form via Ratatoskr: {url} ({len(fields)} fields)")

        try:
            # Build action chain: fill each field
            actions = [{"type": "fill", "selector": sel, "value": val} for sel, val in fields.items()]

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.ratatoskr_url}/api/v1/interact",
                    json={"url": url, "actions": actions},
                )
                resp.raise_for_status()
                data = resp.json()

                completed = data.get("actions_completed", 0)
                total = data.get("actions_total", 0)
                error = data.get("error")

                if error:
                    return f"Filled {completed}/{total} fields. Error: {error}"
                return f"Filled {completed}/{total} fields successfully: {list(fields.keys())}"
        except httpx.ConnectError:
            return "ERROR: Ratatoskr not available."
        except Exception as e:
            return f"ERROR: Form fill failed: {e}"

    async def screenshot(self, url: str, path: str = "/tmp/fenrir_screenshot.png") -> str:
        """Take a screenshot of a page via Ratatoskr."""
        if not is_allowed_url(url):
            return f"BLOCKED: URL '{url}' is not allowed."

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.ratatoskr_url}/api/v1/screenshot",
                    json={"url": url},
                )
                resp.raise_for_status()

                # Save screenshot to file
                with open(path, "wb") as f:
                    f.write(resp.content)

                return f"Screenshot saved: {path}"
        except httpx.ConnectError:
            return "ERROR: Ratatoskr not available."
        except Exception as e:
            return f"ERROR: Screenshot failed: {e}"
