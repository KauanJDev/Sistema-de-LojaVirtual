from fastapi import APIRouter, HTTPException, status
from db.db import get_db_connection, get_db_cursor


router = APIRouter(prefix="/estoque", tags=["Estoque"])

@router.get("{produto_id}/estoque", status_code=status.HTTP_200_OK)
def visualizar_estoque():
    sql = """
        SELECT * FROM estoque
    """
    try:
        with get_db_connection() as connection:
            with get_db_cursor(connection) as cursor:
                cursor.execute(sql)

                return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Não foi possível exibir estoque: {e}"
        )
@router.get("/{produto_id}/qtd_disponivel", status_code=status.HTTP_200_OK)
def obter_quantidade_disponivel(produto_id: str):
    sql = """
        SELECT p.nome, e.quantidade_disponivel
        FROM estoque e, produtos p
        WHERE e.produto_id = %s
    """

    try:
        with get_db_connection() as connection:
            with get_db_cursor(connection) as cursor:
                cursor.execute(sql, [int(produto_id)])
                return cursor.fetchone()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar por quantidade disponível {e}"
        )


@router.patch("/{produto_id}/repor")
def repor_estoque(produto_id: str, qtd_adicional: str):
    sql = """
        UPDATE estoque
        SET quantidade_disponivel = quantidade_disponivel + %s
        WHERE produto_id = %s
    """

    movimentacao = """
        INSERT INTO movimentacoes_estoque
            (produto_id, tipo, quantidade, observacao)
        VALUES (%s, 'ENTRADA', %s, 'Reposição de estoque')
    """

    parametros = [qtd_adicional, produto_id]

    try:
        with get_db_connection() as connection:
            with get_db_cursor(connection) as cursor:
                cursor.execute(sql, parametros)
                cursor.execute(movimentacao, list(reversed(parametros)))

                cursor.execute("""SELECT * FROM estoque WHERE produto_id = %s""", [produto_id])
                return cursor.fetchone()
    except Exception as e:
        raise HTTPException(status_code=500,
            detail=f"Erro ao salvar alterações {e}"
        )


@router.patch("/{produto_id}/editar_qtd")
def editar_estoque(produto_id: str, qtd_nova: str):
    sql = """
        UPDATE estoque
        SET quantidade_disponivel = %s 
        WHERE produto_id = %s
    """

    movimentacao = """
        INSERT INTO movimentacoes_estoque
            (produto_id, tipo, quantidade, observacao)
        VALUES (%s, 'AJUSTE', %s, 'Ajuste no registro')
    """

    parametros = [qtd_nova, produto_id]

    try:
        with get_db_connection() as connection:
            with get_db_cursor(connection) as cursor:
                cursor.execute(sql, parametros)
                cursor.execute(movimentacao, list(reversed(parametros)))

                cursor.execute("""SELECT * FROM estoque WHERE produto_id = %s""", [produto_id])
                return cursor.fetchone()
    except Exception as e:
        raise HTTPException(status_code=500,
            detail=f"Erro ao salvar alterações {e}"
            )

@router.get("/movimentações")
def visualizar_movimentacoes(produto_id: str | None = None, tipo: str | None = None):
    sql = """
        SELECT * FROM
        movimentacoes_estoque
    """
    parametros = []

    if produto_id:
         sql += """
             WHERE produto_id = %s
         """
         parametros.append(produto_id)
    if tipo:
        if produto_id:
           sql += """ AND """
        else:
           sql += """ WHERE """
        sql += """ tipo = %s """
        parametros.append(tipo.upper())

    try:
        with get_db_connection() as connection:
            with get_db_cursor(connection) as cursor:
                if parametros != []:
                    cursor.execute(sql, parametros)
                else:
                    cursor.execute(sql)

                return {"result" : cursor.fetchall(), "query" : sql}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao ler tabela: {e}"
        )
