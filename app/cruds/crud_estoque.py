from  fastapi import HTTPException
from sqlalchemy import delete, func, insert, or_, select, update, desc
from app.models.ClienteModel import Cliente
from app.models.EstoqueModel import Estoque, MovimentacaoEstoque
from app.models.ProdutoModel import Produto
from app.models.Enums import TipoMovimentacao
from app.cruds.funcoes_auxiliares import listar, executar_um
from app.models.ProdutoModel import Produto
from db.db import Sessao

def listar_estoque(produto_id=None):
    consulta = select(Estoque.__table__).order_by(Estoque.produto_id)
    if produto_id is not None:
        consulta = consulta.where(Estoque.produto_id == produto_id)
    return listar(consulta)

def quantidade_disponivel(produto_id):
    return executar_um(
        select(Produto.nome, Estoque.quantidade_disponivel)
        .join(Estoque)
        .where(Produto.id == produto_id)
    )

def alterar_estoque(produto_id, quantidade, tipo):
    with Sessao.begin() as sessao:
        estoque = sessao.get(Estoque, produto_id, with_for_update=True)

        if estoque is None:
            raise HTTPException(404, "Estoque nao encontrado.")
        
        entrada = tipo == TipoMovimentacao.ENTRADA
        variacao = quantidade if entrada else quantidade - estoque.quantidade_disponivel

        if variacao:
            estoque.quantidade_disponivel += variacao
            estoque.atualizado_em = func.now()
            sessao.add(
                MovimentacaoEstoque(
                    produto_id=produto_id,
                    tipo=tipo.value,
                    quantidade=variacao,
                    observacao="Reposição de estoque"
                    if entrada
                    else "Ajuste no registro",
                )
            )
            sessao.flush()
        return (
            sessao.execute(
                select(Estoque.__table__).where(Estoque.produto_id == produto_id)
            )
            .mappings()
            .one()
        )

def listar_movimentacoes(produto_id=None, tipo=None):
    consulta = select(MovimentacaoEstoque.__table__)
    if produto_id is not None:
        consulta = consulta.where(MovimentacaoEstoque.produto_id == produto_id)
    if tipo:
        consulta = consulta.where(MovimentacaoEstoque.tipo == tipo.upper())
    return {"result": listar(consulta), "query": str(consulta)}