from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from psycopg2 import OperationalError, errors

from app.routers import crud
from app.models.ClienteModel import ClienteCreate, ClienteRead, ClienteUpdate
from app.models.CategoriaModel import CategoriaCreate
from app.models.ProdutoModel import ProdutoCreate, ProdutoRead, ProdutoUpdate, CaracteristicaProdutoCreate
from app.models.EnderecoModel import EnderecoCreate, EnderecoUpdate, EnderecoRead

app = FastAPI(
    title="Loja Virtual",
    description="",
    version="0.0.1",
)

@app.exception_handler(errors.UniqueViolation)
def tratar_duplicidade(request: Request, erro: errors.UniqueViolation):
    mensagem = "Ja existe um registro com esses dados."
    return JSONResponse(status_code=409, content={"detail": mensagem})

@app.exception_handler(errors.ForeignKeyViolation)
def tratar_referencia(request: Request, erro: errors.ForeignKeyViolation):
    mensagem = "Um dos registros informados não existe."
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

# ENDEREÇO

@app.post("/enderecos", response_model=EnderecoRead, status_code=201, tags=["Endereços"],
          summary="Cadastra um endereço para o cliente")
def criar_endereco(dados: EnderecoCreate):
    return crud.criar_endereco(dados)
 
@app.get("/clientes/{id_cliente}/enderecos", response_model=list[EnderecoRead],
         tags=["Endereços"], summary="Lista os endereços do cliente")
def listar_enderecos(id_cliente: int, apenas_ativos: bool = True):
    erro_404(crud.buscar_cliente(id_cliente), "Cliente não encontrado.")
    return crud.listar_enderecos(id_cliente, apenas_ativos)
 
@app.patch("/enderecos/{id_endereco}", response_model=EnderecoRead, tags=["Endereços"],
           summary="Atualiza so os campos enviados")
def atualizar_endereco(id_endereco: int, dados: EnderecoUpdate):
    return erro_404(crud.atualizar_endereco(id_endereco, dados), "Endereço não encontrado.")
 
@app.post("/enderecos/{id_endereco}/principal", response_model=EnderecoRead, tags=["Endereços"],
          summary="Define como o endereço principal do cliente")
def definir_endereco_principal(id_endereco: int):
    return erro_404(crud.definir_endereco_principal(id_endereco),
                  "Endereço não encontrado ou não é o ativo.")
 
@app.delete("/enderecos/{id_endereco}", response_model=EnderecoRead, tags=["Endereços"],
            summary="Desativa o endereço")
def desativar_endereco(id_endereco: int):
    return erro_404(crud.desativar_endereco(id_endereco), "Endereço não encontrado.")
 
@app.post("/enderecos/{id_endereco}/reativar", response_model=EnderecoRead, tags=["Endereos"])
def reativar_endereco(id_endereco: int):
    return erro_404(crud.reativar_endereco(id_endereco), "Endereço não encontrado.")