from  fastapi import HTTPException
from sqlalchemy import delete, func, insert, or_, select, update, desc
from app.models.ClienteModel import Cliente
from app.cruds.funcoes_auxiliares import campos, executar_um, listar, atualizar
from db.db import Sessao

def criar_cliente(dados):
    return executar_um(
        insert(Cliente).values(**campos(dados)).returning(*Cliente.__table__.c)
    )

def listar_clientes(busca=None, apenas_ativos=True):

    consulta = select(Cliente.__table__).order_by(Cliente.nome)

    if apenas_ativos:
        consulta = consulta.where(Cliente.ativo)

    if busca:
        texto = f"%{busca.strip()}%"
        consulta = consulta.where(
            or_(Cliente.nome.ilike(texto), Cliente.email.ilike(texto))
        )
    return listar(consulta)

def buscar_cliente(id_cliente):
    return executar_um(select(Cliente.__table__).where(Cliente.id == id_cliente))

def atualizar_cliente(id_cliente, dados):
    return atualizar(Cliente, id_cliente, campos(dados))

def desativar_cliente(id_cliente):
    return atualizar(Cliente, id_cliente, {"ativo": False})

def reativar_cliente(id_cliente):
    return atualizar(Cliente, id_cliente, {"ativo": True})
