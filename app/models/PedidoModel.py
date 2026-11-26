from datetime import datetime
from decimal import Decimal
from .Base import Base
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

class Pedido(Base):
    __tablename__ = "pedidos"
    __table_args__ = (
        CheckConstraint(
            "status IN ('AGUARDANDO_CONFIRMACAO', 'CONFIRMADO', 'ENVIADO', 'ENTREGUE', 'CANCELADO')"
        ),
        CheckConstraint("valor_total >= 0"),
        CheckConstraint(
            " status NOT IN ('CONFIRMADO', 'ENVIADO', 'ENTREGUE') OR data_confirmacao IS NOT NULL ",
            name="check_pedidos_data_confirmacao",
        ),
        Index("index_pedidos_cliente", "cliente_id"),
        Index("index_pedidos_status_confirmacao", "status", "data_confirmacao"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"))
    endereco_id: Mapped[int | None] = mapped_column(ForeignKey("enderecos.id"))
    status: Mapped[str] = mapped_column(
        String(30), server_default="AGUARDANDO_CONFIRMACAO"
    )
    data_pedido: Mapped[datetime] = mapped_column(server_default=func.now())
    data_confirmacao: Mapped[datetime | None] = mapped_column()
    data_envio: Mapped[datetime | None] = mapped_column()
    data_entrega: Mapped[datetime | None] = mapped_column()
    data_cancelamento: Mapped[datetime | None] = mapped_column()
    motivo_cancelamento: Mapped[str | None] = mapped_column(String(255))
    valor_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), server_default="0")
    entrega_destinatario: Mapped[str] = mapped_column(String(100))
    entrega_cep: Mapped[str] = mapped_column(String(9))
    entrega_numero: Mapped[str] = mapped_column(String(10))
    entrega_complemento: Mapped[str | None] = mapped_column(String(60))
    entrega_bairro: Mapped[str] = mapped_column(String(60))
    entrega_cidade: Mapped[str] = mapped_column(String(60))
    entrega_estado: Mapped[str] = mapped_column(String(50))


class ItemPedido(Base):
    __tablename__ = "itens_pedido"
    __table_args__ = (
        CheckConstraint("quantidade > 0"),
        CheckConstraint("preco_unitario >= 0"),
        UniqueConstraint("pedido_id", "produto_id"),
        Index("idx_itens_pedido_produto", "produto_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"))
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"))
    quantidade: Mapped[int] = mapped_column()
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))


class HistoricoStatusPedido(Base):
    __tablename__ = "historico_status_pedido"
    __table_args__ = (
        CheckConstraint(
            "status_anterior IS NULL OR status_anterior IN ( 'AGUARDANDO_CONFIRMACAO', 'CONFIRMADO', 'ENVIADO', 'ENTREGUE', 'CANCELADO')"
        ),
        CheckConstraint(
            "status_novo IN ( 'AGUARDANDO_CONFIRMACAO', 'CONFIRMADO', 'ENVIADO', 'ENTREGUE', 'CANCELADO')"
        ),
        Index("idx_historico_pedido", "pedido_id", "data_hora"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"))
    status_anterior: Mapped[str | None] = mapped_column(String(30))
    status_novo: Mapped[str] = mapped_column(String(30))
    data_hora: Mapped[datetime] = mapped_column(server_default=func.now())
    observacao: Mapped[str | None] = mapped_column(String(255))