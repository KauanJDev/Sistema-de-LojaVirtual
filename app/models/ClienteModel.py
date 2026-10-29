from datetime import datetime
from pydantic import BaseModel, Field

class ClienteCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=150)
    telefone: str | None = Field(default=None, max_length=20)
    cpf: str = Field(default=None)

class ClienteUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=150)
    telefone: str | None = Field(default=None, max_length=20)
    cpf: str = Field(default=None)
    ativo: bool | None = None

class ClienteRead(BaseModel):
    id: int
    nome: str
    email: str
    telefone: str | None
    cpf: str
    ativo: bool
    criado_em: datetime