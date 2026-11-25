from datetime import datetime
from sqlalchemy import CheckConstraint, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column
from .Base import Base

class Estoque(Base):
    __tablename__ = "estoque"
    __table_args__ = (CheckConstraint("quantidade_disponivel >= 0"),)

    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), primary_key=True)
    quantidade_disponivel: Mapped[int] = mapped_column(server_default="0")
    atualizado_em: Mapped[datetime] = mapped_column(server_default=func.now())

class MovimentacaoEstoque(Base):
    __tablename__ = "movimentacoes_estoque"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('ENTRADA', 'SAIDA_VENDA', 'ESTORNO_CANCELAMENTO', 'AJUSTE')"
        ),
        CheckConstraint(
            " quantidade <> 0 AND (tipo = 'AJUSTE' OR quantidade > 0) ",
            name="check_mov_quantidade",
        ),
        CheckConstraint(
            " tipo NOT IN ('SAIDA_VENDA', 'ESTORNO_CANCELAMENTO') OR pedido_id IS NOT NULL ",
            name="check_mov_pedido",
        ),
        Index("index_mov_estoque_produto", "produto_id", "data_hora"),
        Index("index_mov_estoque_pedido", "pedido_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"))
    pedido_id: Mapped[int | None] = mapped_column(ForeignKey("pedidos.id"))
    tipo: Mapped[str] = mapped_column(String(30))
    quantidade: Mapped[int] = mapped_column()
    data_hora: Mapped[datetime] = mapped_column(server_default=func.now())
    observacao: Mapped[str | None] = mapped_column(String(255))