from fastapi import APIRouter, Query
from app.models.Enums import TipoMovimentacao
from app.cruds import crud_estoque as crud
from app.services.erro import erro_404

router = APIRouter(prefix="/estoque", tags=["Estoque"])

@router.get("{produto_id}/estoque", include_in_schema=False)
@router.get("/{produto_id}/estoque")
def visualizar_estoque_do_produto(produto_id: int):
    registros = crud.listar_estoque(produto_id)
    return erro_404(registros or None, "Estoque do produto nao encontrado")

@router.get("/{produto_id}/qtd_disponivel")
def obter_quantidade_disponivel(produto_id: int):
    return erro_404(crud.quantidade_disponivel(produto_id), "Estoque do produto nao encontrado")

@router.patch("/{produto_id}/repor")
def repor_estoque(produto_id: int, qtd_adicional: int = Query(gt=0)):
    return crud.alterar_estoque(produto_id, qtd_adicional, TipoMovimentacao.ENTRADA)

@router.patch("/{produto_id}/editar_qtd")
def editar_estoque(produto_id: int, qtd_nova: int = Query(ge=0)):
    return crud.alterar_estoque(produto_id, qtd_nova, TipoMovimentacao.AJUSTE)

@router.get("/movimentações")
def visualizar_movimentacoes(produto_id: int | None = None, tipo: str | None = None):
    return crud.listar_movimentacoes(produto_id, tipo)
