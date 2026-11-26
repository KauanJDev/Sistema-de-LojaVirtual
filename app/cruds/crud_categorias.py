from  fastapi import HTTPException
from sqlalchemy import delete, func, insert, or_, select, update, desc
from app.models.CategoriaModel import Categoria
from app.cruds.funcoes_auxiliares import listar, executar_um, campos
from db.db import Sessao

def criar_categoria(dados):
    return executar_um(
        insert(Categoria).values(**campos(dados)).returning(*Categoria.__table__.c)
    )

def listar_categorias(apenas_ativas=True):

    consulta = select(Categoria.__table__).order_by(Categoria.nome)

    if apenas_ativas:
        consulta = consulta.where(Categoria.ativa)
    return listar(consulta)
