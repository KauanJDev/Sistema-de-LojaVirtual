from datetime import datetime
from sqlalchemy import String, func, true
from sqlalchemy.orm import Mapped, mapped_column
from .Base import Base

class Cliente(Base):
    __tablename__ = "clientes"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True)
    cpf: Mapped[str] = mapped_column(String(14), unique=True)
    telefone: Mapped[str | None] = mapped_column(String(20))
    ativo: Mapped[bool] = mapped_column(server_default=true())
    criado_em: Mapped[datetime] = mapped_column(server_default=func.now())