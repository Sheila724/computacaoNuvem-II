# Projeto Mensageria - Marketplace

**Computacao em Nuvem II** - FATEC DSM 6o semestre

**Equipe:** Gabriel Fillip | Leonardo Cassio | Sheila Alves

---

## 1. Arquitetura do Sistema

Sistema de mensageria para um marketplace. Consome pedidos publicados pelo professor no **GCP Pub/Sub**, persiste os dados em **PostgreSQL** e disponibiliza uma **API REST** com **frontend web** para consulta.

![Arquitetura do Sistema](Documenta%C3%A7%C3%A3o/arquitetura_pubsub_pipeline.png)

### Stack Tecnologica

| Componente     | Tecnologia                        | Porta  |
|----------------|-----------------------------------|--------|
| Consumer       | Node.js + @google-cloud/pubsub    | -      |
| API REST       | Python 3 + FastAPI + SQLAlchemy   | 8000   |
| Frontend       | HTML/CSS/JS (servido pela API)    | 8000   |
| Banco de Dados | PostgreSQL 18                     | 5432   |
| Mensageria     | GCP Pub/Sub (serjava-demo)        | -      |

---

## 2. Consumer JavaScript

O consumer e o componente central do projeto. Ele escuta mensagens da subscription `sub-grupo1` do GCP Pub/Sub e persiste cada pedido no PostgreSQL.

### Fluxo de processamento

1. Conecta ao PostgreSQL via Sequelize e sincroniza os modelos
2. Cria um subscriber na subscription `sub-grupo1` do projeto `serjava-demo`
3. Para cada mensagem recebida:
   - Faz **parse** do JSON do pedido
   - Valida campos obrigatorios (uuid, customer.id, items)
   - Abre uma **transaction** no banco
   - **Upsert** do cliente (pelo `customer.id`)
   - **Upsert** de cada produto (pelo `product_id` dos items)
   - **Upsert** do pedido (pelo `uuid`) com `indexed_at = new Date()`
   - **Insert** de cada item do pedido
   - Faz `message.ack()` em caso de sucesso
   - Faz `message.nack()` em caso de erro (reprocessamento automatico)

### Tratamento de duplicatas

Pedidos com mesmo UUID sao tratados via upsert — se o pedido ja existe, os dados sao atualizados sem gerar duplicata.

### Volume processado

O consumer processou com sucesso **185.882 pedidos** enviados pelo professor, demonstrando a robustez do pipeline.

### Configuracao

```bash
cd consumer-js
npm install
node src/index.js
```

Requer o arquivo `service-account-key.json` com credenciais do service account `sa-pubsub-grupo1@serjava-demo.iam.gserviceaccount.com`.

---

## 3. Banco de Dados PostgreSQL

Database `mensageria_pubsub` com 4 tabelas relacionais.

### Diagrama Conceitual

![Diagrama Conceitual](Documenta%C3%A7%C3%A3o/Diagrama%20Conceitual%20BD.png)

### Diagrama Logico

![Diagrama Logico](Documenta%C3%A7%C3%A3o/Diagrama%20Logico%20BD.png)

### Tabelas

#### cliente
| Coluna    | Tipo         | Constraints                         |
|-----------|-------------|-------------------------------------|
| id        | INTEGER     | PRIMARY KEY                         |
| nome      | VARCHAR(255)| NOT NULL                            |
| email     | VARCHAR(255)|                                     |
| documento | VARCHAR(20) | NOT NULL DEFAULT '987.654.321-00'   |

#### produto
| Coluna            | Tipo         | Constraints |
|-------------------|-------------|-------------|
| id                | INTEGER     | PRIMARY KEY |
| nome              | VARCHAR(255)| NOT NULL    |
| categoria_id      | VARCHAR(20) |             |
| categoria_nome    | VARCHAR(100)|             |
| subcategoria_id   | VARCHAR(20) |             |
| subcategoria_nome | VARCHAR(100)|             |

