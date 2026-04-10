# ===================================================================
# INSTRUCOES PARA QUALQUER IA / COPILOT / ASSISTENTE DE CODIGO
# ===================================================================
#
# LEIA ESTE ARQUIVO INTEIRO ANTES DE ESCREVER QUALQUER CODIGO.
# Este arquivo e a fonte de verdade do projeto. Toda IA que trabalhar
# aqui DEVE seguir estas regras.
#
# ===================================================================

# REGRA ZERO - OBRIGATORIO

## 1. ATUALIZE ESTE ARQUIVO
Sempre que voce fizer qualquer alteracao no projeto (criar arquivo, modificar codigo,
adicionar dependencia, mudar schema, etc.), ATUALIZE a secao "LOG DE PROGRESSO" no
final deste arquivo com:
- O que foi feito
- Quais arquivos foram criados/modificados
- Data e hora (se disponivel)
- Qual IA realizou a tarefa (Claude, ChatGPT, Copilot, Gemini, etc.)

## 2. INDIQUE ONDE PAROU
Ao final de TODA sessao de trabalho, escreva na secao "ONDE PAREI" exatamente:
- Qual tarefa estava sendo feita
- O que falta para completar
- Quais arquivos estavam sendo editados
- Se ha algum erro/bug pendente
- Proximos passos recomendados

Isso garante que a proxima IA (ou humano) que abrir o projeto saiba
exatamente de onde retomar.

## 3. NAO QUEBRE O QUE JA FUNCIONA
Antes de alterar qualquer arquivo existente, leia-o por completo.
Nao sobrescreva codigo funcional sem necessidade.

## 4. NAO COMMITE CREDENCIAIS
O arquivo `service-account-key.json` e `.env` estao no `.gitignore`.
NUNCA inclua chaves, senhas ou tokens em arquivos commitados.

---

# CONTEXTO DO PROJETO

## O que e este projeto?
Sistema de mensageria para marketplace - trabalho da FATEC (Computacao em Nuvem 2).

**Duas partes principais:**
1. **Consumer (consumer-js/)**: Le mensagens de pedidos do GCP Pub/Sub e salva no PostgreSQL
2. **API REST**: Consulta pedidos com paginacao, filtros e ordenacao
   - `api-python/` = implementacao principal (FastAPI) - JA FUNCIONAL
   - `api-js/` = implementacao bonus (Express.js)

## Equipe
- Gabriel Fillip
- Leonardo Cassio
- Sheila Alves

## Stack
- **Consumer**: Node.js + @google-cloud/pubsub + Sequelize
- **API principal**: Python + FastAPI + SQLAlchemy
- **API bonus**: Node.js + Express.js + Sequelize
- **Banco**: PostgreSQL (database: `mensageria_pubsub`)
- **Cloud**: GCP Pub/Sub (projeto: `serjava-demo`, subscription: `sub-grupo1`)

---

# ESTRUTURA DE PASTAS

```
computacaoNuvem-II/
  CLAUDE.md                      # Instrucoes especificas para Claude
  COPILOT_INSTRUCTIONS.md        # ESTE ARQUIVO - instrucoes universais
  .gitignore
  api-python/                    # API REST Python (FastAPI) - FUNCIONAL
    main.py                      # Servidor principal (porta 8000)
    requirements.txt             # fastapi, uvicorn, sqlalchemy, psycopg2-binary
    migrations/
  consumer-js/                   # Consumer Pub/Sub JavaScript
    package.json                 # @google-cloud/pubsub, sequelize, pg, dotenv
    .env.example
    src/
      index.js                   # Entry point
      config/
        database.js              # Conexao Sequelize
        pubsub.js                # Cliente Pub/Sub
      models/
        index.js                 # Modelos + associacoes
        Pedido.js
        Cliente.js
        Produto.js
        ItemPedido.js
      handlers/
        orderHandler.js          # Parse da mensagem + persistencia em transaction
  api-js/                        # API REST Express.js (bonus)
    package.json                 # express, sequelize, pg, cors, dotenv
    .env.example
    src/
      index.js                   # Servidor Express (porta 3000)
      config/database.js
      models/                    # Mesmos modelos do consumer-js
      routes/orders.js           # GET /orders e GET /orders/:uuid
      middlewares/errorHandler.js
  database/
    migrations/001_create_tables.sql   # DDL das 4 tabelas
    seed/sample_message.json           # Mensagem exemplo do Pub/Sub
    diagram/DER.png                    # Diagrama ER (a criar)
  Documentacao/
    Nuvem - Atividade Mensageria 2026.pdf   # Enunciado do professor
    Plano_Sprints_Mensageria.pdf            # Plano de sprints da equipe
```

