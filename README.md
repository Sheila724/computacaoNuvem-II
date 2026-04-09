# Projeto Mensageria - Marketplace

Trabalho da disciplina **Computacao em Nuvem II** - FATEC DSM 6o semestre.

Sistema que consome pedidos de um marketplace via **GCP Pub/Sub**, persiste em **PostgreSQL** e expoe uma **API REST** para consulta.

## Equipe

- Gabriel Fillip
- Leonardo Cassio
- Sheila Alves

## Arquitetura

```
GCP Pub/Sub (topic do professor)
        |
        v
  consumer-js/          Node.js - escuta mensagens e persiste no banco
        |
        v
  PostgreSQL (mensageria_pubsub)
        ^
        |
  api-python/           FastAPI - API REST (principal)
  api-js/               Express.js - API REST (bonus)
```

## Estrutura do Projeto

```
computacaoNuvem-II/
  README.md                    Visao geral e guia de execucao
  consumer-js/                 Consumer Pub/Sub (Node.js)
    publisher.js               Utilitario opcional para publicar pedidos de teste
  api-python/                  API REST (FastAPI)
  api-js/                      API REST (Express.js)
  database/
    migrations/                DDL das tabelas
    seed/                      Mensagem exemplo
    diagram/                   Diagrama ER
  Documentacao/                Enunciado e plano de sprints
```

## Stack

| Componente       | Tecnologia                          |
|------------------|-------------------------------------|
| Consumer         | Node.js + @google-cloud/pubsub      |
| API (principal)  | Python + FastAPI + SQLAlchemy        |
| API (bonus)      | Node.js + Express.js + Sequelize     |
| Banco de dados   | PostgreSQL                           |
| Mensageria       | GCP Pub/Sub                          |

## Banco de Dados

Database: `mensageria_pubsub` com 4 tabelas:

- **cliente** - dados do comprador (id, nome, email, documento)
- **produto** - catalogo de produtos com categoria/subcategoria
- **pedido** - pedido completo com seller, shipment, payment e metadata
- **item_pedido** - itens do pedido com preco e quantidade

### Aplicar migrations

```bash
psql -U postgres -d mensageria_pubsub -f database/migrations/001_create_tables.sql
```

## Como Rodar

### Pre-requisitos

- Node.js 18+
- Python 3.10+
- PostgreSQL rodando localmente
- Arquivo `service-account-key.json` com credenciais GCP na raiz do projeto

### 1. Criar o banco

```bash
createdb -U postgres mensageria_pubsub
psql -U postgres -d mensageria_pubsub -f database/migrations/001_create_tables.sql
```

### 2. Consumer (Node.js)

```bash
cd consumer-js
cp .env.example .env    # editar com suas credenciais
npm install
npm start
```

O consumer conecta na subscription `sub-grupo1` do projeto GCP `serjava-demo` e persiste cada mensagem recebida no PostgreSQL.

### 2.1 Publisher de teste (opcional)

O arquivo `consumer-js/publisher.js` e um utilitario de apoio para testes locais do fluxo fim a fim.

- Nao faz parte do requisito obrigatorio da entrega.
- Serve para publicar pedidos de teste no topico e validar integracao com o consumer.
- Variaveis esperadas: `PUBSUB_PROJECT_ID` (ou `PROJECT_ID`), `GOOGLE_APPLICATION_CREDENTIALS` e opcionalmente `PUBSUB_TOPIC`.

```bash
cd consumer-js
node publisher.js
```

Observacao: para funcionar, configure as credenciais GCP e as variaveis de ambiente esperadas pelo script.

### 3. API Python (principal)

```bash
cd api-python
pip install -r requirements.txt
python main.py
# Disponivel em http://localhost:8000
```

### 4. API Express.js (bonus)

```bash
cd api-js
cp .env.example .env    # editar com suas credenciais
npm install
npm start
# Disponivel em http://localhost:3000
```

## Endpoints da API

### GET /orders

Lista pedidos com paginacao e filtros.

| Parametro     | Tipo   | Default    | Descricao              |
|---------------|--------|------------|------------------------|
| codigoCliente | int    | -          | Filtrar por cliente    |
| product_id    | int    | -          | Filtrar por produto    |
| status        | string | -          | Filtrar por status     |
| page          | int    | 1          | Pagina                 |
| pageSize      | int    | 10         | Itens por pagina (max 100) |
| sortBy        | string | created_at | Campo de ordenacao     |
| sortOrder     | string | desc       | asc ou desc            |

**Status validos:** `created`, `paid`, `separated`, `shipped`, `delivered`, `canceled`

Exemplo:
```
GET /orders?codigoCliente=7788&status=created&page=1&pageSize=20&sortBy=created_at&sortOrder=desc
```

### GET /orders/:uuid

Retorna um pedido especifico pelo UUID.

```
GET /orders/ORD-2025-0001
```

## Variaveis de Ambiente

Criar `.env` a partir do `.env.example` em cada subpasta:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mensageria_pubsub
DB_USER=postgres
DB_PASSWORD=sua_senha
PUBSUB_PROJECT_ID=serjava-demo
PUBSUB_SUBSCRIPTION=sub-grupo1
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
```

## Regras de Negocio

- **Total do pedido**: calculado como `SUM(unit_price * quantity)` dos itens (nao armazenado)
- **Total do item**: `unit_price * quantity` (nao armazenado)
- **indexed_at**: timestamp de quando o consumer salvou a mensagem no banco
- Mensagens duplicadas sao tratadas por **upsert** (chave: UUID do pedido)
