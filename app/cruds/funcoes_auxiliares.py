from  fastapi import HTTPException
from sqlalchemy import delete, func, insert, or_, select, update, desc
from db.db import Sessao

def listar(consulta):
    with Sessao() as sessao:
        return sessao.execute(consulta).mappings().all()

def executar_um(comando):
    with Sessao.begin() as sessao:
        return sessao.execute(comando).mappings().one_or_none()

def campos(dados):

    valores = dados.model_dump(exclude_unset=True)

    for campo in (
        "nome",
        "destinatario",
        "numero",
        "bairro",
        "cidade",
        "estado",
        "valor",
    ):
        if valores.get(campo) is not None:
            valores[campo] = valores[campo].strip()

    if valores.get("email"):
        valores["email"] = valores["email"].strip().lower()

    if valores.get("cpf"):
        valores["cpf"] = valores["cpf"].replace(".", "").replace("-", "")
    return valores

def atualizar(modelo, identificador, valores):
    if not valores:
        return executar_um(select(modelo.__table__).where(modelo.id == identificador))
    
    comando = update(modelo).where(modelo.id == identificador).values(**valores)
    return executar_um(comando.returning(*modelo.__table__.c))
