-- Inserir dados de teste baseado em sample_message.json

BEGIN;

-- Inserir cliente
INSERT INTO cliente (id, nome, email, documento) 
VALUES (7788, 'Maria Oliveira', 'maria@email.com', '987.654.321-00')
ON CONFLICT (id) DO UPDATE SET email = 'maria@email.com';

-- Inserir produto
INSERT INTO produto (id, nome, categoria_id, categoria_nome, subcategoria_id, subcategoria_nome) 
VALUES (9001, 'Smartphone X', 'ELEC', 'Eletronicos', 'PHONE', 'Smartphones')
ON CONFLICT (id) DO UPDATE SET nome = 'Smartphone X';

-- Inserir pedido
INSERT INTO pedido (
  uuid, created_at, channel, status, cliente_id, 
  seller_id, seller_nome, seller_cidade, seller_estado,
  shipment_carrier, shipment_service, shipment_status, shipment_tracking,
  payment_method, payment_status, payment_transaction_id,
  metadata, indexed_at
) VALUES (
  'ORD-2025-0001',
  '2025-10-01T10:15:00Z',
  'mobile_app',
  'separated',
  7788,
  55,
  'Tech Store',
  'Sao Paulo',
  'SP',
  'Correios',
  'SEDEX',
  'shipped',
  'BR123456789',
  'pix',
  'approved',
  'pay_987654321',
  '{"source": "app", "user_agent": "Mozilla/5.0...", "ip_address": "10.0.0.1"}',
  NOW()
);

-- Inserir item do pedido
INSERT INTO item_pedido (
  pedido_uuid, product_id, product_name, unit_price, quantity,
  categoria_id, categoria_nome, subcategoria_id, subcategoria_nome
) VALUES (
  'ORD-2025-0001',
  9001,
  'Smartphone X',
  2500.00,
  2,
  'ELEC',
  'Eletronicos',
  'PHONE',
  'Smartphones'
);

COMMIT;
