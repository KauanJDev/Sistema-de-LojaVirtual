from fastapi import APIRouter

from services import crud
from app.models.CategoriaModel import CategoriaCreate

router = APIRouter(prefix="/categorias", tags=["Categorias"])

@router.post("", status_code=201)
def criar_categoria(dados: CategoriaCreate):
    return crud.criar_categoria(dados)

@router.get("", status_code=200)
def listar_categorias(apenas_ativas: bool = True):
    return crud.listar_categorias(apenas_ativas)

