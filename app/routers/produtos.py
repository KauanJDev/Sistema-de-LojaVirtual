from fastapi import APIRouter, Query

from services import crud
from services.erro import erro_404
from app.models.ProdutoModel import ProdutoCreate, ProdutoSaida, ProdutoUpdate

router = APIRouter(prefix="/produtos", tags=["Produtos"])

@router.post("", response_model=ProdutoSaida, status_code=201)
def criar_produto(dados: ProdutoCreate):
    return crud.criar_produto(dados)

@router.get("", response_model=list[ProdutoSaida])
def listar_produtos(
    busca: str | None = Query(default=None, description="Procura pelo nome"),
    categoria_id: int | None = None,
    apenas_ativos: bool = True,
    apenas_disponiveis: bool = False,
):
    return crud.listar_produtos(busca, categoria_id, apenas_ativos, apenas_disponiveis)

@router.get("/{id_produto}", response_model=ProdutoSaida)
def buscar_produto(id_produto: int):
    return erro_404(crud.buscar_produto(id_produto), "Produto não encontrado")

@router.patch("/{id_produto}", response_model=ProdutoSaida)
def atualizar_produto(id_produto: int, dados: ProdutoUpdate):
    return erro_404(crud.atualizar_produto(id_produto, dados), "Produto não encontrado")

@router.delete("/{id_produto}", response_model=ProdutoSaida, summary="Desativar produtos")
def desativar_produto(id_produto: int):
    erro_404(crud.desativar_produto(id_produto), "Produto não encontrado")
    return crud.buscar_produto(id_produto)

@router.post("/{id_produto}/reativar", response_model=ProdutoSaida)
def reativar_produto(id_produto: int):
    erro_404(crud.reativar_produto(id_produto), "Produto não encontrado")
    return crud.buscar_produto(id_produto)


