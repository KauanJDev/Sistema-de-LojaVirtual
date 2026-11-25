from datetime import datetime
from decimal import Decimal
from .Base import Base
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

class Produto(Base):
    __tablename__ = "produtos"
    __table_args__ = (
        CheckConstraint("preco_atual >= 0"),
        Index("index_produtos_categoria", "categoria_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias.id"))
    nome: Mapped[str] = mapped_column(String(100))
    descricao: Mapped[str | None] = mapped_column(Text)
    preco_atual: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    ativo: Mapped[bool] = mapped_column(server_default=true())
    criado_em: Mapped[datetime] = mapped_column(server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(server_default=func.now())

class CaracteristicaProduto(Base):
    __tablename__ = "caracteristicas_produto"
    __table_args__ = (UniqueConstraint("produto_id", "nome"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id", ondelete="CASCADE")
    )
    nome: Mapped[str] = mapped_column(String(60))
    valor: Mapped[str] = mapped_column(String(255))