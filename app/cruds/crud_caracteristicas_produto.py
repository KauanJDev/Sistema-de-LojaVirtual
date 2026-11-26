from  fastapi import HTTPException
from sqlalchemy import delete, func, insert, or_, select, update, desc
from app.models.ProdutoModel import CaracteristicaProduto
from app.cruds.funcoes_auxiliares import listar, executar_um, campos
from db.db import Sessao

def criar_caracteristica(dados):
    return executar_um(
        insert(CaracteristicaProduto)
        .values(**campos(dados))
        .returning(*CaracteristicaProduto.__table__.c)
    )

def listar_caracteristicas(id_produto):
    return listar(
        select(CaracteristicaProduto.__table__)
        .where(CaracteristicaProduto.produto_id == id_produto)
        .order_by(CaracteristicaProduto.nome)
    )

def excluir_caracteristica(id_caracteristica):
    return executar_um(
        delete(CaracteristicaProduto)
        .where(CaracteristicaProduto.id == id_caracteristica)
        .returning(*CaracteristicaProduto.__table__.c)
    )
