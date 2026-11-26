from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import DBAPIError, DataError, IntegrityError, OperationalError, TimeoutError
from psycopg2 import errors as pg

from app.routers.estoque import router as estoque_router
from app.routers import(
    clientes,
    produtos,
    categorias,
    caracteristicas,
    enderecos,
    pedidos,
    verifica_db,
    relatorios,
)

app = FastAPI(
    title="Loja Virtual",
    description="Sistema de Vendas para Loja Virtual",
    version="0.1",
)

app.include_router(estoque_router)
app.include_router(clientes.router)
app.include_router(produtos.router)
app.include_router(categorias.router)
app.include_router(caracteristicas.router)
app.include_router(caracteristicas.router_do_produto)
app.include_router(enderecos.router)
app.include_router(enderecos.router_do_cliente)
app.include_router(pedidos.router)
app.include_router(pedidos.router_do_cliente)
app.include_router(verifica_db.router)
app.include_router(relatorios.router)

def resposta_erro(status, mensagem):
    return JSONResponse(status_code=status, content={"detail": mensagem})

@app.exception_handler(RequestValidationError)
async def tratar_validacao(request: Request, erro: RequestValidationError):
    detalhes = [
        {"loc": item["loc"], "type": item["type"],
         "msg": "Campo obrigatorio" if item["type"] == "missing" else "Valor invalido"}
        for item in erro.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": detalhes})

def banco_indisponivel(erro: DBAPIError) -> bool:
    if erro.connection_invalidated:
        return True
    if not isinstance(erro, OperationalError):
        return False

    causa = erro.orig
    codigo = getattr(causa, "pgcode", None)
    return (
        not codigo
        or codigo.startswith("08")
        or isinstance(causa, (pg.AdminShutdown, pg.CrashShutdown, pg.CannotConnectNow))
    )

@app.exception_handler(DBAPIError)
async def tratar_banco(request: Request, erro: DBAPIError):
    causa = erro.orig

    if banco_indisponivel(erro):
        return resposta_erro(503, "Banco de dados indisponivel")
    if isinstance(causa, pg.UniqueViolation):
        return resposta_erro(409, "Registro duplicado")
    if isinstance(causa, (pg.SerializationFailure, pg.DeadlockDetected)):
        return resposta_erro(409, "Conflito na operacao")
    if isinstance(causa, pg.ForeignKeyViolation):
        return resposta_erro(400, "Referencia invalida para esta operacao")
    if isinstance(erro, (DataError, IntegrityError)):
        return resposta_erro(422, "Dados invalidos para esta operacao")
    return resposta_erro(500, "Erro interno no banco de dados")

@app.exception_handler(TimeoutError)
async def tratar_timeout(request: Request, erro: TimeoutError):
    return resposta_erro(503, "Banco de dados indisponivel")

@app.exception_handler(Exception)
async def tratar_erro_interno(request: Request, erro: Exception):
    return resposta_erro(500, "Erro interno no servidor")


