from fastapi import APIRouter, HTTPException, status
from db.db import get_db_connection, get_db_cursor


router = APIRouter (prefix="/estoque", tags=["Estoque"])

@router.get("/{produto_id}/qtd_disponivel", status_code=status.HTTP_200_OK)
def obter_quantidade_disponivel(produto_id: str):
    sql = """ 
        SELECT quantidade_disponivel
        FROM estoque
        WHERE produto_id = %s
    """

    try:
        with get_db_connection() as connection:
            with get_db_cursor(connection) as cursor:
                cursor.execute(sql, [produto_id])
                return cursor.fetchone()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar por quantidade disponível"
        )

@router.patch("/{produto_id}/repor_estoque")
def repor_estoque(produto_id: str, qtd_adicional: str):
    sql = """
        UPDATE estoque
        SET quantidade_disponivel = quantidade_disponivel + %s 
        WHERE produto_id = %s
    """

    parametros = [qtd_adicional, produto_id]

    try:
        with get_db_connection() as connection:
            with get_db_cursor(connection) as cursor:
                cursor.execute(sql, parametros)

                cursor.execute("""SELECT * FROM estoque WHERE produto_id = %s""", [produto_id])
                return cursor.fetchone()
    except Exception as e:
        raise HTTPException(status_code=500,
            detail=f"Erro ao salvar alterações {e}"
        )
