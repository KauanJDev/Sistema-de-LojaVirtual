# Sistema de Loja Virtual

**Tema recebido** — Tema 9 — Sistema de Loja Virtual.  
**Integrantes** — Gabriel Fernandes, Anna Liz e Kauan Ferreira.

## Contexto e descrição do problema

Uma pequena empresa de comércio eletrônico vende produtos de informática, acessórios e equipamentos eletrônicos. No começo se era usado planilhas para controlar todas as vendas da loja, com o crescimento de demanda começou a ficar dificil saber a quantidade de unidades dos produtos disponiveis e como estavam a situação dos pedidos solicitados. Dois clientes podiam comprar a última unidade de um produto quase ao mesmo tempo, provocando atrasos e cancelamentos.

A empresa também precisava preservar as condições de cada compra. Uma alteração de preço no catálogo ou de endereço no cadastro do cliente não pode modificar o valor cobrado nem o destino de um pedido anterior.

## Objetivo e necessidade central

Registrar pedidos, controlar a disponibilidade dos produtos e gerar resumos de vendas por período, produto e categoria. A administração deve conseguir identificar os produtos com mais unidades vendidas e comparar o faturamento de diferentes períodos usando os preços efetivamente praticados nas vendas.

## Funcionalidade específica do tema

Um cliente pode fazer vários pedidos ao longo do tempo e escolher um endereço de entrega diferente para cada compra. Cada pedido pode reunir vários produtos. Quando o cliente compra mais de uma unidade do mesmo produto, o item registra a quantidade e o preço unitário daquela compra.

| Operação | Efeito no estoque | Efeito no faturamento |
|---|---|---|
| Registrar o pedido | Verifica a disponibilidade de cada item. O saldo permanece disponível até a confirmação. | O pedido fica pendente. |
| Confirmar o pedido | Verifica novamente o saldo e dá baixa nas unidades de cada item. | O valor entra no faturamento na data da confirmação. |
| Enviar ou entregar | Mantém o saldo registrado na confirmação. | A venda continua contabilizada uma única vez. |
| Cancelar antes de confirmar | Mantém o saldo, pois ainda não houve baixa. | O pedido permanece fora do faturamento. |
| Cancelar após confirmar e antes de enviar | Devolve as unidades ao estoque e registra o estorno. | O pedido cancelado é excluído do total de vendas efetivadas. |

No PostgreSQL, a confirmação bloqueia as linhas de estoque durante a transação. Se dois pedidos pendentes disputarem a última unidade, a primeira confirmação consome o saldo. A segunda encontra saldo insuficiente e recebe HTTP 409.

## Tecnologias utilizadas

| Tecnologia | Uso no projeto |
|---|---|
| Python 3.12 | Execução da aplicação e dos exemplos deste README |
| FastAPI e Pydantic | Rotas HTTP, validação dos dados e documentação da API |
| Uvicorn | Servidor da aplicação |
| SQLAlchemy | Consultas, relacionamentos e transações |
| PostgreSQL e psycopg2 | Banco de dados e driver usados pela versão publicada |
| Alembic | Criação e evolução das tabelas por migrações |
| python-dotenv | Leitura da configuração local no arquivo `.env` |
| SQLite | Alternativa para demonstração local com a adaptação documentada abaixo |

## Modelo relacional

![Diagrama entidade-relacionamento da loja](docs/modelo-ER.png)

### Entidades e relacionamentos

