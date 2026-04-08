-- ============================================
-- Migration 001: Criacao das 4 tabelas obrigatorias
-- Projeto Mensageria - FATEC Computacao em Nuvem II
-- ============================================

BEGIN;

-- 1. Tabela: cliente
CREATE TABLE IF NOT EXISTS cliente (
    id INTEGER PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    documento VARCHAR(20) NOT NULL DEFAULT '987.654.321-00'
);

-- 2. Tabela: produto
CREATE TABLE IF NOT EXISTS produto (
    id INTEGER PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    categoria_id VARCHAR(20),
    categoria_nome VARCHAR(100),
    subcategoria_id VARCHAR(20),
    subcategoria_nome VARCHAR(100)
);

-- 3. Tabela: pedido
CREATE TABLE IF NOT EXISTS pedido (
    uuid VARCHAR(50) PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE,
    channel VARCHAR(50),
    status VARCHAR(20),
    cliente_id INTEGER REFERENCES cliente(id),
    seller_id INTEGER,
    seller_nome VARCHAR(255),
    seller_cidade VARCHAR(100),
    seller_estado VARCHAR(5),
    shipment_carrier VARCHAR(100),
    shipment_service VARCHAR(50),
    shipment_status VARCHAR(50),
    shipment_tracking VARCHAR(100),
    payment_method VARCHAR(50),
    payment_status VARCHAR(50),
    payment_transaction_id VARCHAR(100),
    metadata JSONB,
    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Tabela: item_pedido
CREATE TABLE IF NOT EXISTS item_pedido (
    id SERIAL PRIMARY KEY,
    pedido_uuid VARCHAR(50) REFERENCES pedido(uuid),
    product_id INTEGER REFERENCES produto(id),
    product_name VARCHAR(255),
    unit_price NUMERIC(12,2),
    quantity INTEGER,
    categoria_id VARCHAR(20),
    categoria_nome VARCHAR(100),
    subcategoria_id VARCHAR(20),
    subcategoria_nome VARCHAR(100)
);

-- Indices para performance das queries de filtro
CREATE INDEX IF NOT EXISTS idx_pedido_cliente_id ON pedido(cliente_id);
CREATE INDEX IF NOT EXISTS idx_pedido_status ON pedido(status);
CREATE INDEX IF NOT EXISTS idx_pedido_created_at ON pedido(created_at);
CREATE INDEX IF NOT EXISTS idx_item_pedido_pedido_uuid ON item_pedido(pedido_uuid);
CREATE INDEX IF NOT EXISTS idx_item_pedido_product_id ON item_pedido(product_id);

COMMIT;
