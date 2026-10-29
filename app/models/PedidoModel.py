from pydantic import BaseModel, Field, model_validator
from .Enums import StatusPedido

class ItemPedidoCreate(BaseModel):
    produto_id: int = Field(gt=0)
    quantidade: int = Field(gt=0)  # RN03

class PedidoCreate(BaseModel):
    cliente_id: int = Field(gt=0)
    endereco_id: int = Field(gt=0)
    itens: list[ItemPedidoCreate] = Field(min_length=1)  # RN04

    @model_validator(mode="after")
    def sem_produto_repetido(self):
        indice = [item.produto_id for item in self.itens]
        if len(indice) != len(set(indice)):
            raise ValueError("Não é permitido produtos repetidos no pedido")
        return self

class PedidoStatusUpdate(BaseModel):
    status: StatusPedido
    motivo_cancelamento: str | None = Field(default=None, max_length=255)
    observacao: str | None = Field(default=None, max_length=255)