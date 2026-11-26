from  fastapi import HTTPException
from sqlalchemy import delete, func, insert, or_, select, update, desc
from app.models.ClienteModel import Cliente
from app.models.EnderecoModel import Endereco
from app.models.ProdutoModel import Produto
from app.models.EstoqueModel import Estoque, MovimentacaoEstoque
from app.models.PedidoModel import Pedido, ItemPedido, HistoricoStatusPedido
from app.models.Enums import StatusPedido, TipoMovimentacao, TRANSICOES_PERMITIDAS
from db.db import Sessao

def pedido_completo(sessao, id_pedido):

    pedido = (
        sessao.execute(select(Pedido.__table__).where(Pedido.id == id_pedido))
        .mappings()
        .one_or_none()
    )

    if pedido is None:
        return None
    
    itens = (
        select(
            ItemPedido.id,
            ItemPedido.produto_id,
            Produto.nome.label("nome_produto"),
            ItemPedido.quantidade,
            ItemPedido.preco_unitario,
            (ItemPedido.quantidade * ItemPedido.preco_unitario).label("subtotal"),
        )
        .join(Produto)
        .where(ItemPedido.pedido_id == id_pedido)
        .order_by(ItemPedido.id)
    )
    return {**pedido, "itens": sessao.execute(itens).mappings().all()}

def buscar_pedido(id_pedido):
    with Sessao() as sessao:
        return pedido_completo(sessao, id_pedido)

def listar_pedidos(status_pedido=None, cliente_id=None ,data_inicio=None ,data_fim=None ,offset=0 , limit=10,): 
    filtros = []

    if status_pedido is not None:
        filtros.append(Pedido.status == status_pedido)
    if cliente_id is not None:
        filtros.append(Pedido.cliente_id == cliente_id)
    if data_inicio is not None:
        filtros.append(Pedido.data_pedido >= data_inicio)
    if data_fim is not None:
        filtros.append(Pedido.data_pedido <= data_fim)

    consulta = (
        select(
            Pedido.id,
            Pedido.cliente_id,
            Cliente.nome.label("cliente_nome"),
            Pedido.status,
            Pedido.data_pedido,
            Pedido.data_confirmacao,
            Pedido.valor_total,
            func.coalesce(func.sum(ItemPedido.quantidade), 0).label("total_itens"),
        )
        .select_from(Pedido)
        .join(Cliente)
        .outerjoin(ItemPedido)
        .where(*filtros)
        .group_by(Pedido.id, Cliente.nome)
        .order_by(Pedido.data_pedido.desc(), Pedido.id.desc())
        .offset(offset)
        .limit(limit)
    )
    with Sessao() as sessao:
        total = sessao.scalar(select(func.count()).select_from(Pedido).where(*filtros))
        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "itens": sessao.execute(consulta).mappings().all(),
        }

def listar_historico_pedido(id_pedido):
    with Sessao() as sessao:
        if sessao.get(Pedido, id_pedido) is None:
            return None
        
        consulta = select(HistoricoStatusPedido.__table__).where(
            HistoricoStatusPedido.pedido_id == id_pedido
        )
        return (
            sessao.execute(
                consulta.order_by(
                    HistoricoStatusPedido.data_hora, HistoricoStatusPedido.id
                )
            )
            .mappings()
            .all()
        )

