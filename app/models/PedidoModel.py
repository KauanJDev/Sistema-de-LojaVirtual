from datetime import datetime
from decimal import Decimal
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

class ItemPedidoSaida(BaseModel):
    id: int
    produto_id: int
    nome_produto: str
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal

class HistoricoStatusSaida(BaseModel):
    id: int
    pedido_id: int
    status_anterior: StatusPedido | None
    status_novo: StatusPedido
    data_hora: datetime
    observacao: str | None

class PedidoSaida(BaseModel):
    id: int
    cliente_id: int
    endereco_id: int | None
    status: StatusPedido
    data_pedido: datetime
    data_confirmacao: datetime | None
    data_envio: datetime | None
    data_entrega: datetime | None
    data_cancelamento: datetime | None
    motivo_cancelamento: str | None
    valor_total: Decimal
    entrega_destinatario: str
    entrega_cep: str
    entrega_numero: str
    entrega_complemento: str | None
    entrega_bairro: str
    entrega_cidade: str
    entrega_estado: str
    itens: list[ItemPedidoSaida]

class PedidoResumoSaida(BaseModel):
    id: int
    cliente_id: int
    cliente_nome: str
    status: StatusPedido
    data_pedido: datetime
    data_confirmacao: datetime | None
    valor_total: Decimal
    total_itens: int