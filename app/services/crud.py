from decimal import Decimal
from fastapi import HTTPException
from db.db import get_db_connection, get_db_cursor
from app.models.Enums import StatusPedido, TipoMovimentacao, TRANSICOES_PERMITIDAS

# CRUD DE CLIENTE

def criar_cliente(dados):
    sql = """
        INSERT INTO clientes
            (nome, email, cpf, telefone)
        VALUES
            (%s, %s, %s, %s)
        RETURNING *;
    """

    parametros = (
        dados.nome.strip(),
        dados.email.strip().lower(),
        dados.cpf.replace(".", "").replace("-", "") if dados.cpf else None,
        dados.telefone,
    )
 
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql, parametros)
            return cursor.fetchone()
 
def listar_clientes(busca=None, apenas_ativos=True):
    sql = """SELECT * FROM clientes WHERE 1 = 1"""
    parametros = []

    if apenas_ativos:
        sql += " AND ativo"

    if busca:
        texto = f"%{busca.strip()}%"
        sql += " AND (nome ILIKE %s OR email ILIKE %s)"
        parametros.append(texto)
        parametros.append(texto)

    sql += " ORDER BY nome;"

    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql, parametros)
            return cursor.fetchall()

def buscar_cliente(id_cliente):
    sql = """
        SELECT *
        FROM clientes
        WHERE id = %s;
    """
 
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql, (id_cliente,))
            return cursor.fetchone()

def atualizar_cliente(id_cliente, dados):
    sql = """
        UPDATE clientes
        SET nome = (%s, nome),
            email = (%s, email),
            cpf = (%s, cpf),
            telefone = (%s, telefone),
            ativo = (%s, ativo)
        WHERE id = %s
        RETURNING *;
    """
 
    parametros = (
        dados.nome.strip() if dados.nome else None,
        dados.email.strip().lower() if dados.email else None,
        dados.cpf.replace(".", "").replace("-", "") if dados.cpf else None,
        dados.telefone,
        dados.ativo,
        id_cliente,
    )
 
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql, parametros)
            return cursor.fetchone()
 
def desativar_cliente(id_cliente):
    sql = """
        UPDATE clientes
        SET ativo = FALSE
        WHERE id = %s
        RETURNING *;
    """
 
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql, (id_cliente,))
            return cursor.fetchone()
 
def reativar_cliente(id_cliente):
    sql = """
        UPDATE clientes
        SET ativo = TRUE
        WHERE id = %s
        RETURNING *;
    """
 
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql, (id_cliente,))
            return cursor.fetchone()

# CADASTRO DE CATEGORIA

def criar_categoria(dados):
    sql = """
        INSERT INTO categorias
            (nome, descricao)
        VALUES (%s, %s)
        RETURNING *;
    """
 
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql, (dados.nome.strip(), dados.descricao))
            return cursor.fetchone()
 
def listar_categorias(apenas_ativas=True):
    sql = """
        SELECT *
        FROM categorias
        WHERE (ativa OR NOT %s)
        ORDER BY nome;
    """
 
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql, (apenas_ativas,))
            return cursor.fetchall()

# CRUD DE PRODUTO

SELECT_PRODUTO = """
    SELECT
        p.id,
        p.categoria_id,
        c.nome AS categoria,
        p.nome,
        p.descricao,
        p.preco_atual,
        p.ativo,
        e.quantidade_disponivel,
        p.criado_em,
        p.atualizado_em
    FROM produtos p
    INNER JOIN categorias c
        ON c.id = p.categoria_id
    LEFT JOIN estoque e
        ON e.produto_id = p.id
"""

