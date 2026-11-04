import os
import socket

import pymysql
from dotenv import load_dotenv


load_dotenv()


def main() -> None:
    host = os.getenv("MYSQL_HOST", "100.78.215.44")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    user = os.getenv("MYSQL_USER", "climaguru_app")
    password = os.getenv("MYSQL_PASSWORD", "")
    database = os.getenv("MYSQL_DATABASE", "climaguru")

    print(f"[INFO] Verificando socket TCP hacia {host}:{port}...")
    with socket.create_connection((host, port), timeout=5):
        print("[OK] Puerto MySQL accesible")

    print("[INFO] Probando autenticacion MySQL...")
    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        connect_timeout=5,
        read_timeout=5,
        write_timeout=5,
        ssl_disabled=True,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
        print(f"[OK] Conexion MySQL establecida. Version: {version}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
