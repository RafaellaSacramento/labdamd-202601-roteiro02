import os
from pathlib import Path

from dotenv import load_dotenv
import redis

_ENV_PATH = Path(__file__).with_name(".env")
load_dotenv(_ENV_PATH)


def get_redis() -> redis.Redis:
    host = os.getenv("REDIS_HOST") or "localhost"
    port_str = os.getenv("REDIS_PORT") or "6379"
    username = os.getenv("REDIS_USERNAME") or None
    password = os.getenv("REDIS_PASSWORD") or None

    return redis.Redis(
        host=host,
        port=int(port_str),
        username=username,
        password=password,
        ssl=False,
        decode_responses=True,
    )
