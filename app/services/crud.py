from fastapi import HTTPException
from sqlalchemy import delete, func, insert, or_, select, update
from app.models.ProdutoModel import Produto, CaracteristicaProduto
from app.models.ClienteModel import Cliente
from app.models.CategoriaModel import Categoria
from app.models.EnderecoModel import Endereco
from app.models.PedidoModel import Pedido, ItemPedido, HistoricoStatusPedido
from app.models.EstoqueModel import Estoque, MovimentacaoEstoque
from app.models.Enums import StatusPedido, TipoMovimentacao, TRANSICOES_PERMITIDAS
from db.db import Sessao

# FUNCOES AUXILIARES

def listar(consulta):
    with Sessao() as sessao:
        return sessao.execute(consulta).mappings().all()

def executar_um(comando):
    with Sessao.begin() as sessao:
        return sessao.execute(comando).mappings().one_or_none()

def campos(dados):

    valores = dados.model_dump(exclude_unset=True)

    for campo in (
        "nome",
        "destinatario",
        "numero",
        "bairro",
        "cidade",
        "estado",
        "valor",
    ):
        if valores.get(campo) is not None:
            valores[campo] = valores[campo].strip()

    if valores.get("email"):
        valores["email"] = valores["email"].strip().lower()

    if valores.get("cpf"):
        valores["cpf"] = valores["cpf"].replace(".", "").replace("-", "")
    return valores

def atualizar(modelo, identificador, valores):
    if not valores:
        return executar_um(select(modelo.__table__).where(modelo.id == identificador))
    
    comando = update(modelo).where(modelo.id == identificador).values(**valores)
    return executar_um(comando.returning(*modelo.__table__.c))

# CRUD DE CLIENTE

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

# CRUD DE CATEGORIA

def criar_categoria(dados):
    return executar_um(
        insert(Categoria).values(**campos(dados)).returning(*Categoria.__table__.c)
    )

def listar_categorias(apenas_ativas=True):

    consulta = select(Categoria.__table__).order_by(Categoria.nome)

    if apenas_ativas:
        consulta = consulta.where(Categoria.ativa)
    return listar(consulta)

# CRUD DE PRODUTO

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
    if busca.strip():
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

# CARACTERISTICAS DO PRODUTO

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

# CRUD DE ENDERECO

def limpar_principal(sessao, cliente_id):
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
            limpar_principal(sessao, dados.cliente_id)

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

        if exigir_ativo and not endereco.ativo:
            return None
        
        if not valores.get("ativo", endereco.ativo):
            valores["principal"] = False

        if valores.get("principal"):
            limpar_principal(sessao, cliente_id)

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

# CRUD DE PEDIDO

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
        estornar = (
            novo == StatusPedido.CANCELADO and anterior == StatusPedido.CONFIRMADO
        )
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

# CONTROLE DE ESTOQUE

def listar_estoque():
    return listar(select(Estoque.__table__).order_by(Estoque.produto_id))

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
        variacao = quantidade if entrada else -quantidade

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