---

# BANCO DE DADOS - SCHEMA

4 tabelas obrigatorias. **NAO altere nomes de colunas** sem consultar a equipe.

## cliente
| Coluna    | Tipo         | Constraints                          |
|-----------|-------------|--------------------------------------|
| id        | INTEGER     | PRIMARY KEY                          |
| nome      | VARCHAR(255)| NOT NULL                             |
| email     | VARCHAR(255)|                                      |
| documento | VARCHAR(20) | NOT NULL DEFAULT '987.654.321-00'    |

## produto
| Coluna            | Tipo         | Constraints   |
|-------------------|-------------|---------------|
| id                | INTEGER     | PRIMARY KEY   |
| nome              | VARCHAR(255)| NOT NULL      |
| categoria_id      | VARCHAR(20) |               |
| categoria_nome    | VARCHAR(100)|               |
| subcategoria_id   | VARCHAR(20) |               |
| subcategoria_nome | VARCHAR(100)|               |

## pedido
| Coluna                   | Tipo                     | Constraints           |
|--------------------------|-------------------------|-----------------------|
| uuid                     | VARCHAR(50)             | PRIMARY KEY           |
| created_at               | TIMESTAMP WITH TIME ZONE|                       |
| channel                  | VARCHAR(50)             |                       |
| status                   | VARCHAR(20)             |                       |
| cliente_id               | INTEGER                 | FK -> cliente(id)     |
| seller_id                | INTEGER                 |                       |
| seller_nome              | VARCHAR(255)            |                       |
| seller_cidade            | VARCHAR(100)            |                       |
| seller_estado            | VARCHAR(5)              |                       |
| shipment_carrier         | VARCHAR(100)            |                       |
| shipment_service         | VARCHAR(50)             |                       |
| shipment_status          | VARCHAR(50)             |                       |
| shipment_tracking        | VARCHAR(100)            |                       |
| payment_method           | VARCHAR(50)             |                       |
| payment_status           | VARCHAR(50)             |                       |
| payment_transaction_id   | VARCHAR(100)            |                       |
| metadata                 | JSONB                   |                       |
| indexed_at               | TIMESTAMP WITH TIME ZONE| DEFAULT NOW()         |

## item_pedido
| Coluna            | Tipo          | Constraints           |
|-------------------|--------------|------------------------|
| id                | SERIAL       | PRIMARY KEY            |
| pedido_uuid       | VARCHAR(50)  | FK -> pedido(uuid)     |
| product_id        | INTEGER      | FK -> produto(id)      |
| product_name      | VARCHAR(255) |                        |
| unit_price        | NUMERIC(12,2)|                        |
| quantity          | INTEGER      |                        |
| categoria_id      | VARCHAR(20)  |                        |
| categoria_nome    | VARCHAR(100) |                        |
| subcategoria_id   | VARCHAR(20)  |                        |
| subcategoria_nome | VARCHAR(100) |                        |

## Relacionamentos
- pedido.cliente_id -> cliente.id (N:1)
- item_pedido.pedido_uuid -> pedido.uuid (N:1)
- item_pedido.product_id -> produto.id (N:1)

---

# CONTRATO DA API - RESPOSTA OBRIGATORIA

A API DEVE retornar EXATAMENTE este formato. Nao mude nomes de campos.

## GET /orders/:uuid (pedido unico)

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

## GET /orders (listagem paginada)

