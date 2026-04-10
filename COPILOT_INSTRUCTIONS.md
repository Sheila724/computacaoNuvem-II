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

## Ultima atualizacao: 2026-04-09 | IA: GitHub Copilot (GPT-5.3-Codex)

### O que foi feito nesta sessao:
- Revisao dos requisitos de entrega x implementacao atual
- Ajustada resiliencia do consumer em `consumer-js/src/handlers/orderHandler.js`:
  - validacao de payload obrigatorio (uuid, customer.id, items, campos de item)
  - mensagens malformadas agora sao descartadas com `ack` para evitar loop infinito
- Ajustada API Python em `api-python/main.py`:
  - correcao da ordenacao por `total` com calculo dinamico via SQL
  - correcao do `id` dos itens para usar o id real da tabela `item_pedido`
  - normalizacao de datetime para UTC com sufixo `Z`
  - filtro por `product_id` com `EXISTS` (evita duplicidade e melhora consistencia)
- Criado DER em Mermaid em `database/diagram/DER.mmd` para facilitar exportacao de `DER.png`
- Documentado no README e neste guia que `consumer-js/publisher.js` e utilitario opcional (nao obrigatorio)
- Padronizado `consumer-js/publisher.js` para aceitar `PUBSUB_PROJECT_ID` (fallback `PROJECT_ID`) e `PUBSUB_TOPIC` opcional
- Atualizado este arquivo de instrucoes com estado atual da sessao

### O que falta fazer:
1. Rodar `npm install` em `consumer-js/` e `api-js/` (se ainda nao instalado no ambiente atual)
2. Criar/validar `.env` em `consumer-js/` e `api-js/` a partir do `.env.example`
3. Executar migration no PostgreSQL e validar schema final
4. Testar fluxo fim a fim: Pub/Sub -> consumer -> PostgreSQL -> GET /orders
5. Exportar `database/diagram/DER.mmd` para `database/diagram/DER.png`
6. Garantir commits de todos os 3 membros para requisito final de entrega

### Arquivos que estavam sendo editados:
- consumer-js/src/handlers/orderHandler.js
- api-python/main.py
- database/diagram/DER.mmd
- COPILOT_INSTRUCTIONS.md

### Bugs/erros conhecidos:
- Nao ha bug conhecido introduzido nesta sessao
- Fluxo completo ainda precisa de teste integrado no ambiente com Pub/Sub e PostgreSQL ativos

### Proximos passos recomendados:
1. Rodar consumer: `cd consumer-js && node src/index.js`
2. Publicar mensagem de teste e validar insercao nas 4 tabelas
3. Subir API e validar `GET /orders`, `GET /orders/{uuid}` e filtros obrigatorios
4. Gerar `DER.png` a partir do Mermaid e anexar na entrega

---

# ===================================================================
# LOG DE PROGRESSO (adicionar entradas no topo, mais recente primeiro)
# ===================================================================

## [2026-04-09] GitHub Copilot (GPT-5.3-Codex) - Padronizacao de variaveis do publisher
- `consumer-js/publisher.js` ajustado para priorizar `PUBSUB_PROJECT_ID` (com fallback `PROJECT_ID`)
- `consumer-js/publisher.js` ajustado para aceitar `PUBSUB_TOPIC` opcional (fallback `TOPIC_NAME` e `pedidos-topic`)
- `consumer-js/.env.example` atualizado com `PUBSUB_TOPIC`
- `README.md` e `COPILOT_INSTRUCTIONS.md` atualizados para esclarecer variaveis esperadas do publisher

## [2026-04-09] GitHub Copilot (GPT-5.3-Codex) - Ajustes de conformidade dos requisitos
- Revisados requisitos do enunciado e plano de sprint em relacao ao codigo atual
- `consumer-js/src/handlers/orderHandler.js` atualizado para resiliencia:
  - validacao de payload obrigatorio
  - descarte com `ack` de mensagem malformada para evitar reprocessamento infinito
- `api-python/main.py` atualizado para contrato e regras:
  - ordenacao por total com calculo dinamico (sem depender de coluna inexistente)
  - uso do id real de `item_pedido` na resposta
  - normalizacao de data para UTC
  - filtro de produto com `EXISTS`
- Criado `database/diagram/DER.mmd` com relacionamentos obrigatorios
- `COPILOT_INSTRUCTIONS.md` atualizado com o estado atual da sessao

## [2026-04-09] GitHub Copilot (GPT-5.3-Codex) - Documentacao do publisher opcional
- `README.md` atualizado para explicitar `consumer-js/publisher.js` como utilitario de teste
- `COPILOT_INSTRUCTIONS.md` atualizado na secao de execucao com o mesmo direcionamento
- Mantida a regra: publisher e opcional e nao bloqueia requisito obrigatorio da entrega

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
