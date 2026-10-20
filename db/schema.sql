-- =====================================================================
-- Status do pedido:
--   AGUARDANDO_CONFIRMACAO, CONFIRMADO, ENVIADO, ENTREGUE, CANCELADO
-- Tipos de movimentação de estoque:
--   ENTRADA, SAIDA_VENDA, ESTORNO_CANCELAMENTO, AJUSTE
-- =====================================================================

CREATE TABLE IF NOT EXISTS categorias (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) UNIQUE NOT NULL,
    descricao VARCHAR(255),
    ativa BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS produtos (
    id SERIAL PRIMARY KEY,
    categoria_id INTEGER NOT NULL REFERENCES categorias(id),
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    preco_atual NUMERIC(10, 2) NOT NULL CHECK (preco_atual >= 0),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS caracteristicas_produto (
    id SERIAL PRIMARY KEY,
    produto_id INTEGER NOT NULL REFERENCES produtos(id) ON DELETE CASCADE,
    nome VARCHAR(60) NOT NULL,
    valor VARCHAR(255) NOT NULL,
    UNIQUE (produto_id, nome)
);

-- ---------------------------------------------------------------------
-- ESTOQUE (1:1 com produtos)
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS estoque (
    produto_id INTEGER PRIMARY KEY REFERENCES produtos(id),
    quantidade_disponivel INTEGER NOT NULL DEFAULT 0
        CHECK (quantidade_disponivel >= 0),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------
-- CLIENTES E ENDEREÇOS
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    cpf VARCHAR(14) UNIQUE,
    telefone VARCHAR(20),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS enderecos (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    destinatario VARCHAR(100) NOT NULL,
    cep VARCHAR(9) NOT NULL,
    numero VARCHAR(10) NOT NULL,
    complemento VARCHAR(60),
    bairro VARCHAR(60) NOT NULL,
    cidade VARCHAR(60) NOT NULL,
    estado VARCHAR(50) NOT NULL,
    principal BOOLEAN NOT NULL DEFAULT FALSE,
    ativo BOOLEAN NOT NULL DEFAULT TRUE
);

-- Cada cliente pode ter no máximo um endereço principal ativo
CREATE UNIQUE INDEX IF NOT EXISTS ux_enderecos_principal
    ON enderecos (cliente_id)
    WHERE principal AND ativo;

-- ---------------------------------------------------------------------
-- PEDIDOS
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pedidos (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    endereco_id INTEGER REFERENCES enderecos(id),   -- apenas referência ao cadastro
    status VARCHAR(30) NOT NULL DEFAULT 'AGUARDANDO_CONFIRMACAO'
        CHECK (status IN ('AGUARDANDO_CONFIRMACAO', 'CONFIRMADO',
                          'ENVIADO', 'ENTREGUE', 'CANCELADO')),
    data_pedido TIMESTAMP NOT NULL DEFAULT NOW(),
    data_confirmacao TIMESTAMP,
    data_envio TIMESTAMP,
    data_entrega TIMESTAMP,
    data_cancelamento TIMESTAMP,
    motivo_cancelamento VARCHAR(255),
    valor_total NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (valor_total >= 0),

    -- Snapshot do endereço de entrega (copiado no momento do pedido)
    entrega_destinatario VARCHAR(100) NOT NULL,
    entrega_cep VARCHAR(9) NOT NULL,
    entrega_numero VARCHAR(10) NOT NULL,
    entrega_complemento VARCHAR(60),
    entrega_bairro VARCHAR(60) NOT NULL,
    entrega_cidade VARCHAR(60) NOT NULL,
    entrega_estado VARCHAR(50) NOT NULL,

    -- Vendas efetivadas precisam ter data de confirmação (usada nos relatórios)
    CONSTRAINT ck_pedidos_data_confirmacao CHECK (
        status NOT IN ('CONFIRMADO', 'ENVIADO', 'ENTREGUE')
        OR data_confirmacao IS NOT NULL
    )
);

CREATE TABLE IF NOT EXISTS itens_pedido (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id),
    produto_id INTEGER NOT NULL REFERENCES produtos(id),
    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
    preco_unitario NUMERIC(10, 2) NOT NULL CHECK (preco_unitario >= 0),  -- preço congelado
    UNIQUE (pedido_id, produto_id)
);

CREATE TABLE IF NOT EXISTS historico_status_pedido (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id),
    status_anterior VARCHAR(30)
        CHECK (status_anterior IS NULL OR status_anterior IN (
            'AGUARDANDO_CONFIRMACAO', 'CONFIRMADO',
            'ENVIADO', 'ENTREGUE', 'CANCELADO')),
    status_novo VARCHAR(30) NOT NULL
        CHECK (status_novo IN (
            'AGUARDANDO_CONFIRMACAO', 'CONFIRMADO',
            'ENVIADO', 'ENTREGUE', 'CANCELADO')),
    data_hora TIMESTAMP NOT NULL DEFAULT NOW(),
    observacao VARCHAR(255)
);

-- ---------------------------------------------------------------------
-- MOVIMENTAÇÕES DE ESTOQUE (auditoria)
-- quantidade é sempre positiva, exceto em AJUSTE (positivo ou negativo)
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS movimentacoes_estoque (
    id SERIAL PRIMARY KEY,
    produto_id INTEGER NOT NULL REFERENCES produtos(id),
    pedido_id INTEGER REFERENCES pedidos(id),   -- nulo em entradas e ajustes
    tipo VARCHAR(30) NOT NULL
        CHECK (tipo IN ('ENTRADA', 'SAIDA_VENDA', 'ESTORNO_CANCELAMENTO', 'AJUSTE')),
    quantidade INTEGER NOT NULL,
    data_hora TIMESTAMP NOT NULL DEFAULT NOW(),
    observacao VARCHAR(255),
    CONSTRAINT ck_mov_quantidade CHECK (
        quantidade <> 0 AND (tipo = 'AJUSTE' OR quantidade > 0)
    ),
    CONSTRAINT ck_mov_pedido CHECK (
        tipo NOT IN ('SAIDA_VENDA', 'ESTORNO_CANCELAMENTO')
        OR pedido_id IS NOT NULL
    )
);

-- ---------------------------------------------------------------------
-- ÍNDICES (chaves estrangeiras e filtros dos relatórios)
-- ---------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_produtos_categoria
    ON produtos (categoria_id);

CREATE INDEX IF NOT EXISTS idx_enderecos_cliente
    ON enderecos (cliente_id);

CREATE INDEX IF NOT EXISTS idx_pedidos_cliente
    ON pedidos (cliente_id);

CREATE INDEX IF NOT EXISTS idx_pedidos_status_confirmacao
    ON pedidos (status, data_confirmacao);

CREATE INDEX IF NOT EXISTS idx_itens_pedido_produto
    ON itens_pedido (produto_id);

CREATE INDEX IF NOT EXISTS idx_historico_pedido
    ON historico_status_pedido (pedido_id, data_hora);

CREATE INDEX IF NOT EXISTS idx_mov_estoque_produto
    ON movimentacoes_estoque (produto_id, data_hora);

CREATE INDEX IF NOT EXISTS idx_mov_estoque_pedido
    ON movimentacoes_estoque (pedido_id);