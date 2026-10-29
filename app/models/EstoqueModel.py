from typing import Literal

from pydantic import BaseModel, Field, model_validator


class MovimentacaoEstoqueCreate(BaseModel):
    produto_id: int = Field(gt=0)
    tipo: Literal["ENTRADA", "AJUSTE"]
    quantidade: int
    observacao: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validar_quantidade(self):
        if self.quantidade == 0:
            raise ValueError("A quantidade não pode ser zero.")
        if self.tipo == "ENTRADA" and self.quantidade < 0:
            raise ValueError("Uma entrada precisa ter quantidade positiva.")
        return self