#### pedido
| Coluna                 | Tipo                      | Constraints           |
|------------------------|---------------------------|-----------------------|
| uuid                   | VARCHAR(50)               | PRIMARY KEY           |
| created_at             | TIMESTAMP WITH TIME ZONE  |                       |
| channel                | VARCHAR(50)               |                       |
| status                 | VARCHAR(20)               |                       |
| cliente_id             | INTEGER                   | FK -> cliente(id)     |
| seller_id              | INTEGER                   |                       |
| seller_nome            | VARCHAR(255)              |                       |
| seller_cidade          | VARCHAR(100)              |                       |
| seller_estado          | VARCHAR(5)                |                       |
| shipment_carrier       | VARCHAR(100)              |                       |
| shipment_service       | VARCHAR(50)               |                       |
| shipment_status        | VARCHAR(50)               |                       |
| shipment_tracking      | VARCHAR(100)              |                       |
| payment_method         | VARCHAR(50)               |                       |
| payment_status         | VARCHAR(50)               |                       |
| payment_transaction_id | VARCHAR(100)              |                       |
| metadata               | JSONB                     |                       |
| indexed_at             | TIMESTAMP WITH TIME ZONE  | DEFAULT NOW()         |

#### item_pedido
| Coluna            | Tipo          | Constraints              |
|-------------------|--------------|--------------------------|
| id                | SERIAL       | PRIMARY KEY              |
| pedido_uuid       | VARCHAR(50)  | FK -> pedido(uuid)       |
| product_id        | INTEGER      | FK -> produto(id)        |
| product_name      | VARCHAR(255) |                          |
| unit_price        | NUMERIC(12,2)|                          |
| quantity          | INTEGER      |                          |
| categoria_id      | VARCHAR(20)  |                          |
| categoria_nome    | VARCHAR(100) |                          |
| subcategoria_id   | VARCHAR(20)  |                          |
| subcategoria_nome | VARCHAR(100) |                          |

### Relacionamentos

- `pedido.cliente_id` -> `cliente.id` (N pedidos : 1 cliente)
- `item_pedido.pedido_uuid` -> `pedido.uuid` (N itens : 1 pedido)
- `item_pedido.product_id` -> `produto.id` (N itens : 1 produto)

### Queries uteis para verificacao

```sql
-- Total de pedidos no banco
SELECT COUNT(*) FROM pedido;

-- Total de clientes distintos
SELECT COUNT(*) FROM cliente;

-- Total de produtos distintos
SELECT COUNT(DISTINCT product_id) FROM item_pedido;

-- Distribuicao por status
SELECT status, COUNT(*) FROM pedido GROUP BY status ORDER BY COUNT(*) DESC;

-- Pedidos por canal
SELECT channel, COUNT(*) FROM pedido GROUP BY channel;
```

### Aplicar migrations

```bash
psql -U postgres -d mensageria_pubsub -f database/migrations/001_create_tables.sql
```

---

## 4. API REST (FastAPI/Python)

A API expoe os dados persistidos pelo consumer atraves de endpoints REST com paginacao, filtros e ordenacao.

### Endpoints

#### GET /orders

Lista pedidos com suporte a filtros, paginacao e ordenacao.

| Parametro     | Tipo   | Default    | Descricao                       |
|---------------|--------|------------|---------------------------------|
| codigoCliente | int    | -          | Filtrar por ID do cliente       |
| product_id    | int    | -          | Filtrar por ID do produto       |
| status        | string | -          | Filtrar por status do pedido    |
| page          | int    | 1          | Pagina atual                    |
| pageSize      | int    | 10         | Itens por pagina (max 100)      |
| sortBy        | string | created_at | Campo de ordenacao              |
| sortOrder     | string | desc       | Direcao: asc ou desc            |

**Status validos:** `created`, `paid`, `separated`, `shipped`, `delivered`, `canceled`

#### GET /orders/:uuid

Retorna um pedido especifico pelo UUID com todos os dados aninhados.

### Contrato de resposta (payload)

Cada pedido segue exatamente o contrato definido pelo professor:

```json
{
  "uuid": "ORD-2025-0001",
  "created_at": "2025-10-01T10:15:00Z",
  "channel": "mobile_app",
  "total": 5000.00,
  "status": "separated",
  "customer": {
    "id": 7788,
    "name": "Maria Oliveira",
    "email": "maria@email.com",
    "document": "987.654.321-00"
  },
  "seller": {
    "id": 55,
    "name": "Tech Store",
    "city": "Sao Paulo",
    "state": "SP"
  },
  "items": [
    {
      "id": 1,
      "product_id": 9001,
      "product_name": "Smartphone X",
      "unit_price": 2500.00,
      "quantity": 2,
      "category": {
        "id": "ELEC",
        "name": "Eletronicos",
        "sub_category": {
          "id": "PHONE",
          "name": "Smartphones"
        }
      },
      "total": 5000.00
    }
  ],
  "shipment": {
    "carrier": "Correios",
    "service": "SEDEX",
    "status": "shipped",
    "tracking_code": "BR123456789"
  },
  "payment": {
    "method": "pix",
    "status": "approved",
    "transaction_id": "pay_987654321"
  },
  "metadata": {
    "source": "app",
    "user_agent": "Mozilla/5.0...",
    "ip_address": "10.0.0.1"
  }
}
```

