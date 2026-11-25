from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import DBAPIError, DataError, IntegrityError, OperationalError, TimeoutError

from app.routers.estoque import router as estoque_router
from app.routers import(
    clientes,
    produtos,
    categorias,
    caracteristicas,
    enderecos,
    pedidos,
    verifica_db,
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

@app.exception_handler(DBAPIError)
async def tratar_banco(request: Request, erro: DBAPIError):
    #usei IA pra pegar os codigos que o banco retorna

    codigo = getattr(erro.orig, "pgcode", None)

    if erro.connection_invalidated or isinstance(erro, OperationalError) and (
        not codigo or codigo.startswith("08") or codigo in {"57P01", "57P02", "57P03"}
    ):
        return resposta_erro(503, "Banco de dados indisponivel")
    
    if codigo in {"23505", "40001", "40P01"}:
        return resposta_erro(409, "Registro duplicado" if codigo == "23505" else "Conflito na operacao")
    
    if codigo == "23503":
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


