import redis

import redis_utils


def main() -> None:
    r = redis_utils.get_redis()
    try:
        r.ping()
        print("Conexao com Redis Cloud estabelecida com sucesso!")
        r.set("lab04:teste", "ok", ex=60)
        print("SET/GET funcionando:", r.get("lab04:teste"))
    except redis.exceptions.ConnectionError as e:
        print(f"Falha de conexao: {e}")
        print("   Verifique HOST e PORT no seu .env")
    except redis.exceptions.AuthenticationError as e:
        print(f"Falha de autenticacao: {e}")
        print("   Verifique se a REDIS_PASSWORD esta correta no seu .env")


if __name__ == "__main__":
    main()