```json
{
  "orders": [ ],
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

## Filtros obrigatorios
| Param         | Tipo   | Default      | Exemplo                        |
|---------------|--------|-------------|--------------------------------|
| codigoCliente | int    | null        | /orders?codigoCliente=7788     |
| product_id    | int    | null        | /orders?product_id=9001        |
| status        | string | null        | /orders?status=created         |
| page          | int    | 1           | /orders?page=2                 |
| pageSize      | int    | 10 (max 100)| /orders?pageSize=20           |
| sortBy        | string | created_at  | /orders?sortBy=status          |
| sortOrder     | string | desc        | /orders?sortOrder=asc          |

## Status validos
`created`, `paid`, `separated`, `shipped`, `delivered`, `canceled`

## REGRAS DE CALCULO
- **total do pedido** = SUM(unit_price * quantity) de todos os items -> CALCULADO, NAO ARMAZENADO
- **total do item** = unit_price * quantity -> CALCULADO, NAO ARMAZENADO
- **indexed_at** = timestamp de quando o consumer salvou no banco

---

# CONSUMER JS - REGRAS

1. Conectar ao Pub/Sub: projeto `serjava-demo`, subscription `sub-grupo1`
2. Credenciais: `GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json`
3. Ao receber mensagem:
   - Parsear JSON
   - UPSERT cliente (pelo id)
   - UPSERT produto (pelo product_id de cada item)
   - UPSERT pedido com indexed_at = new Date()
   - DELETE + INSERT items do pedido (para reprocessamento)
   - Tudo em TRANSACTION
4. message.ack() apos sucesso
5. message.nack() apos erro
6. A mensagem Pub/Sub segue o mesmo formato do payload da API acima

---

# VARIAVEIS DE AMBIENTE

Criar `.env` a partir do `.env.example` em cada subpasta.

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mensageria_pubsub
DB_USER=postgres
DB_PASSWORD=(ver com a equipe)
PUBSUB_PROJECT_ID=serjava-demo
PUBSUB_SUBSCRIPTION=sub-grupo1
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
PORT=3000  (apenas para api-js)

# API Python usa DB_URL (obrigatorio - sem fallback):
DB_URL=postgresql+psycopg2://postgres:SENHA@localhost:5432/mensageria_pubsub
```

---

# CONVENCOES

- JavaScript: const/let, async/await, camelCase
- Modelos Sequelize: PascalCase (ex: Pedido), colunas snake_case (ex: created_at)
- Python: snake_case, type hints quando possivel
- Commits: mensagens em portugues, descritivas
- Branch: main (projeto academico)

---

# COMO RODAR

## Consumer JS
```bash
cd consumer-js
cp .env.example .env   # editar com credenciais corretas
npm install
node src/index.js
```

### Publisher de teste (opcional)
`consumer-js/publisher.js` existe apenas como utilitario para testes locais de publicacao.
- Nao e requisito obrigatorio do projeto.
- Pode ser usado para validar o fluxo fim a fim quando ambiente estiver pronto.
- Variaveis esperadas: `PUBSUB_PROJECT_ID` (ou `PROJECT_ID`), `GOOGLE_APPLICATION_CREDENTIALS` e opcionalmente `PUBSUB_TOPIC`.

```bash
cd consumer-js
node publisher.js
```

## API Python (principal)
```bash
cd api-python
pip install -r requirements.txt
# OBRIGATORIO: definir DB_URL (nao tem mais fallback hardcoded)
export DB_URL="postgresql+psycopg2://postgres:SENHA@localhost:5432/mensageria_pubsub"
python main.py
# http://localhost:8000
```

## API JS (bonus)
```bash
cd api-js
cp .env.example .env
npm install
node src/index.js
# http://localhost:3000
```

---

# ===================================================================
# ONDE PAREI (atualizar sempre ao final de cada sessao)
# ===================================================================

## Ultima atualizacao: 2026-04-10 | IA: Claude (Opus 4.6) + GitHub Copilot (GPT-5.3-Codex)

### O que foi feito nas sessoes recentes:
- Revisao dos requisitos de entrega x implementacao atual (Copilot)
- Ajustada resiliencia do consumer: validacao de payload, descarte de msgs malformadas (Copilot)
- Ajustada API Python: ordenacao por total dinamico, id real de item_pedido, datetime UTC, filtro EXISTS (Copilot)
- Criado DER em Mermaid: `database/diagram/DER.mmd` (Copilot)
- Criado publisher.js utilitario opcional para testes (Copilot)
- Analisado commits da Sheila, atualizado docs, criado README.md (Claude)
- PostgreSQL reinstalado, banco criado, migrations executadas (Claude)
- Modelos Sequelize validados com references nas FKs (Claude)
- Handler testado: upsert, idempotencia, transaction OK (Claude)
- Consumer testado: conexao Pub/Sub OK (depende permissao GCP) (Claude)

