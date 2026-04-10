# Projeto Mensageria - FATEC Computacao em Nuvem II

## Visao Geral

Sistema de mensageria para um marketplace. Consome pedidos do **GCP Pub/Sub**, persiste em **PostgreSQL** e expoe uma **API REST** para consulta.

**Equipe**: Gabriel, Leonardo Cassio, Sheila Alves
**Linguagem designada**: JavaScript (Node.js)
**Disciplina**: Computacao em Nuvem 2 - FATEC DSM 6o semestre

---

## Arquitetura

```
GCP Pub/Sub (topic do professor)
        |
        v
  consumer-js/        <-- Node.js subscriber (JS obrigatorio)
        |
        v
  PostgreSQL (mensageria_pubsub)
        ^
        |
  api-python/         <-- FastAPI REST API (entrega existente)
  api-js/             <-- Express.js REST API (bonus/alternativa)
```

## Estrutura do Repositorio

```
computacaoNuvem-II/
  CLAUDE.md                      # Este arquivo
  .gitignore
  api-python/                    # API REST em Python (FastAPI) - funcional
    main.py
    requirements.txt
    migrations/
      001_fix_cliente_documento.sql  # Fix coluna documento (NOT NULL + DEFAULT)
  consumer-js/                   # Consumer Pub/Sub em JavaScript
    package.json
    src/
      index.js                   # Entry point - conecta DB e inicia listener
      config/
        database.js              # Conexao Sequelize com PostgreSQL
        pubsub.js                # Cliente @google-cloud/pubsub
      models/
        index.js                 # Loader e associacoes dos modelos
        Pedido.js
        Cliente.js
        Produto.js
        ItemPedido.js
      handlers/
        orderHandler.js          # Parse da mensagem e persistencia
  api-js/                        # API REST em Express.js (se implementada)
    package.json
    src/
      index.js
      config/database.js
      models/
      routes/orders.js
      middlewares/errorHandler.js
  database/
    migrations/001_create_tables.sql
    seed/sample_message.json
    diagram/DER.png
  Documentacao/
```

---

## GCP Pub/Sub

- **Projeto GCP**: `serjava-demo`
- **Service Account**: `sa-pubsub-grupo1@serjava-demo.iam.gserviceaccount.com`
- **Subscription**: `sub-grupo1`
- **Credenciais**: arquivo `service-account-key.json` na raiz (NAO commitado - esta no .gitignore)
- **Variavel de ambiente**: `GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json`

---

## Banco de Dados PostgreSQL

### Conexao
```
Host: localhost
Port: 5432
Database: mensageria_pubsub
User: postgres
Password: (ver .env)
```

### Schema - 4 Tabelas Obrigatorias

#### cliente
| Coluna    | Tipo         | Constraints                |
|-----------|-------------|----------------------------|
| id        | INTEGER     | PRIMARY KEY                |
| nome      | VARCHAR(255)| NOT NULL                   |
| email     | VARCHAR(255)|                            |
| documento | VARCHAR(20) | NOT NULL DEFAULT '987.654.321-00' |

#### produto
| Coluna            | Tipo         | Constraints   |
|-------------------|-------------|---------------|
| id                | INTEGER     | PRIMARY KEY   |
| nome              | VARCHAR(255)| NOT NULL      |
| categoria_id      | VARCHAR(20) |               |
| categoria_nome    | VARCHAR(100)|               |
| subcategoria_id   | VARCHAR(20) |               |
| subcategoria_nome | VARCHAR(100)|               |

#### pedido
| Coluna                   | Tipo                     | Constraints                    |
|--------------------------|-------------------------|-------------------------------|
| uuid                     | VARCHAR(50)             | PRIMARY KEY                   |
| created_at               | TIMESTAMP WITH TIME ZONE|                               |
| channel                  | VARCHAR(50)             |                               |
| status                   | VARCHAR(20)             |                               |
| cliente_id               | INTEGER                 | FK -> cliente(id)             |
| seller_id                | INTEGER                 |                               |
| seller_nome              | VARCHAR(255)            |                               |
| seller_cidade            | VARCHAR(100)            |                               |
| seller_estado            | VARCHAR(5)              |                               |
| shipment_carrier         | VARCHAR(100)            |                               |
| shipment_service         | VARCHAR(50)             |                               |
| shipment_status          | VARCHAR(50)             |                               |
| shipment_tracking        | VARCHAR(100)            |                               |
| payment_method           | VARCHAR(50)             |                               |
| payment_status           | VARCHAR(50)             |                               |
| payment_transaction_id   | VARCHAR(100)            |                               |
| metadata                 | JSONB                   |                               |
| indexed_at               | TIMESTAMP WITH TIME ZONE| DEFAULT NOW() - hora do consumo|

