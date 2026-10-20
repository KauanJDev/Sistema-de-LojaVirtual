# Sistema de Loja Virtual
 
> Sistema de Loja Virtual com persistência relacional, controle de estoque seguro contra concorrência e relatórios de vendas baseados em pedidos efetivamente registrados.
 
**Descrição:**
Sistema de loja virtual com banco relacional: registro de pedidos, controle de estoque transacional, preservação de preços e endereços históricos e relatórios de vendas por período, produto e categoria.

## Integrantes

- Gabriel Fernandes
- Anna Liz
- Kauan Ferreira

## Sobre o projeto
 
Este projeto implementa o back-end de uma loja virtual de produtos de informática, acessórios e equipamentos eletrônicos. A aplicação substitui o controle feito em planilhas por um banco de dados relacional, garantindo integridade dos dados, rastreabilidade das operações e consistência do estoque.
 
O sistema permite:
 
- manter um catálogo de produtos organizado por categorias;
- registrar pedidos de clientes, com múltiplos itens e endereço de entrega;
- controlar a disponibilidade dos produtos, impedindo vendas acima do estoque;
- preservar o histórico de preços e dados de entrega de cada venda;
- gerar resumos de vendas por período, produto e categoria.

 ## Contexto e problema

 A empresa utilizava planilhas para armezenar os dados como os clientes, produtos e vendas. Com o crescimento do volume de pedidos, esse modelo passou a gerar problemas como: Pedidos aceitos sem estoque suficiente, Operações simultâneas sobre o mesmo produto, Alteração de preço ou de endereço no cadastro, Falta de distinção entre pedido e venda efetivada além de dados "jogados" na planilha.

 ## Objetivos

 - Modelar um banco relacional com integridade referencial.
 - Não deixar modificar o preço e endereço no momento da compra(etapa final).
 - Aplicar efeitos distintos no estoque conforme o status do pedido.
 - Disponibilziar analises consistentes sobre as vendas realizadas.

 ## Funcionalidades

 **Catálogo**
- Cadastro, edição e desativação de categorias e produtos
- Mostrar caracteristicas dos produtos
- Busca por nome, categoria e disponibilidade

**Clientes e endereços**
- Cadastro de clientes
- Múltiplos endereços por cliente(Adicional), com endereço principal

**Pedidos**
- Criação de pedidos com vários produtos e quantidades
- Verificação de disponibilidade no registro
- Baixar estoque ao realizar uma venda efetiva
- Atualização de status (aguardando confirmação → confirmado → enviado → entregue)
- Cancelamento com tratamento de estoque conforme o status
- Histórico de mudanças de status

**Estoque**
- Consulta de quantidade disponível
- Entradas de reposição e ajustes manuais
- Registro de todas as movimentações

**Relatórios**
- Vendas por período, por produto e por categoria
- Ranking de produtos mais vendidos
- Comparação entre períodos

## Regras de negócio
 
| Código | Regra |
|---|---|
| RN01 | A quantidade em estoque nunca pode ficar negativa. |
| RN02 | Não é possível registrar item com quantidade acima da disponível. |
| RN03 | A quantidade de cada item deve ser maior que zero. |
| RN04 | Um pedido deve ter ao menos um item; o mesmo produto não se repete no pedido. |
| RN05 | O preço do item é o preço do catálogo no momento da compra e nunca é recalculado. |
| RN06 | mudanças no cadastro de endereços não afetam pedidos anteriores. |
| RN07 | Produtos e clientes com histórico não são apagados fisicamente (apenas inativada). |
| RN08 | Só é possível usar um endereço que pertença ao cliente do pedido. |
| RN09 | O faturamento considera apenas vendas efetivadas (`CONFIRMADO`, `ENVIADO`, `ENTREGUE`). |
| RN10 | O cancelamento só é permitido antes do envio. |
| RN11 | As mudanças de status seguem apenas as transições permitidas. |
| RN12 | Produtos inativos não podem ser adicionados a novos pedidos. |

## Entidades

| Entidade | Atributos |
|---|---|
| `categoria` | `id` (PK), `nome` (UK), `descricao`, `ativa` |
| `produto` | `id` (PK), `categoria_id` (FK), `nome`, `descricao`, `preco_atual`, `ativo`, `criado_em`, `atualizado_em` |
| `caracteristica_produto` | `id` (PK), `produto_id` (FK), `nome`, `valor` |
| `estoque` | `produto_id` (PK e FK), `quantidade_disponivel` (≥ 0), `atualizado_em` |
| `movimentacao_estoque` | `id` (PK), `produto_id` (FK), `pedido_id` (FK), `tipo`, `quantidade`, `data_hora`, `observacao` |
| `cliente` | `id` (PK), `nome`, `email` (UK), `cpf` (UK), `telefone`, `ativo`, `criado_em` |
| `endereco` | `id` (PK), `cliente_id` (FK), `destinatario`, `cep`, `numero`, `complemento`, `bairro`, `cidade`, `estado`, `principal`, `ativo` |
| `pedido` | `id` (PK), `cliente_id` (FK), `endereco_id` (FK), `status`, `data_pedido`, `data_confirmacao`, `data_envio`, `data_entrega`, `data_cancelamento`, `motivo_cancelamento`, `valor_total`, `entrega_destinatario`, `entrega_cep`, `entrega_numero`, `entrega_complemento`, `entrega_bairro`, `entrega_cidade`, `entrega_estado` |
| `item_pedido` | `id` (PK), `pedido_id` (FK), `produto_id` (FK), `quantidade`, `preco_unitario` |
| `historico_status_pedido` | `id` (PK), `pedido_id` (FK), `status_anterior`, `status_novo`, `data_hora`, `observacao` |
 
**Restrições:**
 
- `item_pedido`: `UNIQUE (pedido_id, produto_id)` e `CHECK (quantidade > 0)`.
- `estoque`: `(quantidade_disponivel >= 0)`.
- `produto`: `(preco_atual >= 0)`.
- `pedido.status` e `movimentacao_estoque.tipo` aceitam apenas os valores definidos nos enums.
- `pedido.endereco_id` é só uma referência ao cadastro; os dados de entrega de fato ficam nas colunas `entrega_*`.




