"""anti_pattern.py — apenas para leitura.

Transparencia excessiva: a funcao parece local, mas esconde que pode ser uma chamada
remota (latencia, timeout, falhas parciais). O ponto do exemplo e o contrato ruim.
"""


def get_user(user_id: int) -> dict:
    raise NotImplementedError


if __name__ == "__main__":
    print("Este arquivo e apenas para leitura (anti-pattern).")
    print("Veja bom_pattern.py para um contrato mais explicito (async/timeout/Optional).")
