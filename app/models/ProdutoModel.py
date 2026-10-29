from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

class ProdutoCreate(BaseModel):
    categoria_id: int = Field(gt=0)
    nome: str = Field(min_length=1, max_length=100)
    descricao: str | None = None
    preco_atual: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    quantidade_inicial: int = Field(default=0, ge=0)

class ProdutoUpdate(BaseModel):
    categoria_id: int | None = Field(default=None, gt=0)
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    descricao: str | None = None
    preco_atual: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    ativo: bool | None = None

class ProdutoRead(BaseModel):
    id: int
    categoria_id: int
    categoria: str
    nome: str
    descricao: str | None
    preco_atual: Decimal
    ativo: bool
    quantidade_disponivel: int
    criado_em: datetime
    atualizado_em: datetime
    caracteristicas: dict[str, str] | None = None

class CaracteristicaProdutoCreate(BaseModel):
    produto_id: int = Field(gt=0)
    nome: str = Field(min_length=1, max_length=60)
    valor: str = Field(min_length=1, max_length=255)