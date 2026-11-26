from datetime import datetime

from fastapi import APIRouter

from app.services import crud
from app.services.erro import erro_404

from app.models.Enums import StatusPedido
from app.schemas.PedidoModel import (
    HistoricoStatusSaida,
    PedidoCreate,
    PedidoResumoSaida,
    PedidoSaida,
    PedidoStatusUpdate,
)

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])

@router.get("/filtro/periodo")
def relatorio_periodo(p_comeco: datetime, p_fim: datetime):
    return crud.relatorio_por_periodo(p_comeco, p_fim)

@router.get("/filtro/produto/{id}")
def relatorio_por_produto(produto_id: int):
    return crud.relatorio_por_produto(produto_id)

@router.get("/ranking")
def ranking_vendas(limit: int):
    return crud.ranking_de_vendas(limit)
