import json
import sys
from pathlib import Path

import redis

LAB04_DIR = Path(__file__).resolve().parents[1]
if str(LAB04_DIR) not in sys.path:
    sys.path.insert(0, str(LAB04_DIR))

from redis_utils import get_redis


def save_session(r: redis.Redis, user_id: str, data: dict) -> None:
    r.setex(name=f"session:{user_id}", time=3600, value=json.dumps(data))
    print(f"[Instancia A] Sessao de '{user_id}' salva no Redis Cloud.")


if __name__ == "__main__":
    r = get_redis()
    try:
        r.ping()
    except Exception as e:
        print(f"[Instancia A] Falha ao conectar no Redis: {e}")
        print("Preencha lab04/.env com REDIS_HOST, REDIS_PORT, REDIS_USERNAME e REDIS_PASSWORD")
        raise

    print("[Instancia A] Conectada ao Redis Cloud.")

    # Usuario navega — estado salvo no Redis Cloud, nao em memoria
    save_session(
        r,
        "user_42",
        {"cart": ["item_1", "item_2"], "promo": "DESCONTO10"},
    )

    print("[Instancia A] Encerrando processo — simulando migracao de servidor.")
