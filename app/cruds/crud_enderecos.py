from  fastapi import HTTPException
from sqlalchemy import delete, func, insert, or_, select, update, desc
from app.models.EnderecoModel import Endereco
from app.models.ClienteModel import Cliente
from app.cruds.funcoes_auxiliares import listar, campos
from db.db import Sessao

def buscar_cliente(id_cliente, id_endereco):
    with Sessao() as sessao:
        endereco = (
            sessao.execute(
                select(Endereco.__table__).where(
                    Endereco.id == id_endereco, Endereco.cliente_id == id_cliente
                )
            )
            .mappings()
            .one_or_none()
        )
        return endereco

def limpar_o_principal(sessao, cliente_id):
    sessao.execute(
        update(Endereco)
        .where(Endereco.cliente_id == cliente_id, Endereco.principal)
        .values(principal=False)
    )

def criar_endereco(dados):
    valores = campos(dados)
    with Sessao.begin() as sessao:
        sessao.get(Cliente, dados.cliente_id, with_for_update=True)
        ativos = select(Endereco.id).where(
            Endereco.cliente_id == dados.cliente_id, Endereco.ativo
        )

        if dados.principal:
            limpar_o_principal(sessao, dados.cliente_id)

        valores["principal"] = dados.principal or not sessao.scalar(
            select(ativos.exists())
        )
        return (
            sessao.execute(
                insert(Endereco).values(**valores).returning(*Endereco.__table__.c)
            )
            .mappings()
            .one()
        )

def listar_enderecos(id_cliente, apenas_ativos=True):
    consulta = select(Endereco.__table__).where(Endereco.cliente_id == id_cliente)
    if apenas_ativos:
        consulta = consulta.where(Endereco.ativo)
    return listar(consulta.order_by(Endereco.principal.desc(), Endereco.id))

def atualizar_endereco(id_endereco, dados):
    return alterar_endereco(id_endereco, campos(dados))

def alterar_endereco(id_endereco, valores, exigir_ativo=False):
    with Sessao.begin() as sessao:
        cliente_id = sessao.scalar(
            select(Endereco.cliente_id).where(Endereco.id == id_endereco)
        )

        if cliente_id is None:
            return None
        
        sessao.get(Cliente, cliente_id, with_for_update=True)
        endereco = sessao.get(Endereco, id_endereco)

        if endereco is None:
            return None

        if exigir_ativo and not endereco.ativo:
            return None
        
        if not valores.get("ativo", endereco.ativo):
            valores["principal"] = False

        if valores.get("principal"):
            limpar_o_principal(sessao, cliente_id)

        for campo, valor in valores.items():
            setattr(endereco, campo, valor)

        sessao.flush()
        return (
            sessao.execute(select(Endereco.__table__).where(Endereco.id == id_endereco))
            .mappings()
            .one()
        )

def definir_endereco_principal(id_endereco):
    return alterar_endereco(id_endereco, {"principal": True}, exigir_ativo=True)

def desativar_endereco(id_endereco):
    return alterar_endereco(id_endereco, {"ativo": False})

def reativar_endereco(id_endereco):
    return alterar_endereco(id_endereco, {"ativo": True})