#### item_pedido
| Coluna            | Tipo          | Constraints                    |
|-------------------|--------------|-------------------------------|
| id                | SERIAL       | PRIMARY KEY                   |
| pedido_uuid       | VARCHAR(50)  | FK -> pedido(uuid)            |
| product_id        | INTEGER      | FK -> produto(id)             |
| product_name      | VARCHAR(255) |                               |
| unit_price        | NUMERIC(12,2)|                               |
| quantity          | INTEGER      |                               |
| categoria_id      | VARCHAR(20)  |                               |
| categoria_nome    | VARCHAR(100) |                               |
| subcategoria_id   | VARCHAR(20)  |                               |
| subcategoria_nome | VARCHAR(100) |                               |

### Associacoes
- `pedido.cliente_id` -> `cliente.id` (N:1)
- `item_pedido.pedido_uuid` -> `pedido.uuid` (N:1)
- `item_pedido.product_id` -> `produto.id` (N:1)

---

## Contrato da API REST

### Endpoints

#### GET /orders/:uuid
Retorna um pedido pelo UUID.
- **404**: `{"error": "Pedido nao encontrado"}`

#### GET /orders
Lista pedidos com paginacao e filtros.

**Query Parameters:**
| Param         | Tipo    | Default    | Descricao              |
|---------------|---------|------------|------------------------|
| codigoCliente | int     | null       | Filtro por cliente ID  |
| product_id    | int     | null       | Filtro por produto ID  |
| status        | string  | null       | Filtro por status      |
| page          | int     | 1          | Pagina atual           |
| pageSize      | int     | 10 (max 100)| Itens por pagina     |
| sortBy        | string  | created_at | Campo de ordenacao     |
| sortOrder     | string  | desc       | asc ou desc            |

**Status validos**: `created`, `paid`, `separated`, `shipped`, `delivered`, `canceled`

### Payload de Resposta (contrato do professor)

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

### Resposta da listagem (GET /orders)

```json
{
  "orders": [ /* array de pedidos no formato acima */ ],
  "pagination": {
    "page": 1,
    "pageSize": 10,
    "totalRecords": 50,
    "totalPages": 5,
    "sortBy": "created_at",
    "sortOrder": "desc"
  }
}
```

### Regras de Negocio
- **total do pedido**: calculado dinamicamente como `SUM(unit_price * quantity)` dos items - NAO armazenado no banco
- **total do item**: calculado como `unit_price * quantity`
- **indexed_at**: timestamp de quando o consumer persistiu a mensagem no banco

---

## Consumer JS - Regras de Implementacao

1. Conectar ao Pub/Sub usando `@google-cloud/pubsub` com service account
2. Escutar subscription `sub-grupo1` do projeto `serjava-demo`
3. Ao receber mensagem JSON de pedido:
   - Fazer **upsert** de `cliente` (pelo id)
   - Fazer **upsert** de `produto` (pelo product_id de cada item)
   - Fazer **insert** de `pedido` com `indexed_at = new Date()`
   - Fazer **insert** de cada `item_pedido`
   - Tudo em uma **transaction**
4. Fazer `message.ack()` apos persistencia bem-sucedida
5. Fazer `message.nack()` em caso de erro (reprocessar)
6. Tratar duplicatas de pedido por UUID (upsert ou ignore)

### Formato esperado da mensagem Pub/Sub
A mensagem recebida segue o mesmo formato do payload da API (ver contrato acima).

---

## Variaveis de Ambiente (.env)

```env
# Consumer JS e API JS usam variaveis separadas:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mensageria_pubsub
DB_USER=postgres
DB_PASSWORD=(ver .env)
PUBSUB_PROJECT_ID=serjava-demo
PUBSUB_SUBSCRIPTION=sub-grupo1
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json

# API Python usa DB_URL (obrigatorio - nao tem mais fallback hardcoded):
DB_URL=postgresql+psycopg2://postgres:SENHA@localhost:5432/mensageria_pubsub
```

---

## Stack Tecnologica

| Componente | Tecnologia |
|------------|-----------|
| Consumer   | Node.js + @google-cloud/pubsub |
| API (principal) | Python + FastAPI + SQLAlchemy |
| API (bonus) | Node.js + Express.js + Sequelize |
| ORM JS     | Sequelize |
| Banco      | PostgreSQL |
| Cloud      | GCP Pub/Sub |

---

## Convencoes de Codigo

- **JavaScript**: usar `const`/`let`, async/await, camelCase para variaveis
- **Modelos Sequelize**: PascalCase para nomes de modelo, snake_case para colunas (match DB)
- **Commits**: mensagens em portugues, descritivas
- **Branches**: trabalhar na main (projeto academico simples)

---

## Como Rodar

### Consumer JS
```bash
cd consumer-js
cp .env.example .env  # configurar variaveis
npm install
node src/index.js
```

### API Python
```bash
cd api-python
pip install -r requirements.txt
# IMPORTANTE: definir DB_URL como variavel de ambiente (nao mais hardcoded)
export DB_URL="postgresql+psycopg2://postgres:SUA_SENHA@localhost:5432/mensageria_pubsub"
python main.py
# Disponivel em http://localhost:8000
```

### API JS (se implementada)
```bash
cd api-js
cp .env.example .env
npm install
node src/index.js
# Disponivel em http://localhost:3000
```