def criar_produto(dados):
    sql_produto = """
        INSERT INTO produtos
            (categoria_id, nome, descricao, preco_atual)
        VALUES
            (%s, %s, %s, %s)
        RETURNING id;
    """
 
    sql_estoque = """
        INSERT INTO estoque
            (produto_id, quantidade_disponivel)
        VALUES (%s, %s);
    """
 
    sql_movimentacao = """
        INSERT INTO movimentacoes_estoque
            (produto_id, tipo, quantidade, observacao)
        VALUES (%s, 'ENTRADA', %s, 'Estoque inicial');
    """
 
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(
                sql_produto,
                (
                    dados.categoria_id,
                    dados.nome.strip(),
                    dados.descricao,
                    dados.preco_atual,
                ),
            )
            id_produto = cursor.fetchone()["id"]
 
            cursor.execute(sql_estoque, (id_produto, dados.quantidade_inicial))
 
            if dados.quantidade_inicial > 0:
                cursor.execute(sql_movimentacao, (id_produto, dados.quantidade_inicial))
 
            cursor.execute(SELECT_PRODUTO + " WHERE p.id = %s;", (id_produto,))
            return cursor.fetchone()

def listar_produtos(busca=None, categoria_id=None, apenas_ativos=True,
                    apenas_disponiveis=False):
    filtros = []
    parametros = []

    busca = (busca or "").strip()

    if apenas_ativos:
        filtros.append("p.ativo")
    if busca:
        filtros.append("p.nome ILIKE %s")
        parametros.append(f"%{busca}%")
    if categoria_id is not None:
        filtros.append("p.categoria_id = %s")
        parametros.append(categoria_id)
    if apenas_disponiveis:
        filtros.append("e.quantidade_disponivel > 0")

    sql = SELECT_PRODUTO
    if filtros:
        sql += " WHERE " + " AND ".join(filtros)
    sql += " ORDER BY p.nome;"

    busca = busca.strip() if busca else None
 
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql, parametros)
            return cursor.fetchall()
 
def buscar_produto(id_produto):
    sql = SELECT_PRODUTO + " WHERE p.id = %s;"
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql, (id_produto,))
            return cursor.fetchone()

def atualizar_produto(id_produto, dados):
    sql = """
        UPDATE produtos
        SET categoria_id = (%s, categoria_id),
            nome = (%s, nome),
            descricao = (%s, descricao),
            preco_atual = (%s, preco_atual),
            ativo = (%s, ativo),
            atualizado_em = NOW()
        WHERE id = %s;
    """
 
    parametros = (
        dados.categoria_id,
        dados.nome.strip() if dados.nome else None,
        dados.descricao,
        dados.preco_atual,
        dados.ativo,
        id_produto,
    )
 
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql, parametros)
 
            if cursor.rowcount == 0:
                return None
 
            cursor.execute(SELECT_PRODUTO + " WHERE p.id = %s;", (id_produto,))
            return cursor.fetchone()

def desativar_produto(id_produto):
    sql = """
        UPDATE produtos
        SET ativo = FALSE,
            atualizado_em = NOW()
        WHERE id = %s
        RETURNING *;
    """
 
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql, (id_produto,))
            return cursor.fetchone()
 
def reativar_produto(id_produto):
    sql = """
        UPDATE produtos
        SET ativo = TRUE,
            atualizado_em = NOW()
        WHERE id = %s
        RETURNING *;
    """
 
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql, (id_produto,))
            return cursor.fetchone()

# CARACTERISTICAS DO PRODUTO

def criar_caracteristica(dados):
    sql = """
        INSERT INTO caracteristicas_produto
            (produto_id, nome, valor)
        VALUES (%s, %s, %s)
        RETURNING *;
    """
 
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(
                sql,
                (dados.produto_id, dados.nome.strip(), dados.valor.strip()),
            )
            return cursor.fetchone()
 
def listar_caracteristicas(id_produto):
    sql = """
        SELECT *
        FROM caracteristicas_produto
        WHERE produto_id = %s
        ORDER BY nome;
    """
 
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql, (id_produto,))
            return cursor.fetchall()
 
def excluir_caracteristica(id_caracteristica):
    sql = """
        DELETE FROM caracteristicas_produto
        WHERE id = %s
        RETURNING *;
    """
 
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql, (id_caracteristica,))
            return cursor.fetchone()