| Tabela | Descrição e relacionamentos |
|---|---|
| `categorias` | Armazena nome único, descrição e situação. Uma categoria pode agrupar vários produtos. |
| `produtos` | Armazena nome, descrição, preço atual e situação. Cada produto pertence a uma categoria por meio de `categoria_id`. |
| `caracteristicas_produto` | Guarda características como “Capacidade: 1 TB”. Um produto pode ter várias características. O nome da característica é único dentro do mesmo produto. |
| `estoque` | Guarda a quantidade disponível e a data de atualização. `produto_id` é chave primária e estrangeira. A API cria um registro de estoque para cada produto. |
| `movimentacoes_estoque` | Registra entradas, ajustes, saídas por venda e estornos. Cada movimentação pertence a um produto. Saídas por venda e estornos também identificam o pedido. |
| `clientes` | Armazena nome, e-mail, CPF, telefone e situação. E-mail e CPF são únicos. Um cliente pode ter vários endereços e pedidos. |
| `enderecos` | Armazena destinatário, CEP, número, complemento, bairro, cidade e estado. Cada endereço pertence a um cliente, que pode ter no máximo um endereço ativo marcado como principal. |
| `pedidos` | Guarda cliente, referência ao endereço, cópia dos dados de entrega, status, datas e valor total. Um mesmo endereço pode ser usado em vários pedidos. |
| `itens_pedido` | Relaciona pedidos e produtos. Um pedido pode conter vários produtos, e um produto pode aparecer em vários pedidos. Cada item guarda quantidade e preço unitário da compra. |
| `historico_status_pedido` | Registra a criação do pedido e cada mudança de status, com data, estado anterior, estado novo e observação. Um pedido pode ter vários registros de histórico. |

## Instalação

Instale Git e Python 3.12. Para o caminho padrão, instale também PostgreSQL e o cliente `psql`. O fluxo abaixo foi validado com PostgreSQL 16.

### 1. Clonar o repositório e criar o ambiente virtual

```bash
git clone https://github.com/KauanJDev/Sistema-de-LojaVirtual.git
cd Sistema-de-LojaVirtual
python -m venv .venv
```

No Windows PowerShell, ative o ambiente com:

```powershell
.\.venv\Scripts\Activate.ps1
```

No Linux ou macOS:

```bash
source .venv/bin/activate
```

### 2. Instalar as dependências

Na raiz do projeto, com o ambiente virtual ativo:

```bash
python -m pip install -r requirements.txt
```

### 3. Configurar o PostgreSQL

Com o serviço PostgreSQL em execução, conecte-se como administrador:

```bash
psql -U postgres -d postgres
```

No `psql`, crie um usuário para a aplicação, defina sua senha e crie o banco. O comando `\password` solicita a senha sem exibi-la.

```sql
CREATE ROLE loja_app LOGIN;
\password loja_app
CREATE DATABASE loja_virtual OWNER loja_app;
```

Crie um arquivo `.env` na raiz do repositório usando `.envexample` como referência. Preencha `DB_PASSWORD` com a senha definida acima.

```dotenv
DB_HOST=localhost
DB_NAME=loja_virtual
DB_USER=loja_app
DB_PASSWORD=sua_senha_local
```

Essa é a configuração usada diretamente pela versão publicada do projeto.

### 4. Configurar DATABASE_URL

Na versão publicada, `db/db.py` monta uma conexão PostgreSQL a partir de `DB_HOST`, `DB_NAME`, `DB_USER` e `DB_PASSWORD`. Para escolher o banco por `DATABASE_URL`, aplique a adaptação abaixo. Quem utiliza a configuração padrão de PostgreSQL pode seguir diretamente para as migrações.
```
A API e o Alembic compartilham essa conexão. O `PRAGMA` ativa as chaves estrangeiras em cada conexão SQLite. A função `now()` atende aos valores padrão usados pela migração existente.
```

Execute as migrações e a aplicação a partir da raiz do projeto. O Alembic criará o arquivo `loja.db` nessa pasta.

Para usar **PostgreSQL pela mesma variável**, substitua a linha do SQLite por:

```dotenv
DATABASE_URL=postgresql+psycopg2://loja_app:sua_senha_local@localhost:5432/loja_virtual
```


O SQLite atende a demonstrações locais de cadastro, pedidos e consultas. Use PostgreSQL nos testes de confirmações simultâneas, pois SQLite não implementa o bloqueio de linha `SELECT ... FOR UPDATE`.

</details>

### 5. Executar as migrações

```bash
python -m alembic upgrade head
python -m alembic current
```

