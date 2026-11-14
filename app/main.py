from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from psycopg2 import OperationalError, errors

from app.routers.estoque import router as estoque_router
from app.routers import(
    clientes,
    produtos,
    categorias,
    caracteristicas,
    enderecos,
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
app.include_router(verifica_db.router)

@app.exception_handler(errors.UniqueViolation)
def tratar_duplicidade(request: Request, erro: errors.UniqueViolation):
    mensagem = "Ja existe um registro com esses dados"
    return JSONResponse(status_code=409, content={"detail": mensagem})

@app.exception_handler(errors.ForeignKeyViolation)
def tratar_referencia(request: Request, erro: errors.ForeignKeyViolation):
    mensagem = "Um dos registros informados não existe"
    return JSONResponse(status_code=400, content={"detail": mensagem})

@app.exception_handler(errors.CheckViolation)
def tratar_restricao(request: Request, erro: errors.CheckViolation):
    mensagem = f"Valor não permitido ({erro.diag.constraint_name})."
    return JSONResponse(status_code=400, content={"detail": mensagem})

@app.exception_handler(OperationalError)
def tratar_banco_fora(request: Request, erro: OperationalError):
    mensagem = "Não foi possivel conectar ao banco de dados"
    return JSONResponse(status_code=503, content={"detail": mensagem})