### O que falta fazer:
1. ~~Rodar migrations no PostgreSQL~~ FEITO (banco criado + 4 tabelas + indices)
2. ~~npm install em consumer-js/~~ FEITO
3. Rodar `npm install` em `api-js/`
4. Exportar `database/diagram/DER.mmd` para `database/diagram/DER.png`
5. Implementar e testar API JS (Express) - Track B
6. Testar fluxo fim a fim: Pub/Sub -> consumer -> PostgreSQL -> GET /orders
7. Garantir commits de todos os 3 membros (Gabriel, Sheila e Leonardo ja tem)

### Arquivos que estavam sendo editados:
- consumer-js/src/handlers/orderHandler.js
- api-python/main.py
- database/diagram/DER.mmd
- COPILOT_INSTRUCTIONS.md

### Bugs/erros conhecidos:
- API Python EXIGE variavel DB_URL (sem fallback) - se nao definir, da erro no startup
- Consumer Pub/Sub depende de permissao da service account no GCP (PERMISSION_DENIED se nao liberado)

### Proximos passos recomendados:
1. Implementar API JS (Express) - Track B do Sprint 1
2. Exportar DER.mmd para DER.png
3. Testar fluxo completo: Pub/Sub -> consumer -> PostgreSQL -> API
4. Preparar entrega final

---

# ===================================================================
# LOG DE PROGRESSO (adicionar entradas no topo, mais recente primeiro)
# ===================================================================

## [2026-04-10] Claude (Opus 4.6) - Merge Leo + resolucao conflitos
- Pull das alteracoes do Leonardo (4 commits)
- Resolucao de conflitos no COPILOT_INSTRUCTIONS.md
- Merge bem-sucedido de ambas as contribuicoes

## [2026-04-09] GitHub Copilot (GPT-5.3-Codex) - Ajustes de conformidade (Leo)
- consumer-js/src/handlers/orderHandler.js: validacao de payload, resiliencia
- api-python/main.py: ordenacao por total dinamico, id real de item_pedido, datetime UTC, filtro EXISTS
- Criado database/diagram/DER.mmd, consumer-js/publisher.js, run.py, start-consumer.py
- README.md expandido com opcoes automatizadas de execucao

## [2026-04-09] Claude (Opus 4.6) - Analise commits Sheila + README + DB setup
- Analisado commits da Sheila, documentado mudancas
- PostgreSQL reinstalado (senha: postgres), banco mensageria_pubsub criado
- Migrations executadas (001_create_tables + fix_cliente_documento)
- Modelos Sequelize validados e testados com dados reais
- Handler testado: upsert, idempotencia, transaction OK

## [2026-04-04 a 2026-04-09] Sheila Alves - Commits manuais
- Commit inicial: api-python/main.py, consumer-js/ (estrutura)
- requirements.txt, refatoracao main.py, remocao credenciais hardcoded
- Migration fix_cliente_documento.sql, correcoes .gitignore

## [2026-04-08] Claude (Opus 4.6) - Sessao inicial
- Analisado projeto existente (api-python/, .gitignore, migrations)
- Planejado sprints (Sprint 0-3) com distribuicao de tarefas por membro
- Executado Sprint 0 completo:
  - CLAUDE.md criado
  - COPILOT_INSTRUCTIONS.md criado
  - .gitignore corrigido
  - Credencial vazada removida do repo
  - database/migrations/001_create_tables.sql criado
  - database/seed/sample_message.json criado
  - consumer-js/ inicializado com estrutura completa
  - api-js/ inicializado com estrutura completa
  - PDF do plano gerado em Documentacao/
- Arquivos criados: 20+
- Arquivos modificados: .gitignore
- Arquivos removidos: Documentacao/Json.txt (credencial), generate_plan_pdf.py (temp)
