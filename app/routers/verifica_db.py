from fastapi import APIRouter
from sqlalchemy import select
from db.db import Sessao

router = APIRouter(tags=["Geral"])

@router.get("/verificar-banco", summary="ver se o banco ta prestando")
def verificar_db():
    with Sessao() as sessao:
        return {"api": "ok", "banco": "ok" if sessao.scalar(select(1)) == 1 else "erro"}

        