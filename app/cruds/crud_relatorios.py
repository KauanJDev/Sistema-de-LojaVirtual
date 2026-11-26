from  fastapi import HTTPException
from sqlalchemy import delete, func, insert, or_, select, update, desc
from app.models.PedidoModel import Pedido, ItemPedido
from app.models.ProdutoModel import Produto
from db.db import Sessao

def relatorio_por_periodo(p_comeco, p_fim):
    filtros = []

    filtros.append(Pedido.status != "AGUARDANDO_CONFIRMADO")
    filtros.append(Pedido.data_confirmacao <= p_fim)

    consulta = (
        select(func.count().label("vendas_durante_periodo")).select_from(Pedido).where(*filtros))

    with Sessao() as sessao:
        result = sessao.execute(consulta).mappings().all()
        return {
            "inicio_periodo" : p_comeco,
            "fim_periodo" : p_fim,
            "produtos_vendidos" : result,
        }

def relatorio_por_produto(produto_id):
    filtros = []

    filtros.append(Pedido.status != "AGUARDANDO_CONFIRMADO")
    filtros.append(ItemPedido.produto_id == produto_id)

    consulta = (
        select(func.count().label("vendas_deste_produto")).select_from(Pedido).where(*filtros))

    with Sessao() as sessao:
        result = sessao.execute(consulta).mappings().all()
        return {
            "produto_id" : produto_id,
            "produtos_vendidos" : result,
        }


def ranking_de_vendas(limit: int):
    filtro = []

    filtro.append(ItemPedido.produto_id == Produto.id)

    sub = (
        select(func.count(Pedido.id))
        .select_from(Pedido)
        .join(ItemPedido, ItemPedido.pedido_id == Pedido.id)
        .where(*filtro)
        .scalar_subquery()
    )
    consulta = (
        select(Produto.id, Produto.nome, sub.label("vendas"))
        .select_from(Produto)
        .order_by(desc(Produto.preco_atual))
        .limit(limit)
    )

    with Sessao() as sessao:
        return {
            "limit": limit,
            "itens": sessao.execute(consulta).mappings().all(),
        }