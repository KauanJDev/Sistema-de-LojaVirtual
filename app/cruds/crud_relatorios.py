from  fastapi import HTTPException
from sqlalchemy import delete, func, insert, or_, select, update, desc
from app.models.PedidoModel import Pedido, ItemPedido
from app.models.ProdutoModel import Produto
from db.db import Sessao

def relatorio_por_periodo(p_comeco, p_fim):
    filtros = []

    filtros.append(Pedido.status != "AGUARDANDO_CONFIRMADO")
    filtros.append(Pedido.data_confirmacao <= p_fim)
    filtros.append(Pedido.data_confirmacao >= p_comeco)

    consulta = (
        select(func.sum(ItemPedido.quantidade).label("vendas_periodo"))
        .select_from(ItemPedido)
        .join(Pedido, Pedido.id == ItemPedido.pedido_id)
        .where(*filtros)
    )

    with Sessao() as sessao:
        result = sessao.execute(consulta).mappings().all()
        return {
            "inicio_periodo" : p_comeco,
            "fim_periodo" : p_fim,
            "itens" : result,
        }

def relatorio_por_produto(produto_id):
    filtros = []

    filtros.append(Pedido.status != "AGUARDANDO_CONFIRMADO")
    filtros.append(ItemPedido.produto_id == produto_id)

    consulta = (
        select(func.sum(ItemPedido.quantidade).label("vendas_deste_produto"))
        .select_from(ItemPedido)
        .join(Pedido, Pedido.id == ItemPedido.pedido_id)
        .where(*filtros)
    )

    with Sessao() as sessao:
        result = sessao.execute(consulta).mappings().all()
        return {
            "produto_id" : produto_id,
            "produtos_vendidos" : result,
        }


def ranking_de_vendas(limit: int):
    filtro = []

    filtro.append(ItemPedido.produto_id == Produto.id)

    consulta = (
        select(Produto.id, Produto.nome, func.sum(ItemPedido.quantidade).label("total_vendido"))
        .select_from(Produto)
        .join(ItemPedido, ItemPedido.produto_id == Produto.id)
        .group_by(Produto.id, Produto.nome)
        .order_by(desc(func.sum(ItemPedido.quantidade)))
        .limit(limit)
    )

    with Sessao() as sessao:
        return {
            "limit": limit,
            "itens": sessao.execute(consulta).mappings().all(),
        }