# ENDEREÇOS

def criar_endereco(dados):
    sql = """
        INSERT INTO enderecos
            (cliente_id, destinatario, cep, numero, complemento,
             bairro, cidade, estado, principal)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s,
             %s OR NOT EXISTS (SELECT 1 FROM enderecos 
             WHERE cliente_id = %s AND ativo))
        RETURNING *;
    """

    parametros = (
        dados.cliente_id,
        dados.destinatario.strip(),
        dados.cep,
        dados.numero.strip(),
        dados.complemento,
        dados.bairro.strip(),
        dados.cidade.strip(),
        dados.estado.strip(),
        dados.principal,
        dados.cliente_id,
    )

    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            if dados.principal:
                cursor.execute(dados.cliente_id)
            cursor.execute(sql, parametros)
            return cursor.fetchone()

def listar_enderecos(id_cliente, apenas_ativos=True):
    sql = (
        "SELECT * FROM enderecos WHERE cliente_id = %s "
        "AND (%s = FALSE OR ativo) ORDER BY principal DESC;"
    )

    parametros = (
        id_cliente,
        apenas_ativos
    )
 
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql, parametros)
            return cursor.fetchall()

def atualizar_endereco(id_endereco,dados):
    sql = """
        UPDATE enderecos
        SET destinatario = (%s, destinatario),
            cep = (%s, cep),
            numero = (%s, numero),
            complemento = (%s, complemento),
            bairro = (%s, bairro),
            cidade = (%s, cidade),
            estado = (%s, estado)
        WHERE id = %s
        RETURNING *;
    """

    parametros = (
        dados.destinatario.strip() if dados.destinatario else None,
        dados.cep,
        dados.numero.strip() if dados.numero else None,
        dados.complemento,
        dados.bairro.strip() if dados.bairro else None,
        dados.cidade.strip() if dados.cidade else None,
        dados.estado.strip() if dados.estado else None,
        id_endereco,
    )
    
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql, parametros)
            return cursor.fetchone()

def definir_endereco_principal(id_endereco):
    sql_cliente = """
        SELECT cliente_id
        FROM enderecos
        WHERE id = %s AND ativo;
    """
    sql_principal_false = """
        UPDATE enderecos
        SET principal = FALSE
        WHERE cliente_id = %s AND principal;
    """
    sql_principal_true = """
        UPDATE enderecos
        SET principal = TRUE
        WHERE id = %s
        RETURNING *;
    """

    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql_cliente, (id_endereco,))
            endereco = cursor.fetchone()
            if endereco is None:
                return None
            cursor.execute(sql_principal_false, (endereco["cliente_id"],))
            cursor.execute(sql_principal_true, (id_endereco,))
            return cursor.fetchone()

def desativar_endereco(id_endereco):
    sql = """
        UPDATE enderecos
        SET ativo = FALSE,
            principal = FALSE
        WHERE id = %s
        RETURNING *;
    """

    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql, (id_endereco,))
            return cursor.fetchone()

def reativar_endereco(id_endereco):
    sql = """
        UPDATE enderecos
        SET ativo = TRUE
        WHERE id = %s
        RETURNING *;
    """
 
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql, (id_endereco,))
            return cursor.fetchone()

# AUXILIARES CRIAR PEDIDO

def _validar_cliente_pedido(cursor, cliente_id: int):
    cursor.execute("SELECT id, ativo FROM clientes WHERE id = %s;", (cliente_id,))
    cliente = cursor.fetchone()
    
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    
    if not cliente["ativo"]:
        raise HTTPException(status_code=400, detail="Cliente inativo não pode realizar pedidos.")

