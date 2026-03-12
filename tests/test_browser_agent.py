"""Tests for fenrir.browser.agent — Browser Use wrapper."""

from fenrir.browser.agent import BrowserAgent, is_allowed_url


class TestURLSecurity:
    """URL validation tests (security-critical)."""

    def test_localhost_allowed(self):
        assert is_allowed_url("http://localhost:80/test") is True

    def test_127_allowed(self):
        assert is_allowed_url("http://127.0.0.1:9090/healthz") is True

    def test_external_blocked(self):
        assert is_allowed_url("https://google.com") is False

    def test_external_ip_blocked(self):
        assert is_allowed_url("http://192.168.1.1/admin") is False

    def test_local_domain_allowed(self):
        assert is_allowed_url("http://myhost.local/test") is True

    def test_empty_url(self):
        assert is_allowed_url("") is False

    def test_malformed_url(self):
        assert is_allowed_url("not-a-url") is False


class TestBrowserAgent:
    """Browser agent tests."""

    def test_agent_creation(self):
        """Agent should store config."""
        agent = BrowserAgent(headless=True, heimdall_url="http://localhost:8080")
        assert agent.headless is True
        assert agent.heimdall_url == "http://localhost:8080"

    def test_agent_headless_default(self):
        """Default should be headless=True."""
        agent = BrowserAgent()
        assert agent.headless is True

    async def test_navigate_blocked_url(self):
        """External URLs should be blocked."""
        agent = BrowserAgent()
        result = await agent.navigate("https://evil.com/steal-data")
        assert "BLOCKED" in result
