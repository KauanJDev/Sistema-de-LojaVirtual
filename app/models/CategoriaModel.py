from sqlalchemy import String, true
from sqlalchemy.orm import Mapped, mapped_column
from .Base import Base

class Categoria(Base):
    __tablename__ = "categorias"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True)
    descricao: Mapped[str | None] = mapped_column(String(255))
    ativa: Mapped[bool] = mapped_column(server_default=true())
