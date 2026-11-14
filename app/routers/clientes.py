from fastapi import APIRouter, Query

from app.services import crud
from app.services.erro import erro_404
from app.models.ClienteModel import ClienteCreate, ClienteSaida, ClienteUpdate

router = APIRouter(prefix="/clientes", tags=["Clientes"])

@router.post("", response_model=ClienteSaida, status_code=201)
def criar_cliente(dados: ClienteCreate):
    return crud.criar_cliente(dados)

@router.get("", response_model=list[ClienteSaida])
def listar_clientes(
    busca: str | None = Query(default=None, description="Procura pelo nome ou email"),
    apenas_ativos: bool = True,
):
    return crud.listar_clientes(busca, apenas_ativos)

@router.get("/{id_cliente}", response_model=ClienteSaida)
def buscar_cliente(id_cliente: int):
    return erro_404(crud.buscar_cliente(id_cliente), "Cliente não encontrado")

@router.patch("/{id_cliente}", response_model=ClienteSaida)
def atualizar_cliente(id_cliente: int, dados: ClienteUpdate):
    return erro_404(crud.atualizar_cliente(id_cliente, dados), "Cliente não encontrado")

@router.delete("/{id_cliente}", response_model=ClienteSaida, summary="Desativar cliente")
def desativar_cliente(id_cliente: int):
    return erro_404(crud.desativar_cliente(id_cliente), "Cliente não encontrado")

@router.post("/{id_cliente}/reativar", response_model=ClienteSaida)
def reativar_cliente(id_cliente: int):
    return erro_404(crud.reativar_cliente(id_cliente), "Cliente não encontrado")