### Regras de negocio

- **Total do pedido**: calculado dinamicamente como `SUM(unit_price * quantity)` dos itens — nao e armazenado no banco
- **Total do item**: calculado como `unit_price * quantity`
- **indexed_at**: timestamp de quando o consumer persistiu a mensagem (rastreabilidade)

### Exemplos de requisicao

```
GET /orders
GET /orders?status=created
GET /orders?codigoCliente=7788
GET /orders?product_id=9001&page=2&pageSize=20
GET /orders?sortBy=created_at&sortOrder=asc
GET /orders/ORD-2025-0001
```

### Executar a API

```bash
cd api-python
pip install -r requirements.txt
python main.py
# Disponivel em http://localhost:8000
# Swagger UI em http://localhost:8000/docs
```

---

## 5. Frontend (Dashboard)

Dashboard web servido pela propria API em `http://localhost:8000/app`.

### Funcionalidades

- **Tabela de pedidos** com colunas: UUID, cliente, canal, status, total, data
- **Paginacao** com controle de pagina e itens por pagina
- **Filtros**: por UUID, ID do cliente, ID do produto e status
- **Ordenacao**: por data, total ou status (asc/desc)
- **Modal de detalhes**: ao clicar em um pedido, exibe todas as informacoes:
  - Dados do cliente (nome, email, documento)
  - Dados do vendedor (nome, cidade, estado)
  - Tabela de itens com precos e categorias
  - Informacoes de envio (transportadora, rastreio)
  - Informacoes de pagamento (metodo, status, transacao)
  - Metadata (source, user_agent, ip)
- **Status com badges coloridos**:
  - `created` / `pending` = azul
  - `paid` = verde
  - `separated` = laranja
  - `shipped` = roxo
  - `delivered` = teal
  - `canceled` = vermelho
- Formatacao monetaria em **R$ (BRL)** e datas em **pt-BR**

---

## 6. Como Executar o Projeto Completo

### Pre-requisitos

- Node.js 18+
- Python 3.10+
- PostgreSQL rodando na porta 5432
- Arquivo `service-account-key.json` na pasta `consumer-js/`

### Passo a passo

```bash
# 1. Banco de dados (se usar Docker)
docker run -d --name postgresql-projeto \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=mensageria_pubsub \
  -p 5432:5432 postgres:18

# 2. Criar tabelas
psql -U postgres -d mensageria_pubsub -f database/migrations/001_create_tables.sql

# 3. Consumer (consome mensagens do Pub/Sub)
cd consumer-js
npm install
node src/index.js

# 4. API + Frontend
cd api-python
pip install -r requirements.txt
python main.py
```

### Acessos

| Recurso          | URL                                |
|------------------|------------------------------------|
| Dashboard        | http://localhost:8000/app           |
| API REST         | http://localhost:8000/orders        |
| Swagger (docs)   | http://localhost:8000/docs          |

### Variaveis de ambiente

Criar `.env` em `consumer-js/` e `api-python/`:

```env
# Consumer JS
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mensageria_pubsub
DB_USER=postgres
DB_PASSWORD=postgres
PUBSUB_PROJECT_ID=serjava-demo
PUBSUB_SUBSCRIPTION=sub-grupo1
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json

# API Python
DB_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/mensageria_pubsub
```

---

## Estrutura do Repositorio

```
computacaoNuvem-II/
  README.md
  consumer-js/                 Consumer Pub/Sub (Node.js)
    src/
      index.js                 Entry point
      config/database.js       Conexao Sequelize
      config/pubsub.js         Cliente Pub/Sub
      models/                  Modelos: Pedido, Cliente, Produto, ItemPedido
      handlers/orderHandler.js Parse e persistencia
  api-python/                  API REST (FastAPI)
    main.py                    Endpoints e logica
    requirements.txt           Dependencias Python
  frontend/
    index.html                 Dashboard completo (single-file)
  database/
    migrations/                DDL das tabelas
    seed/                      Dados de teste
    diagram/                   DER (diagrama ER)
  Documentacao/                Roteiro de apresentacao e docs
```
