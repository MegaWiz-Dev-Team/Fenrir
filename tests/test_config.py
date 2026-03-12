"""Tests for fenrir.config."""

import os

from fenrir.config import Settings


class TestSettings:
    """Config loading tests."""

    def test_default_settings(self):
        """Default values should be sensible."""
        s = Settings(
            _env_file=None,
        )
        assert s.fenrir_host == "127.0.0.1"
        assert s.fenrir_port == 8200
        assert s.log_level == "info"
        assert s.browser_headless is True

    def test_openemr_defaults(self):
        """OpenEMR defaults should point to localhost."""
        s = Settings(_env_file=None)
        assert "localhost" in s.openemr_url
        assert "fhir" in s.openemr_fhir_url

    def test_heimdall_default(self):
        """Heimdall default should point to port 8080."""
        s = Settings(_env_file=None)
        assert "8080" in s.heimdall_url
