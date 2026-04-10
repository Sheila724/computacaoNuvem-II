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
  consumer-js/                 Consumer Pub/Sub (Node.js)
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

- Node.js 18+ (para o consumer)
- Python 3.10+ (para a API)
- Docker (para PostgreSQL - recomendado) OU PostgreSQL instalado localmente
- Arquivo `service-account-key.json` com credenciais GCP na pasta `consumer-js/`

### 🚀 Opção 1: Tudo Automatizado (RECOMENDADO)

Para **testar a API e banco de dados** (sem consumer):

```bash
python run.py
```

Este script irá:
1. ✅ Criar e iniciar PostgreSQL em Docker (se não estiver rodando)
2. ✅ Criar tabelas e inserir dados de teste
3. ✅ Iniciar FastAPI na porta 8000 em background
4. ✅ Abrir menu interativo com 9 testes prontos para usar

**Endpoints testáveis:**
- GET /orders/:uuid
- GET /orders (com filtros, paginação, ordenação)
- Documentação Swagger

---

### 🚀 Opção 2: Rodar o Consumer Pub/Sub

Para **receber mensagens do professor via Google Cloud Pub/Sub**:

```bash
python start-consumer.py
```

Este script irá:
1. ✅ Verificar credenciais GCP (`service-account-key.json`)
2. ✅ Instalar dependências Node.js se necessário
3. ✅ Conectar na subscription `sub-grupo1` do projeto `serjava-demo`
4. ✅ Persistir mensagens de pedidos no PostgreSQL

**Pré-requisitos para o consumer:**
- Arquivo `consumer-js/service-account-key.json` com credenciais válidas
- PostgreSQL rodando (ou começado por `python run.py`)

---

### Manual (Se Preferir Controle Total)

### 1. Banco de Dados

```bash
# Utilizando Docker 
docker run -d --name postgresql-projeto \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=mensageria_pubsub \
  -p 5432:5432 postgres:18

# Criar tabelas
psql -U postgres -d mensageria_pubsub -f database/migrations/001_create_tables.sql

# Inserir dados de teste
psql -U postgres -d mensageria_pubsub -f database/seed/insert_sample_data.sql
```

### 2. API Python

```bash
cd api-python
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
# Disponível em http://localhost:8000
```

### 3. Consumer Node.js

```bash
cd consumer-js
npm install
npm start
```

### 4. API Express.js (bonus)

```bash
cd api-js
npm install
npm start
# Disponível em http://localhost:3000
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

## Referência Rápida

### Acessar a API

- 🌐 **Swagger UI**: http://localhost:8000/docs
- 📖 **ReDoc**: http://localhost:8000/redoc
- 🔗 **API Base**: http://localhost:8000

### Testes com REST Client (VS Code)

Instale a extensão **REST Client** (humao.rest-client) para fazer requisições direto do VS Code.

Crie um arquivo `requests.http` na raiz do projeto:

```http
### Listar todos os pedidos
GET http://localhost:8000/orders

###
### Listar com filtro por cliente
GET http://localhost:8000/orders?codigoCliente=7788

###
### Listar com filtro por status
GET http://localhost:8000/orders?status=separated

###
### Listar com filtro por produto
GET http://localhost:8000/orders?product_id=9001

###
### Testar paginação
GET http://localhost:8000/orders?page=1&pageSize=5

###
### Testar ordenação (descendente)
GET http://localhost:8000/orders?sortBy=created_at&sortOrder=desc

###
### Obter um pedido específico pelo uuid
GET http://localhost:8000/orders/ORD-2025-0001

###
### Testar erro 404
GET http://localhost:8000/orders/NAO-EXISTE

###
### Combinação: cliente + status + paginação
GET http://localhost:8000/orders?codigoCliente=7788&status=separated&page=1&pageSize=10&sortBy=created_at&sortOrder=desc
```

### Verificar Status

```bash
# Ver containers Docker rodando
docker ps

# Ver logs do PostgreSQL
docker logs postgresql-projeto

# Enviar comando SQL direto
docker exec -it postgresql-projeto psql -U postgres -d mensageria_pubsub
```

### Parar Tudo

```bash
# Encerrar run.py ou start-consumer.py
Ctrl + C

# Parar PostgreSQL
docker stop postgresql-projeto
```

### Problemas Comuns

| Problema | Solução |
|----------|---------|
| Porta 5432 já em uso | `docker stop postgresql-projeto` |
| Porta 8000 já em uso | Alterar porta em `run.py` ou usar diferente |
| Erro de conexão DB | Verificar `postgresql-projeto` está rodando (docker ps) |
| Consumer não recebe msgs | Verificar `service-account-key.json` em `consumer-js/` |
| Erro de indent em `run.py` | Usar Python 3.10+ e verificar encoding UTF-8 |

### URLs Úteis

- 📊 PostgreSQL: `localhost:5432`
- 🚀 FastAPI: `http://localhost:8000`
- 🔐 GCP Pub/Sub: Project `serjava-demo`, Subscription `sub-grupo1`