O primeiro comando aplica as migrações. O segundo mostra a revisão instalada. Para um banco novo, esse procedimento cria as tabelas. O arquivo `db/schema.sql` também contém o DDL de referência para PostgreSQL.

### 6. Executar a aplicação

```bash
python -m uvicorn app.main:app --reload
```

| Endereço local | Finalidade |
|---|---|
| `http://127.0.0.1:8000/docs` | Abrir o Swagger e testar os endpoints |
| `http://127.0.0.1:8000/verificar-banco` | Verificar a comunicação entre API e banco |

Com a conexão funcionando, `/verificar-banco` retorna:

```json
{"api": "ok", "banco": "ok"}
```

## Execução do povoamento

A carga abaixo usa a própria API. Assim, a criação dos registros também exercita as regras de pedido, estoque e histórico.

1. Inicie a aplicação com um banco de demonstração recém-migrado.
2. Salve o código abaixo como `povoar.py` na raiz do projeto.
3. Em um segundo terminal, execute `python povoar.py`.

Execute a carga uma vez por base vazia. Cada requisição concluída grava seus dados, e uma nova execução na mesma base encontra nomes de categorias, e-mails e CPFs já cadastrados.

<details>
<summary>Mostrar código de povoamento das dez tabelas</summary>

```python
import json
from urllib.request import Request, urlopen


def enviar(metodo, rota, dados):
    requisicao = Request(
        "http://127.0.0.1:8000" + rota,
        method=metodo,
        data=json.dumps(dados).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(requisicao) as resposta:
        return json.load(resposta)


# Categoria, produto, preço, saldo inicial, quantidade comprada, especificação, cliente
catalogo = [
    ("Teclados", "Teclado mecânico", 249.90, 20, 2, "ABNT2", "Ana Lima"),
    ("Mouses", "Mouse sem fio", 89.90, 30, 1, "Bluetooth", "Bruno Alves"),
    ("Monitores", "Monitor IPS 24", 899, 12, 1, "Full HD", "Carla Dias"),
    ("Áudio", "Headset USB", 159.90, 18, 2, "USB-A", "Diego Martins"),
    ("Armazenamento", "SSD NVMe", 349, 25, 3, "1 TB", "Elisa Costa"),
    ("Redes", "Roteador Wi-Fi 6", 289.90, 15, 1, "4 portas", "Fábio Reis"),
    ("Vídeo", "Webcam Full HD", 139.90, 16, 2, "30 fps", "Giovana Luz"),
    ("Cabos", "Cabo HDMI", 34.90, 50, 3, "2 metros", "Hugo Ramos"),
    ("Energia", "Filtro de linha", 64.90, 22, 1, "6 tomadas", "Iara Melo"),
    ("Suportes", "Suporte de notebook", 79.90, 14, 1, "Alumínio", "João Castro"),
]

for n, (categoria, produto, preco, saldo, qtd, detalhe, nome) in enumerate(catalogo, 1):
    cat = enviar("POST", "/categorias", {"nome": "Demo - " + categoria})

    p = enviar("POST", "/produtos", {
        "categoria_id": cat["id"],
        "nome": produto,
        "preco_atual": preco,
        "quantidade_inicial": saldo,
    })
    enviar("POST", "/caracteristicas", {
        "produto_id": p["id"], "nome": "Especificação", "valor": detalhe,
    })

    c = enviar("POST", "/clientes", {
        "nome": nome, "cpf": f"{n:011d}", "email": f"loja.demo.{n}@example.test",
    })
    e = enviar("POST", "/enderecos", {
        "cliente_id": c["id"], "destinatario": nome, "cep": "50000000",
        "numero": str(100 + n), "bairro": "Centro", "cidade": "Recife",
        "estado": "PE", "principal": True,
    })

    pedido = enviar("POST", "/pedidos", {
        "cliente_id": c["id"],
        "endereco_id": e["id"],
        "itens": [{"produto_id": p["id"], "quantidade": qtd}],
    })
    if n % 2 == 1:
        enviar("PATCH", f"/pedidos/{pedido['id']}/status", {"status": "CONFIRMADO"})
```