def _validar_endereco_pedido(cursor, endereco_id: int, cliente_id: int):
    cursor.execute(
        "SELECT * FROM enderecos WHERE id = %s AND cliente_id = %s AND ativo;",
        (endereco_id, cliente_id),
    )
    endereco = cursor.fetchone()
    if endereco is None:
        raise HTTPException(
            status_code=400,
            detail="Endereço inválido, inativo ou não pertence ao cliente informado.",
        )
    return endereco

def _validar_e_calcular_itens(cursor, itens):
    itens_ordenados = sorted(itens, key=lambda x: x.produto_id)
    itens_validados = []
    valor_total = Decimal("0.00")

    for item in itens_ordenados:
        cursor.execute(
            """
            SELECT p.id, p.nome, p.preco_atual, p.ativo, e.quantidade_disponivel
            FROM produtos p
            INNER JOIN estoque e ON e.produto_id = p.id
            WHERE p.id = %s
            FOR UPDATE OF e;
            """,
            (item.produto_id,),
        )
        produto = cursor.fetchone()
        if produto is None:
            raise HTTPException(status_code=404, detail=f"Produto {item.produto_id} não encontrado.")
        if not produto["ativo"]:
            raise HTTPException(
                status_code=400,
                detail=f"Produto '{produto['nome']}' está inativo e não pode ser pedido.",
            )
        if produto["quantidade_disponivel"] < item.quantidade:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Estoque insuficiente para '{produto['nome']}'. "
                    f"Disponível: {produto['quantidade_disponivel']}, solicitado: {item.quantidade}."
                ),
            )

        valor_total += produto["preco_atual"] * item.quantidade
        itens_validados.append({
            "produto_id": item.produto_id,
            "quantidade": item.quantidade,
            "preco_unitario": produto["preco_atual"],
        })

    return itens_validados, valor_total

