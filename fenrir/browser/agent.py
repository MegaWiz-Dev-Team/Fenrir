"""Browser Agent — Browser Use wrapper for browser automation.

Wraps the browser-use library to provide structured browser automation
that can be called from MCP tool handlers.

Security: Only allows navigation to localhost URLs by default.
"""

import logging
from urllib.parse import urlparse

logger = logging.getLogger("fenrir.browser")

# Allowed URL patterns for security (patient data must stay local)
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
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
    """Browser automation agent wrapping Browser Use.

    Provides structured methods for browser interaction while enforcing
    security constraints (localhost-only navigation).
    """

    def __init__(self, headless: bool = True, heimdall_url: str = ""):
        self.headless = headless
        self.heimdall_url = heimdall_url
        self._browser = None

    async def navigate(self, url: str) -> str:
        """Navigate to a URL and return page title + content summary.

        Only allows localhost URLs for security.
        """
        if not is_allowed_url(url):
            return f"BLOCKED: URL '{url}' is not allowed. Only localhost URLs are permitted for security."

        logger.info(f"Browser navigate: {url} (headless={self.headless})")

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)

                title = await page.title()
                # Get first 2000 chars of text content
                content = await page.evaluate("document.body?.innerText?.substring(0, 2000) || ''")

                await browser.close()

                return f"Title: {title}\n\nContent:\n{content}"
        except ImportError:
            return "ERROR: Playwright not installed. Run: playwright install chromium"
        except Exception as e:
            logger.error(f"Browser navigate error: {e}")
            return f"ERROR: Navigation failed: {e}"

    async def extract(self, selector: str) -> str:
        """Extract text from current page using CSS selector.

        NOTE: For MVP, this creates a fresh browser session.
        Future: maintain persistent browser context.
        """
        logger.info(f"Browser extract: {selector}")
        return f"Extract requires an active page. Use browser_navigate first, then extract."

    async def fill_form(self, url: str, fields: dict[str, str]) -> str:
        """Fill a form on a page.

        Args:
            url: Page URL to navigate to
            fields: Dict of CSS selector → value to fill
        """
        if not is_allowed_url(url):
            return f"BLOCKED: URL '{url}' is not allowed."

        logger.info(f"Browser fill_form: {url} ({len(fields)} fields)")

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)

                filled = []
                for selector, value in fields.items():
                    try:
                        await page.fill(selector, value)
                        filled.append(selector)
                    except Exception as e:
                        logger.warning(f"Failed to fill {selector}: {e}")

                await browser.close()

                return f"Filled {len(filled)}/{len(fields)} fields: {filled}"
        except ImportError:
            return "ERROR: Playwright not installed."
        except Exception as e:
            return f"ERROR: Form fill failed: {e}"

    async def screenshot(self, url: str, path: str = "/tmp/fenrir_screenshot.png") -> str:
        """Take a screenshot of a page."""
        if not is_allowed_url(url):
            return f"BLOCKED: URL '{url}' is not allowed."

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await page.screenshot(path=path)
                await browser.close()
                return f"Screenshot saved: {path}"
        except Exception as e:
            return f"ERROR: Screenshot failed: {e}"
