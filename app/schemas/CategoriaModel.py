from pydantic import BaseModel, Field

class CategoriaCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    descricao: str | None = Field(default=None, max_length=255)

class CategoriaUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    descricao: str | None = Field(default=None, max_length=255)
    ativa: bool | None = None