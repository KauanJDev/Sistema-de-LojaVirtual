from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from psycopg2 import OperationalError, errors

from app.routers import crud
from app.models.ClienteModel import ClienteCreate, ClienteRead, ClienteUpdate
from app.models.CategoriaModel import CategoriaCreate
from app.models.ProdutoModel import ProdutoCreate, ProdutoRead, ProdutoUpdate, CaracteristicaProdutoCreate

app = FastAPI(
    title="Loja Virtual",
    description="",
    version="0.0.1",
)

MENSAGENS_DUPLICIDADE = {
    "clientes_email_key": "Ja existe um cliente com esse e-mail.",
    "clientes_cpf_key": "Ja existe um cliente com esse CPF.",
    "categorias_nome_key": "Ja existe uma categoria com esse nome.",
    "caracteristicas_produto_id_nome_key": "Esse produto ja tem uma caracteristica com esse nome.",
}

MENSAGENS_REFERENCIA = {
    "produtos_categoria_id_fkey": "Categoria não encontrada.",
    "caracteristicas_produto_id_fkey": "Produto não encontrado.",
}

@app.exception_handler(errors.UniqueViolation)
def tratar_duplicidade(request: Request, erro: errors.UniqueViolation):
    mensagem = MENSAGENS_DUPLICIDADE.get(
        erro.diag.constraint_name, "Ja existe um registro com esses dados."
    )
    return JSONResponse(status_code=409, content={"detail": mensagem})

@app.exception_handler(errors.ForeignKeyViolation)
def tratar_referencia(request: Request, erro: errors.ForeignKeyViolation):
    mensagem = MENSAGENS_REFERENCIA.get(
        erro.diag.constraint_name, "Um dos registros informados não existe."
    )
    return JSONResponse(status_code=400, content={"detail": mensagem})

@app.exception_handler(errors.CheckViolation)
def tratar_restricao(request: Request, erro: errors.CheckViolation):
    mensagem = f"Valor não permitido ({erro.diag.constraint_name})."
    return JSONResponse(status_code=400, content={"detail": mensagem})

@app.exception_handler(OperationalError)
def tratar_banco_fora(request: Request, erro: OperationalError):
    mensagem = "Não foi possivel conectar ao banco de dados."
    return JSONResponse(status_code=503, content={"detail": mensagem})

def erro_404(registro, mensagem):
    if registro is None:
        raise HTTPException(status_code=404, detail=mensagem)
    return registro

@app.get("/verificar-banco", tags=["Geral"], summary="pra ver se o banco ta funcionando")
def verificar_db():
    with crud.get_db_connection() as connection:
        with crud.get_db_cursor(connection) as cursor:
            cursor.execute("SELECT 1 AS ok;")
            return {"api": "ok", "banco": "ok" if cursor.fetchone()["ok"] == 1 else "erro"}

# CLIENTES

@app.post("/clientes", response_model=ClienteRead, status_code=201, tags=["Clientes"])
def criar_cliente(dados: ClienteCreate):
    return crud.criar_cliente(dados)


@app.get("/clientes", response_model=list[ClienteRead], tags=["Clientes"])
def listar_clientes(
    busca: str | None = Query(default=None, description="Procura o nome e no email"),
    apenas_ativos: bool = True,
):
    return crud.listar_clientes(busca, apenas_ativos)

@app.get("/clientes/{id_cliente}", response_model=ClienteRead, tags=["Clientes"])
def buscar_cliente(id_cliente: int):
    return erro_404(crud.buscar_cliente(id_cliente), "Cliente não encontrado.")

@app.patch("/clientes/{id_cliente}", response_model=ClienteRead, tags=["Clientes"],
           summary="Atualiza so os campos enviados")
def atualizar_cliente(id_cliente: int, dados: ClienteUpdate):
    return erro_404(crud.atualizar_cliente(id_cliente, dados), "Cliente não encontrado.")

@app.delete("/clientes/{id_cliente}", response_model=ClienteRead, tags=["Clientes"],
            summary="Desativar cliente")
def desativar_cliente(id_cliente: int):
    return erro_404(crud.desativar_cliente(id_cliente), "Cliente não encontrado.")

@app.post("/clientes/{id_cliente}/reativar", response_model=ClienteRead, tags=["Clientes"])
def reativar_cliente(id_cliente: int):
    return erro_404(crud.reativar_cliente(id_cliente), "Cliente não encontrado.")

# CATEGORIAS

@app.post("/categorias", status_code=201, tags=["Categorias"])
def criar_categoria(dados: CategoriaCreate):
    return crud.criar_categoria(dados)

@app.get("/categorias", tags=["Categorias"])
def listar_categorias(apenas_ativas: bool = True):
    return crud.listar_categorias(apenas_ativas)

# PRODUTOS

@app.post("/produtos", response_model=ProdutoRead, status_code=201, tags=["Produtos"],
          summary="Criar produtos")
def criar_produto(dados: ProdutoCreate):
    return crud.criar_produto(dados)

@app.get("/produtos", response_model=list[ProdutoRead], tags=["Produtos"])
def listar_produtos(
    busca: str | None = Query(default=None, description="Procura pelo nome"),
    categoria_id: int | None = None,
    apenas_ativos: bool = True,
    apenas_disponiveis: bool = False,
):
    return crud.listar_produtos(busca, categoria_id, apenas_ativos, apenas_disponiveis)

@app.get("/produtos/{id_produto}", response_model=ProdutoRead, tags=["Produtos"])
def buscar_produto(id_produto: int):
    return erro_404(crud.buscar_produto(id_produto), "Produto não encontrado.")

@app.patch("/produtos/{id_produto}", response_model=ProdutoRead, tags=["Produtos"],
           summary="Atualiza so os campos enviados")
def atualizar_produto(id_produto: int, dados: ProdutoUpdate):
    return erro_404(crud.atualizar_produto(id_produto, dados), "Produto não encontrado.")

@app.delete("/produtos/{id_produto}", response_model=ProdutoRead, tags=["Produtos"],
            summary="Desativar produtos")
def desativar_produto(id_produto: int):
    erro_404(crud.desativar_produto(id_produto), "Produto não encontrado.")
    return crud.buscar_produto(id_produto)

@app.post("/produtos/{id_produto}/reativar", response_model=ProdutoRead, tags=["Produtos"])
def reativar_produto(id_produto: int):
    erro_404(crud.reativar_produto(id_produto), "Produto não encontrado.")
    return crud.buscar_produto(id_produto)

# CARACTERISTICAS DO PRODUTO

@app.post("/caracteristicas", status_code=201, tags=["Caracteristicas"])
def criar_caracteristica(dados: CaracteristicaProdutoCreate):
    return crud.criar_caracteristica(dados)

@app.get("/produtos/{id_produto}/caracteristicas", tags=["Caracteristicas"])
def listar_caracteristicas(id_produto: int):
    erro_404(crud.buscar_produto(id_produto), "Produto não encontrado.")
    return crud.listar_caracteristicas(id_produto)

@app.delete("/caracteristicas/{id_caracteristica}", tags=["Caracteristicas"])
def excluir_caracteristica(id_caracteristica: int):
    return erro_404(crud.excluir_caracteristica(id_caracteristica), "Caracteristica não encontrada.")