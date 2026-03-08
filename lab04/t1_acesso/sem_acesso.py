import json
from pathlib import Path

import requests


def ler_configuracao(origem: str) -> dict:
    if origem == "local":
        config_path = Path(__file__).with_name("config.json")
        with config_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    if origem == "http":
        resp = requests.get("http://config-srv/config", timeout=3)
        resp.raise_for_status()
        return resp.json()
    if origem == "s3":
        raise NotImplementedError("S3 nao configurado neste lab")
    raise ValueError(f"Origem desconhecida: {origem}")


if __name__ == "__main__":
    try:
        cfg = ler_configuracao("local")
        print("Configuracao carregada:", cfg)
    except FileNotFoundError:
        print("config.json nao encontrado — crie um para testar")
    except Exception as e:
        print(f"Erro ao ler configuracao: {e}")
