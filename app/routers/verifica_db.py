from fastapi import APIRouter
from services import crud

router = APIRouter(tags=["Geral"])

@router.get("/verificar-banco", summary="pra ver se o banco ta funcionando")
def verificar_db():
    with crud.get_db_connection() as connection:
        with crud.get_db_cursor(connection) as cursor:
            cursor.execute("SELECT 1 AS ok;")
            return {"api": "ok", "banco": "ok" if cursor.fetchone()["ok"] == 1 else "erro"}

        