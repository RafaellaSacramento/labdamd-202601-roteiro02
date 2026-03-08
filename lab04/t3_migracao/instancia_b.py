import json
import sys
from pathlib import Path

import redis

LAB04_DIR = Path(__file__).resolve().parents[1]
if str(LAB04_DIR) not in sys.path:
    sys.path.insert(0, str(LAB04_DIR))

from redis_utils import get_redis


def get_session(r: redis.Redis, user_id: str) -> dict:
    raw = r.get(f"session:{user_id}")
    return json.loads(raw) if raw else {}


if __name__ == "__main__":
    r = get_redis()
    try:
        r.ping()
    except Exception as e:
        print(f"[Instancia B] Falha ao conectar no Redis: {e}")
        print("Preencha lab04/.env com REDIS_HOST, REDIS_PORT, REDIS_USERNAME e REDIS_PASSWORD")
        raise

    print("[Instancia B] Nova instancia conectada ao Redis Cloud.")

    sessao = get_session(r, "user_42")

    if sessao:
        print(f"[Instancia B] Sessao recuperada: {sessao}")
        print("[Instancia B] O usuario nao percebeu a migracao de servidor.")
    else:
        print("[Instancia B] Sessao nao encontrada — execute instancia_a.py primeiro.")
