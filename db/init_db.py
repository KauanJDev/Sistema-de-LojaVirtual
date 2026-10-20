from pathlib import Path
from db.db import get_db_connection


def criar_tabelas():
    sql = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")

    connection = get_db_connection()
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
        print("Tabelas criadas com sucesso.")
    finally:
        connection.close()

if __name__ == "__main__":
    criar_tabelas()