import requests


def buscar_usuario(user_id: int) -> dict:
    url = f"http://192.168.10.42:8080/users/{user_id}"
    r = requests.get(url, timeout=2)
    r.raise_for_status()
    return r.json()


def buscar_produto(prod_id: int) -> dict:
    url = f"http://192.168.10.55:9090/products/{prod_id}"
    r = requests.get(url, timeout=2)
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    try:
        buscar_usuario(1)
    except Exception as e:
        print(f"Falha esperada (IP hardcoded): {type(e).__name__}")
