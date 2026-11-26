from sqlalchemy import ForeignKey, Index, String, false, text, true
from sqlalchemy.orm import Mapped, mapped_column
from .Base import Base

class Endereco(Base):
    __tablename__ = "enderecos"
    __table_args__ = (
        Index(
            "unique_enderecos_principal",
            "cliente_id",
            unique=True,
            postgresql_where=text("principal AND ativo"),
            sqlite_where=text("principal AND ativo"),
        ),
        Index("index_enderecos_cliente", "cliente_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"))
    destinatario: Mapped[str] = mapped_column(String(100))
    cep: Mapped[str] = mapped_column(String(9))
    numero: Mapped[str] = mapped_column(String(10))
    complemento: Mapped[str | None] = mapped_column(String(60))
    bairro: Mapped[str] = mapped_column(String(60))
    cidade: Mapped[str] = mapped_column(String(60))
    estado: Mapped[str] = mapped_column(String(50))
    principal: Mapped[bool] = mapped_column(server_default=false())
    ativo: Mapped[bool] = mapped_column(server_default=true())