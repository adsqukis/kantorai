import os
from pathlib import Path

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

from .models import BrandMap, ServerConf, SourceSpec


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    db_path: str = "/var/lib/laporan/laporan.db"
    dashboard_password: str = ""
    session_secret: str = ""
    config_dir: str = "config"
    cookie_secure: bool = True  # false hanya untuk coba di http://localhost


def _yaml(settings: Settings, name: str) -> dict:
    path = Path(settings.config_dir) / name
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_servers(settings: Settings) -> dict[str, ServerConf]:
    data = _yaml(settings, "sources.yaml").get("servers", {})
    return {name: ServerConf(name=name, **conf) for name, conf in data.items()}


def load_sources(settings: Settings) -> list[SourceSpec]:
    return [SourceSpec(**s) for s in _yaml(settings, "sources.yaml").get("sources", [])]


def load_brands(settings: Settings) -> list[BrandMap]:
    return [BrandMap(**b) for b in _yaml(settings, "brands.yaml").get("brands", [])]


def token_for(server: ServerConf) -> str:
    token = os.environ.get(server.token_env, "").strip()
    if not token:
        raise RuntimeError(
            f"Token untuk server '{server.name}' belum diisi: set env {server.token_env}"
        )
    return token
