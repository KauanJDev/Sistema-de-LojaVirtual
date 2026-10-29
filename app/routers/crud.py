from db.db import get_db_connection, get_db_cursor

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

    filtros = []
    parametros = []

    busca = (busca or "").strip()

    if apenas_ativos:
        filtros.append("ativo")
    if busca:
        filtros.append("(nome ILIKE %s OR email ILIKE %s)")
        padrao = f"%{busca}%"
        parametros += [padrao, padrao]

    sql = "SELECT * FROM clientes"
    if filtros:
        sql += " WHERE " + " AND ".join(filtros)
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
    #COALESCE retorna o primeiro valor não nulo.
    sql = """
        UPDATE clientes
        SET nome = COALESCE(%s, nome),
            email = COALESCE(%s, email),
            cpf = COALESCE(%s, cpf),
            telefone = COALESCE(%s, telefone),
            ativo = COALESCE(%s, ativo)
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
        COALESCE(e.quantidade_disponivel, 0) AS quantidade_disponivel,
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
    #COALESCE retorna o primeiro valor não nulo.
    sql = """
        UPDATE produtos
        SET categoria_id = COALESCE(%s, categoria_id),
            nome = COALESCE(%s, nome),
            descricao = COALESCE(%s, descricao),
            preco_atual = COALESCE(%s, preco_atual),
            ativo = COALESCE(%s, ativo),
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

# CARACTERÍSTICAS DO PRODUTO

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

# VOU FAZER CRUD DE ENDEREÇOS AINDA...