def criar_pedido(dados):
    with Sessao.begin() as sessao:
        cliente = sessao.get(Cliente, dados.cliente_id)
        if cliente is None:
            raise HTTPException(404, "Cliente nao encontrado.")
        
        if not cliente.ativo:
            raise HTTPException(400, "Cliente inativo.")
        
        endereco = sessao.get(Endereco, dados.endereco_id)
        if endereco is None or endereco.cliente_id != cliente.id or not endereco.ativo:
            raise HTTPException(
                400, "Endereco invalido ou inativo ou nao pertence ao cliente."
            )
        
        itens = []

        for item in sorted(dados.itens, key=lambda i: i.produto_id):

            produto = sessao.get(Produto, item.produto_id)
            estoque = sessao.get(Estoque, item.produto_id, with_for_update=True)

            if produto is None or estoque is None:
                raise HTTPException(404, f"Produto {item.produto_id} nao encontrado.")
            
            if not produto.ativo:
                raise HTTPException(400, f"Produto {produto.nome} esta inativo.")
            
            if estoque.quantidade_disponivel < item.quantidade:
                raise HTTPException(
                    409,
                    f"Sem estoque de {produto.nome}. Disponivel: {estoque.quantidade_disponivel}.",
                )
            itens.append(
                ItemPedido(
                    produto_id=produto.id,
                    quantidade=item.quantidade,
                    preco_unitario=produto.preco_atual,
                )
            )
        campos = (
            "destinatario",
            "cep",
            "numero",
            "complemento",
            "bairro",
            "cidade",
            "estado",
        )

        entrega = {f"entrega_{campo}": getattr(endereco, campo) for campo in campos}
        pedido = Pedido(
            cliente_id=cliente.id,
            endereco_id=endereco.id,
            **entrega,
            valor_total=sum(item.quantidade * item.preco_unitario for item in itens),
        )
        sessao.add(pedido)
        sessao.flush()

        for item in itens:
            item.pedido_id = pedido.id

        sessao.add_all(itens)
        sessao.add(
            HistoricoStatusPedido(
                pedido_id=pedido.id,
                status_novo=pedido.status,
                observacao="Pedido criado",
            )
        )
        sessao.flush()
        return pedido_completo(sessao, pedido.id)

def atualizar_status_pedido(id_pedido, dados):

    novo = dados.status

    with Sessao.begin() as sessao:
        pedido = sessao.get(Pedido, id_pedido, with_for_update=True)
        if pedido is None:
            raise HTTPException(404, "Pedido nao encontrado.")
        
        anterior = StatusPedido(pedido.status)

        if novo not in TRANSICOES_PERMITIDAS[anterior]:
            raise HTTPException(
                400, f"Transicao invalida de {anterior.value} para {novo.value}."
            )
        
        if novo == StatusPedido.CANCELADO:
            motivo = (dados.motivo_cancelamento or "").strip()
            if not motivo:
                raise HTTPException(400, "O motivo do cancelamento e obrigatorio.")
            pedido.motivo_cancelamento = motivo

        confirmar = novo == StatusPedido.CONFIRMADO
        estornar = (novo == StatusPedido.CANCELADO and anterior == StatusPedido.CONFIRMADO)

        if confirmar or estornar:
            consulta = (
                select(ItemPedido, Produto.nome)
                .join(Produto)
                .where(ItemPedido.pedido_id == pedido.id)
            )

            for item, nome in sessao.execute(consulta.order_by(ItemPedido.produto_id)):
                estoque = sessao.get(Estoque, item.produto_id, with_for_update=True)

                if estoque is None or (
                    confirmar and estoque.quantidade_disponivel < item.quantidade
                ):
                    raise HTTPException(409, f"Sem estoque de {nome}.")
                
                estoque.quantidade_disponivel += (-item.quantidade if confirmar else item.quantidade)
                estoque.atualizado_em = func.now()

                tipo = (
                    TipoMovimentacao.SAIDA_VENDA
                    if confirmar
                    else TipoMovimentacao.ESTORNO_CANCELAMENTO
                )
                sessao.add(
                    MovimentacaoEstoque(
                        produto_id=item.produto_id,
                        pedido_id=pedido.id,
                        tipo=tipo.value,
                        quantidade=item.quantidade,
                        observacao=f"Pedido #{pedido.id}: {novo.value}",
                    )
                )

        datas = {
            StatusPedido.CONFIRMADO: "data_confirmacao",
            StatusPedido.ENVIADO: "data_envio",
            StatusPedido.ENTREGUE: "data_entrega",
            StatusPedido.CANCELADO: "data_cancelamento",
        }

        setattr(pedido, datas[novo], func.now())
        pedido.status = novo.value
        sessao.add(
            HistoricoStatusPedido(
                pedido_id=pedido.id,
                status_anterior=anterior.value,
                status_novo=novo.value,
                observacao=dados.observacao or dados.motivo_cancelamento,
            )
        )
        sessao.flush()
        return pedido_completo(sessao, pedido.id)
