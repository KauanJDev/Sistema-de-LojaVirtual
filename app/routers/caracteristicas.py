from fastapi import APIRouter

from app.services import crud
from app.services.erro import erro_404
from app.models.ProdutoModel import CaracteristicaProdutoCreate

router = APIRouter(prefix="/caracteristicas", tags=["Caracteristicas"])
router_do_produto = APIRouter(prefix="/produtos", tags=["Caracteristicas"])

@router.post("", status_code=201)
def criar_caracteristica(dados: CaracteristicaProdutoCreate):
    return crud.criar_caracteristica(dados)

@router.delete("/{id_caracteristica}")
def excluir_caracteristica(id_caracteristica: int):
    return erro_404(crud.excluir_caracteristica(id_caracteristica), "Caracteristica não encontrada")

@router_do_produto.get("/{id_produto}/caracteristicas")
def listar_caracteristicas(id_produto: int):
    erro_404(crud.buscar_produto(id_produto), "Produto não encontrado")
    return crud.listar_caracteristicas(id_produto)
