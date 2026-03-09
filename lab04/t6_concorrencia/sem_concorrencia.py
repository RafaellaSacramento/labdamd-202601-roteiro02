import multiprocessing
import sys
import time
from pathlib import Path

import redis

LAB04_DIR = Path(__file__).resolve().parents[1]
if str(LAB04_DIR) not in sys.path:
    sys.path.insert(0, str(LAB04_DIR))

from redis_utils import get_redis


def inicializar_saldo(valor: int = 1000) -> None:
    r = get_redis()
    r.set("conta:saldo", valor)
    print(f"Saldo inicial: R${valor}")


def transferir_sem_lock(valor: int, nome: str) -> None:
    """Transferencia SEM controle de concorrencia — sujeita a race condition."""
    r = get_redis()

    saldo_raw = r.get("conta:saldo")
    saldo_atual = int(saldo_raw or 0)  

    time.sleep(0.05)
    novo_saldo = saldo_atual - valor
    r.set("conta:saldo", novo_saldo)  
    print(f"  [{nome}] transferiu R${valor}. Saldo registrado: R${novo_saldo}")


def transferir_sem_lock_barreira(valor: int, nome: str, barreira: multiprocessing.Barrier) -> None:
    """
    Variante deterministica: a barreira garante que ambos processos leiam o saldo
    antes de qualquer um escrever, tornando a race condition reproduzivel.
    """

    r = get_redis()

    saldo_raw = r.get("conta:saldo")
    saldo_atual = int(saldo_raw or 0)

    barreira.wait()

    novo_saldo = saldo_atual - valor
    r.set("conta:saldo", novo_saldo)
    print(f"  [{nome}] transferiu R${valor}. Saldo registrado: R${novo_saldo}")


if __name__ == "__main__":
    multiprocessing.freeze_support()

    inicializar_saldo(1000)

    barreira = multiprocessing.Barrier(2)
    p1 = multiprocessing.Process(target=transferir_sem_lock_barreira, args=(200, "Processo-A", barreira))
    p2 = multiprocessing.Process(target=transferir_sem_lock_barreira, args=(300, "Processo-B", barreira))

    p1.start()
    p2.start()

    p1.join()
    p2.join()

    r = get_redis()
    saldo_final = int(r.get("conta:saldo") or 0)
    delta = saldo_final - 500
    print(f"\nSaldo final no Redis: R${saldo_final}")
    print("Saldo correto seria: R$500")
    if delta == 0:
        print("Diferenca por race condition: R$0 (nao ocorreu nesta execucao)")
    elif delta > 0:
        print(f"Diferenca por race condition: R${delta} (saldo ficou MAIOR que o correto)")
    else:
        print(f"Diferenca por race condition: R${-delta} (saldo ficou MENOR que o correto)")