def _inserir_pedido_e_itens(cursor, cliente_id: int, endereco: dict, itens_validados: list, valor_total: Decimal) -> int:
    cursor.execute(
        """
        INSERT INTO pedidos (
            cliente_id, endereco_id, status, valor_total,
            entrega_destinatario, entrega_cep, entrega_numero,
            entrega_complemento, entrega_bairro, entrega_cidade, entrega_estado
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (
            cliente_id,
            endereco["id"],
            StatusPedido.AGUARDANDO_CONFIRMACAO.value,
            valor_total,
            endereco["destinatario"],
            endereco["cep"],
            endereco["numero"],
            endereco["complemento"],
            endereco["bairro"],
            endereco["cidade"],
            endereco["estado"],
        ),
    )
    id_pedido = cursor.fetchone()["id"]

    for item in itens_validados:
        cursor.execute(
            """
            INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)
            VALUES (%s, %s, %s, %s);
            """,
            (id_pedido, item["produto_id"], item["quantidade"], item["preco_unitario"]),
        )

    cursor.execute(
        """
        INSERT INTO historico_status_pedido (pedido_id, status_anterior, status_novo, observacao)
        VALUES (%s, NULL, %s, 'Pedido criado');
        """,
        (id_pedido, StatusPedido.AGUARDANDO_CONFIRMACAO.value),
    )
    return id_pedido

# AUXILIARES ATUALIZAR STATUS

def _buscar_itens_pedido(cursor, id_pedido: int):
    cursor.execute(
        """
        SELECT ip.produto_id, ip.quantidade, p.nome AS nome_produto
        FROM itens_pedido ip
        INNER JOIN produtos p ON p.id = ip.produto_id
        WHERE ip.pedido_id = %s
        ORDER BY ip.produto_id;
        """,
        (id_pedido,),
    )
    return cursor.fetchall()

def _baixar_estoque_confirmacao(cursor, id_pedido: int, itens: list):
    for item in itens:
        cursor.execute(
            """
            SELECT quantidade_disponivel
            FROM estoque
            WHERE produto_id = %s
            FOR UPDATE;
            """,
            (item["produto_id"],),
        )
        est = cursor.fetchone()
        if est["quantidade_disponivel"] < item["quantidade"]:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Estoque insuficiente para confirmar '{item['nome_produto']}'. "
                    f"Disponível: {est['quantidade_disponivel']}, necessário: {item['quantidade']}."
                ),
            )

        cursor.execute(
            """
            UPDATE estoque
            SET quantidade_disponivel = quantidade_disponivel - %s,
                atualizado_em = NOW()
            WHERE produto_id = %s;
            """,
            (item["quantidade"], item["produto_id"]),
        )
        cursor.execute(
            """
            INSERT INTO movimentacoes_estoque
                (produto_id, pedido_id, tipo, quantidade, observacao)
            VALUES (%s, %s, %s, %s, %s);
            """,
            (
                item["produto_id"],
                id_pedido,
                TipoMovimentacao.SAIDA_VENDA.value,
                item["quantidade"],
                f"Baixa por confirmação do pedido #{id_pedido}",
            ),
        )

def _estornar_estoque_cancelamento(cursor, id_pedido: int, itens: list):
    for item in itens:
        cursor.execute(
            """
            UPDATE estoque
            SET quantidade_disponivel = quantidade_disponivel + %s,
                atualizado_em = NOW()
            WHERE produto_id = %s;
            """,
            (item["quantidade"], item["produto_id"]),
        )
        cursor.execute(
            """
            INSERT INTO movimentacoes_estoque
                (produto_id, pedido_id, tipo, quantidade, observacao)
            VALUES (%s, %s, %s, %s, %s);
            """,
            (
                item["produto_id"],
                id_pedido,
                TipoMovimentacao.ESTORNO_CANCELAMENTO.value,
                item["quantidade"],
                f"Estorno por cancelamento do pedido #{id_pedido}",
            ),
        )

def _aplicar_transicao_pedido(cursor, id_pedido: int, status_atual: StatusPedido, dados):
    novo_status = dados.status
    itens = _buscar_itens_pedido(cursor, id_pedido)

    if novo_status == StatusPedido.CONFIRMADO:
        _baixar_estoque_confirmacao(cursor, id_pedido, itens)
        cursor.execute(
            "UPDATE pedidos SET status = %s, data_confirmacao = NOW() WHERE id = %s;",
            (novo_status.value, id_pedido),
        )

    elif novo_status == StatusPedido.ENVIADO:
        cursor.execute(
            "UPDATE pedidos SET status = %s, data_envio = NOW() WHERE id = %s;",
            (novo_status.value, id_pedido),
        )

    elif novo_status == StatusPedido.ENTREGUE:
        cursor.execute(
            "UPDATE pedidos SET status = %s, data_entrega = NOW() WHERE id = %s;",
            (novo_status.value, id_pedido),
        )

    elif novo_status == StatusPedido.CANCELADO:
        if status_atual == StatusPedido.CONFIRMADO:
            _estornar_estoque_cancelamento(cursor, id_pedido, itens)
        cursor.execute(
            """
            UPDATE pedidos
            SET status = %s, data_cancelamento = NOW(), motivo_cancelamento = %s
            WHERE id = %s;
            """,
            (novo_status.value, dados.motivo_cancelamento.strip(), id_pedido),
        )

# PEDIDOS

def _montar_pedido_completo(cursor, id_pedido: int):
    cursor.execute("SELECT * FROM pedidos WHERE id = %s;", (id_pedido,))
    pedido = cursor.fetchone()
    if pedido is None:
        return None

    cursor.execute(
        """
        SELECT
            ip.id,
            ip.produto_id,
            p.nome AS nome_produto,
            ip.quantidade,
            ip.preco_unitario,
            (ip.quantidade * ip.preco_unitario) AS subtotal
        FROM itens_pedido ip
        INNER JOIN produtos p ON p.id = ip.produto_id
        WHERE ip.pedido_id = %s
        ORDER BY ip.id;
        """,
        (id_pedido,),
    )
    pedido["itens"] = cursor.fetchall()
    return pedido

def listar_pedidos(
    status_pedido: StatusPedido | None = None,
    cliente_id: int | None = None,
    data_inicio=None,
    data_fim=None,
    offset: int = 0,
    limit: int = 10,
):
    filtros = []
    parametros = []

    if status_pedido is not None:
        filtros.append("p.status = %s")
        parametros.append(status_pedido.value)
    if cliente_id is not None:
        filtros.append("p.cliente_id = %s")
        parametros.append(cliente_id)
    if data_inicio is not None:
        filtros.append("p.data_pedido >= %s")
        parametros.append(data_inicio)
    if data_fim is not None:
        filtros.append("p.data_pedido <= %s")
        parametros.append(data_fim)

    where_clause = (" WHERE " + " AND ".join(filtros)) if filtros else ""

    sql_total = f"SELECT COUNT(*) AS total FROM pedidos p {where_clause};"

    sql_dados = f"""
        SELECT
            p.id,
            p.cliente_id,
            c.nome AS cliente_nome,
            p.status,
            p.data_pedido,
            p.data_confirmacao,
            p.valor_total,
            COALESCE(SUM(ip.quantidade), 0) AS total_itens
        FROM pedidos p
        INNER JOIN clientes c ON c.id = p.cliente_id
        LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
        {where_clause}
        GROUP BY p.id, c.nome
        ORDER BY p.data_pedido DESC, p.id DESC
        OFFSET %s LIMIT %s;
    """

    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute(sql_total, parametros)
            total = cursor.fetchone()["total"]

            cursor.execute(sql_dados, parametros + [offset, limit])
            itens = cursor.fetchall()

            return {
                "total": total,
                "offset": offset,
                "limit": limit,
                "itens": itens,
            }

def buscar_pedido(id_pedido: int):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            return _montar_pedido_completo(cursor, id_pedido)

def listar_historico_pedido(id_pedido: int):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute("SELECT id FROM pedidos WHERE id = %s;", (id_pedido,))
            if cursor.fetchone() is None:
                return None

            cursor.execute(
                """
                SELECT *
                FROM historico_status_pedido
                WHERE pedido_id = %s
                ORDER BY data_hora ASC, id ASC;
                """,
                (id_pedido,),
            )
            return cursor.fetchall()

def criar_pedido(dados):
    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            _validar_cliente_pedido(cursor, dados.cliente_id)
            endereco = _validar_endereco_pedido(cursor, dados.endereco_id, dados.cliente_id)
            itens_validados, valor_total = _validar_e_calcular_itens(cursor, dados.itens)
            id_pedido = _inserir_pedido_e_itens(
                cursor, dados.cliente_id, endereco, itens_validados, valor_total
            )
            return _montar_pedido_completo(cursor, id_pedido)

def atualizar_status_pedido(id_pedido: int, dados):
    novo_status = dados.status

    with get_db_connection() as connection:
        with get_db_cursor(connection) as cursor:
            cursor.execute("SELECT * FROM pedidos WHERE id = %s FOR UPDATE;", (id_pedido,))
            pedido = cursor.fetchone()
            if pedido is None:
                raise HTTPException(status_code=404, detail="Pedido não encontrado.")

            status_atual = StatusPedido(pedido["status"])
            if novo_status not in TRANSICOES_PERMITIDAS[status_atual]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Transição inválida de '{status_atual.value}' para '{novo_status.value}'.",
                )

            if novo_status == StatusPedido.CANCELADO and not (dados.motivo_cancelamento or "").strip():
                raise HTTPException(status_code=400, detail="O motivo do cancelamento é obrigatório.")

            _aplicar_transicao_pedido(cursor, id_pedido, status_atual, dados)

            obs = dados.observacao or dados.motivo_cancelamento
            cursor.execute(
                """
                INSERT INTO historico_status_pedido
                    (pedido_id, status_anterior, status_novo, observacao)
                VALUES (%s, %s, %s, %s);
                """,
                (id_pedido, status_atual.value, novo_status.value, obs),
            )

            return _montar_pedido_completo(cursor, id_pedido)