</details>

**Resultado esperado em uma base vazia:** 10 registros em cada uma das oito tabelas de categorias, produtos, características, estoque, clientes, endereços, pedidos e itens. A carga também gera 15 movimentações de estoque e 15 registros de histórico, totalizando **110 registros**.

| Situação | Pedidos | Valor total |
|---|---:|---:|
| `CONFIRMADO` | 5 | R$ 2.790,50 |
| `AGUARDANDO_CONFIRMACAO` | 5 | R$ 884,20 |

## Principais endpoints

Os IDs nos caminhos correspondem aos identificadores devolvidos pela API. Nas rotas de produtos, clientes e endereços, `DELETE` realiza a desativação.

| Recurso | Métodos e caminhos |
|---|---|
| Categorias | `GET /categorias` e `POST /categorias` |
| Produtos | `GET /produtos`, `POST /produtos`, `GET`, `PATCH` e `DELETE /produtos/{id_produto}`, `POST /produtos/{id_produto}/reativar` |
| Características | `POST /caracteristicas`, `GET /produtos/{id_produto}/caracteristicas`, `DELETE /caracteristicas/{id_caracteristica}` |
| Clientes | `GET /clientes`, `POST /clientes`, `GET`, `PATCH` e `DELETE /clientes/{id_cliente}`, `POST /clientes/{id_cliente}/reativar` |
| Endereços | `POST /enderecos`, `GET /clientes/{id_cliente}/enderecos`, `PATCH` e `DELETE /enderecos/{id_endereco}`, `POST /enderecos/{id_endereco}/principal`, `POST /enderecos/{id_endereco}/reativar` |
| Estoque | `GET /estoque/{produto_id}/estoque`, `GET /estoque/{produto_id}/qtd_disponivel`, `GET /estoque/movimentações`, `PATCH /estoque/{produto_id}/repor?qtd_adicional=5`, `PATCH /estoque/{produto_id}/editar_qtd?qtd_nova=10` |
| Pedidos | `POST /pedidos`, `GET /pedidos`, `GET /pedidos/{id_pedido}`, `GET /clientes/{id_cliente}/pedidos`, `PATCH /pedidos/{id_pedido}/status`, `GET /pedidos/{id_pedido}/historico` |
| Relatórios | `GET /relatorios/filtro/periodo`, `GET /relatorios/filtro/produto/{produto_id}`, `GET /relatorios/ranking` |

## Filtros disponíveis

| Consulta | Parâmetros |
|---|---|
| Categorias | `apenas_ativas`, com padrão `true`. |
| Produtos | `busca` por parte do nome, `categoria_id`, `apenas_ativos` e `apenas_disponiveis`. Por padrão, a lista mostra produtos ativos e inclui produtos sem saldo. |
| Clientes | `busca` por nome ou e-mail e `apenas_ativos`, com padrão `true`. |
| Endereços do cliente | `apenas_ativos`, com padrão `true`. |
| Pedidos | `status`, `cliente_id`, `data_inicio` e `data_fim`. As datas filtram o momento do pedido. |
| Paginação de pedidos | A lista geral e a lista por cliente aceitam `offset` e `limit`. Os padrões são 0 e 10. O limite aceito é de 1 a 100. |
| Movimentações de estoque | `produto_id` e `tipo`. Os tipos são `ENTRADA`, `AJUSTE`, `SAIDA_VENDA` e `ESTORNO_CANCELAMENTO`. |
| Relatório por período | `p_comeco` e `p_fim`, obrigatórios, em formato ISO como `2026-11-01T00:00:00`. |
| Ranking | `limit`, obrigatório e maior ou igual a zero. |

Exemplos de uso:

```text
GET /produtos?busca=teclado&apenas_disponiveis=true
GET /clientes?busca=Ana
GET /pedidos?status=CONFIRMADO&limit=5&offset=0
GET /estoque/movimentações?produto_id=1&tipo=SAIDA_VENDA
GET /relatorios/ranking?limit=5
```
## Consultas específicas do tema
o relatório HTTP por período ignorou a data inicial e incluiu um pedido cancelado. O relatório por produto cruzou itens e pedidos sem associá-los pelo ID, e o ranking ordenou os produtos pelo preço. O relatório por categoria previsto no projeto ainda não possui rota HTTP.

As consultas SQL abaixo aplicam diretamente a regra de venda efetivada e permitem conferir os resultados da API.

### 1. Faturamento por período de confirmação

Ajuste as datas ao período desejado. O início é inclusivo e o fim é exclusivo, de modo que todo o último dia do mês entra na consulta.

```sql
SELECT COUNT(*) AS pedidos_efetivados,
       COALESCE(SUM(valor_total), 0) AS faturamento
FROM pedidos
WHERE status IN ('CONFIRMADO', 'ENVIADO', 'ENTREGUE')
  AND data_confirmacao >= '2026-11-01'
  AND data_confirmacao <  '2026-12-01';
```

### 2. Ranking dos produtos por unidades vendidas

```sql
SELECT p.nome, SUM(i.quantidade) AS unidades_vendidas
FROM itens_pedido i
JOIN produtos p ON p.id = i.produto_id
JOIN pedidos v ON v.id = i.pedido_id
WHERE v.status IN ('CONFIRMADO', 'ENVIADO', 'ENTREGUE')
GROUP BY p.id, p.nome
ORDER BY unidades_vendidas DESC, p.id
LIMIT 10;
```

Com a carga de exemplo, o **SSD NVMe** lidera com **3 unidades**. O teclado e a webcam aparecem com **2 unidades** cada.

### 3. Faturamento por categoria

A receita considera o preço unitário registrado no item no momento da venda. O agrupamento usa a categoria atual do produto.

```sql
SELECT c.nome AS categoria,
       SUM(i.quantidade * i.preco_unitario) AS receita
FROM itens_pedido i
JOIN pedidos v ON v.id = i.pedido_id
JOIN produtos p ON p.id = i.produto_id
JOIN categorias c ON c.id = p.categoria_id
WHERE v.status IN ('CONFIRMADO', 'ENVIADO', 'ENTREGUE')
GROUP BY c.id, c.nome
ORDER BY receita DESC, c.id;
```

Com os dados de exemplo, **Demo - Armazenamento** soma **R$ 1.047,00**, correspondentes a três SSDs de R$ 349,00.

## Regras de negócio

| Código | Regra |
|---|---|
| RN01 | A quantidade em estoque deve permanecer maior ou igual a zero. |
| RN02 | A quantidade solicitada deve estar disponível no registro e na confirmação do pedido. |
| RN03 | Cada item deve ter quantidade inteira maior que zero. |
| RN04 | Um pedido deve conter ao menos um item. Cada produto pode aparecer uma única vez no mesmo pedido. |
| RN05 | O item preserva o preço do catálogo no momento da compra. |
| RN06 | Alterações no cadastro de endereços preservam os dados de entrega dos pedidos anteriores. |
| RN07 | A desativação de clientes e produtos preserva o histórico de compras. |
| RN08 | O endereço de entrega deve estar ativo e pertencer ao cliente do pedido, que também deve estar ativo. |
| RN09 | O faturamento considera pedidos em `CONFIRMADO`, `ENVIADO` ou `ENTREGUE`. |
| RN10 | O cancelamento exige um motivo e só é permitido antes do envio. Um pedido confirmado gera estorno. Um pedido aguardando confirmação pode ser cancelado sem movimentar o estoque. |
| RN11 | O fluxo normal é `AGUARDANDO_CONFIRMACAO → CONFIRMADO → ENVIADO → ENTREGUE`. Os dois primeiros estados também permitem a transição para `CANCELADO`. |
| RN12 | Apenas produtos ativos podem ser adicionados a novos pedidos. |




