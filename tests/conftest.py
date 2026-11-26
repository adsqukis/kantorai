import os
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def settings_fixture(tmp_path, monkeypatch):
    from laporan.config import Settings
    return Settings(
        deepseek_api_key="test-key",
        dashboard_password="rahasia",
        session_secret="s" * 32,
        db_path=str(tmp_path / "laporan.db"),
        config_dir=str(ROOT / "config"),
    )
