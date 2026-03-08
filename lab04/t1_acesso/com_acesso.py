import json
import os
from abc import ABC, abstractmethod
from pathlib import Path

import requests


class ConfigRepository(ABC):
    @abstractmethod
    def get(self, key: str) -> dict: ...


class LocalConfig(ConfigRepository):
    def __init__(self, path: Path | None = None):
        self._path = path or Path(__file__).with_name("config.json")

    def get(self, key: str) -> dict:
        with self._path.open("r", encoding="utf-8") as f:
            return json.load(f)[key]


class RemoteConfig(ConfigRepository):
    def __init__(self, base_url: str):
        self._base = base_url.rstrip("/")

    def get(self, key: str) -> dict:
        r = requests.get(f"{self._base}/{key}", timeout=3)
        r.raise_for_status()
        return r.json()


def get_repo_from_env() -> ConfigRepository:
    """Factory: seleciona o backend pela variavel CONFIG_BACKEND."""

    backend = (os.getenv("CONFIG_BACKEND") or "local").strip().lower()
    if backend == "local":
        return LocalConfig()
    if backend == "http":
        url = os.getenv("CONFIG_URL") or "http://localhost:8080/config"
        return RemoteConfig(url)
    raise ValueError(f"Backend desconhecido: {backend}")


if __name__ == "__main__":
    repo = get_repo_from_env()
    try:
        cfg = repo.get("database")
        print("Configuracao obtida:", cfg)
    except Exception as e:
        print(f"Erro ao obter configuracao: {e}")
