"""Tests for application configuration validation."""

import pytest

from underway.config import Settings


class TestValidateRequired:
    def test_valid_settings_passes(self) -> None:
        settings = Settings(
            _env_file=None,
            google_client_id="test-id",
            google_client_secret="test-secret",
        )
        settings.validate_required()  # should not raise

    def test_missing_google_client_id_raises(self) -> None:
        settings = Settings(
            _env_file=None,
            google_client_id="",
            google_client_secret="test-secret",
        )
        with pytest.raises(RuntimeError, match="google_client_id"):
            settings.validate_required()

    def test_missing_multiple_raises(self) -> None:
        settings = Settings(
            _env_file=None,
            google_client_id="",
            google_client_secret="",
        )
        with pytest.raises(RuntimeError, match=r"google_client_id.*google_client_secret"):
            settings.validate_required()
