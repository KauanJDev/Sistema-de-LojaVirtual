from pydantic import BaseModel, Field

class EnderecoCreate(BaseModel):
    cliente_id: int = Field(gt=0)
    destinatario: str = Field(min_length=1, max_length=100)
    cep: str = Field(min_length=8, max_length=9)
    numero: str = Field(min_length=1, max_length=10)
    complemento: str | None = Field(default=None, max_length=60)
    bairro: str = Field(min_length=1, max_length=60)
    cidade: str = Field(min_length=1, max_length=60)
    estado: str = Field(min_length=1, max_length=50)
    principal: bool = False

class EnderecoUpdate(BaseModel):
    destinatario: str | None = Field(default=None, min_length=1, max_length=100)
    cep: str | None = Field(default=None, min_length=8, max_length=9)
    numero: str | None = Field(default=None, min_length=1, max_length=10)
    complemento: str | None = Field(default=None, max_length=60)
    bairro: str | None = Field(default=None, min_length=1, max_length=60)
    cidade: str | None = Field(default=None, min_length=1, max_length=60)
    estado: str | None = Field(default=None, min_length=1, max_length=50)
    principal: bool | None = None
    ativo: bool | None = None

class EnderecoRead(BaseModel):
    id: int
    cliente_id: int
    destinatario: str
    cep: str
    numero: str
    complemento: str | None
    bairro: str
    cidade: str
    estado: str
    principal: bool
    ativo: bool