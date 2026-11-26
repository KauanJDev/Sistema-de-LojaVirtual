from  fastapi import HTTPException
from sqlalchemy import delete, func, insert, or_, select, update, desc
from app.models.ProdutoModel import Produto
from app.models.CategoriaModel import Categoria
from app.models.EstoqueModel import Estoque, MovimentacaoEstoque
from app.cruds.funcoes_auxiliares import listar, executar_um, campos, atualizar
from db.db import Sessao

produtos_com_estoque = (
    select(
        Produto.__table__,
        Categoria.nome.label("categoria"),
        Estoque.quantidade_disponivel,
    )
    .select_from(Produto)
    .join(Categoria)
    .outerjoin(Estoque)
)

def criar_produto(dados):

    valores = campos(dados)
    quantidade = valores.pop("quantidade_inicial", 0)

    with Sessao.begin() as sessao:
        produto = Produto(**valores)
        sessao.add(produto)
        sessao.flush()
        sessao.add(Estoque(produto_id=produto.id, quantidade_disponivel=quantidade))
        if quantidade:
            sessao.add(
                MovimentacaoEstoque(
                    produto_id=produto.id,
                    tipo="ENTRADA",
                    quantidade=quantidade,
                    observacao="Estoque inicial",
                )
            )
        sessao.flush()
        return (
            sessao.execute(produtos_com_estoque.where(Produto.id == produto.id))
            .mappings()
            .one()
        )

def listar_produtos(busca=None, categoria_id=None, apenas_ativos=True, apenas_disponiveis=False):

    consulta = produtos_com_estoque.order_by(Produto.nome)

    if apenas_ativos:
        consulta = consulta.where(Produto.ativo)
    if busca and busca.strip():
        consulta = consulta.where(Produto.nome.ilike(f"%{busca.strip()}%"))
    if categoria_id is not None:
        consulta = consulta.where(Produto.categoria_id == categoria_id)
    if apenas_disponiveis:
        consulta = consulta.where(Estoque.quantidade_disponivel > 0)
    return listar(consulta)

def buscar_produto(id_produto):
    return executar_um(produtos_com_estoque.where(Produto.id == id_produto))

def atualizar_produto(id_produto, dados):
    with Sessao.begin() as sessao:
        sessao.execute(
            update(Produto)
            .where(Produto.id == id_produto)
            .values(**campos(dados), atualizado_em=func.now())
        )
        return (
            sessao.execute(produtos_com_estoque.where(Produto.id == id_produto))
            .mappings()
            .one_or_none()
        )

def desativar_produto(id_produto):
    return atualizar(Produto, id_produto, {"ativo": False, "atualizado_em": func.now()})

def reativar_produto(id_produto):
    return atualizar(Produto, id_produto, {"ativo": True, "atualizado_em": func.now()})
