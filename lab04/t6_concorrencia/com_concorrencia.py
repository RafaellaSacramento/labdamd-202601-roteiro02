import multiprocessing
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import redis

LAB04_DIR = Path(__file__).resolve().parents[1]
if str(LAB04_DIR) not in sys.path:
    sys.path.insert(0, str(LAB04_DIR))

from redis_utils import get_redis


@contextmanager
def distributed_lock(
    r: redis.Redis,
    resource: str,
    ttl: int = 5,
    wait_timeout: float = 5.0,
    poll_interval: float = 0.05,
):
    """
    Lock distribuido via Redis SET NX EX.

    NX = define somente se a chave NAO existir (atomico).
    EX = TTL em segundos (previne deadlock se o processo travar antes de liberar).

    Esta versao espera (spin-wait) ate conseguir o lock ou estourar wait_timeout,
    para que a demonstracao fique deterministica com dois processos concorrentes.
    """

    key = f"lock:{resource}"
    deadline = time.time() + wait_timeout

    acquired = False
    while time.time() < deadline:
        acquired = bool(r.set(key, "1", nx=True, ex=ttl))
        if acquired:
            break
        time.sleep(poll_interval)

    if not acquired:
        raise RuntimeError(f"Recurso '{resource}' em uso — timeout aguardando lock")

    try:
        yield
    finally:
        r.delete(key)


def inicializar_saldo(valor: int = 1000) -> None:
    r = get_redis()
    r.set("conta:saldo", valor)
    print(f"Saldo inicial: R${valor}")


def transferir_com_lock(valor: int, nome: str) -> None:
    """Transferencia COM lock distribuido — segura entre processos distintos."""
    r = get_redis()

    with distributed_lock(r, "conta:saldo"):
        saldo_atual = int(r.get("conta:saldo") or 0)
        time.sleep(0.05)
        novo_saldo = saldo_atual - valor
        r.set("conta:saldo", novo_saldo)
        print(f"  [{nome}] transferiu R${valor}. Saldo atual: R${novo_saldo}")


if __name__ == "__main__":
    multiprocessing.freeze_support()

    inicializar_saldo(1000)

    p1 = multiprocessing.Process(target=transferir_com_lock, args=(200, "Processo-A"))
    p2 = multiprocessing.Process(target=transferir_com_lock, args=(300, "Processo-B"))

    p1.start()
    p2.start()

    p1.join()
    p2.join()

    r = get_redis()
    saldo_final = int(r.get("conta:saldo") or 0)
    print(f"\nSaldo final no Redis: R${saldo_final}")
    print(f"Resultado: {'R$500 correto' if saldo_final == 500 else 'race condition detectada'}")
