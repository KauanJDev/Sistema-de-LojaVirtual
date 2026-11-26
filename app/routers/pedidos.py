from datetime import datetime
from fastapi import APIRouter, Query, status
from app.models.Enums import StatusPedido
from app.schemas.PedidoModel import (
    HistoricoStatusSaida,
    PedidoCreate,
    PedidoResumoSaida,
    PedidoSaida,
    PedidoStatusUpdate,
)
from app.cruds import crud_pedidos as crud
from app.services import erro

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])
router_do_cliente = APIRouter(prefix="/clientes", tags=["Pedidos"])

@router.post("", response_model=PedidoSaida, status_code=status.HTTP_201_CREATED)
def criar_pedido(dados: PedidoCreate):
    return crud.criar_pedido(dados)

@router.get("")
def listar_pedidos(
    status_pedido: StatusPedido | None = Query(default=None, alias="status"),
    cliente_id: int | None = Query(default=None, gt=0),
    data_inicio: datetime | None = Query(default=None),
    data_fim: datetime | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
):
    resultado = crud.listar_pedidos(
        status_pedido=status_pedido,
        cliente_id=cliente_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
        offset=offset,
        limit=limit,
    )
    resultado["itens"] = [PedidoResumoSaida(**item) for item in resultado["itens"]]
    return resultado

@router.get("/{id_pedido}", response_model=PedidoSaida)
def buscar_pedido(id_pedido: int):
    pedido = crud.buscar_pedido(id_pedido)
    return erro.erro_404(pedido, "Pedido não encontrado.")

@router.patch("/{id_pedido}/status", response_model=PedidoSaida)
def atualizar_status_pedido(id_pedido: int, dados: PedidoStatusUpdate):
    return crud.atualizar_status_pedido(id_pedido, dados)

@router.get("/{id_pedido}/historico", response_model=list[HistoricoStatusSaida])
def listar_historico_pedido(id_pedido: int):
    historico = crud.listar_historico_pedido(id_pedido)
    return erro.erro_404(historico, "Pedido não encontrado.")

@router_do_cliente.get("/{id_cliente}/pedidos")
def listar_pedidos_do_cliente(
    id_cliente: int,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
):
    cliente = crud.buscar_cliente(id_cliente)
    erro.erro_404(cliente, "Cliente não encontrado.")

    resultado = crud.listar_pedidos(
        cliente_id=id_cliente,
        offset=offset,
        limit=limit,
    )
    resultado["itens"] = [PedidoResumoSaida(**item) for item in resultado["itens"]]
    return resultado