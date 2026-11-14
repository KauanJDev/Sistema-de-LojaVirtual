from fastapi import APIRouter, Query

from services import crud
from services.erro import erro_404
from app.models.EnderecoModel import EnderecoCreate, EnderecoSaida, EnderecoUpdate

router = APIRouter(prefix="/enderecos", tags=["Enderecos"])
router_do_cliente = APIRouter(prefix="/clientes", tags=["Enderecos do Cliente"])

@router.post("", response_model=EnderecoSaida, status_code=201)
def criar_endereco(dados: EnderecoCreate):
    return crud.criar_endereco(dados)

@router.patch("/{id_endereco}", response_model=EnderecoSaida)
def atualizar_endereco(id_endereco: int, dados: EnderecoUpdate):
    return erro_404(crud.atualizar_endereco(id_endereco, dados), "Endereco não encontrado")

@router.post("/{id_endereco}/principal", response_model=EnderecoSaida)
def definir_endereco_principal(id_endereco: int):
    return erro_404(crud.definir_endereco_principal(id_endereco), "Endereco não encontrado ou não é o ativo")

@router.delete("/{id_endereco}", response_model=EnderecoSaida)
def desativar_endereco(id_endereco: int):
    return erro_404(crud.desativar_endereco(id_endereco), "Endereco não encontrado")

@router.post("/{id_endereco}/reativar", response_model=EnderecoSaida)
def reativar_endereco(id_endereco: int):
    return erro_404(crud.reativar_endereco(id_endereco), "Endereco não encontrado")

@router_do_cliente.get("/{id_cliente}/enderecos", response_model=list[EnderecoSaida])
def listar_enderecos(id_cliente: int, apenas_ativos: bool = True):
    erro_404(crud.buscar_cliente(id_cliente), "Cliente não encontrado")
    return crud.listar_enderecos(id_cliente, apenas_ativos)
