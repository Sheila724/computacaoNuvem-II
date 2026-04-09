import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
import uvicorn

def _create_db_engine():
    db_url = os.getenv("DB_URL")
    if not db_url:
        raise RuntimeError("DB_URL nao configurada. Defina a URL do banco via variavel de ambiente.")
    return create_engine(db_url)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: inicializa o engine
    app.state.engine = _create_db_engine()
    yield
    # Shutdown: cleanup (se necessario)

app = FastAPI(
    title="API Mensageria - FATEC",
    description="API para consulta de pedidos consumidos via GCP Pub/Sub",
    version="1.0.0",
    lifespan=lifespan
)


def _get_engine():
    engine = getattr(app.state, "engine", None)
    if engine is None:
        raise RuntimeError("Engine do banco nao inicializado.")
    return engine

VALID_ORDER_STATUS = {"created", "paid", "separated", "shipped", "delivered", "canceled"}
VALID_ORDER_SORT_FIELDS = {"created_at": "p.created_at", "total": "total_calc", "status": "p.status"}
VALID_SORT_ORDER = {"asc", "desc"}

def _format_datetime(dt):
    if not dt:
        return None
    if isinstance(dt, str):
        return dt

    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt_utc = dt.astimezone(timezone.utc)
        return dt_utc.isoformat().replace("+00:00", "Z")

    return str(dt)

def _normalize_metadata(metadata_value):
    if isinstance(metadata_value, dict):
        return metadata_value
    if isinstance(metadata_value, str):
        try:
            return json.loads(metadata_value)
        except json.JSONDecodeError:
            return {}
    return {}

def _build_order_payload(conn, pedido_row):
    pedido = dict(pedido_row._mapping)
    
    cliente_row = conn.execute(text("""
        SELECT id, nome, email, documento 
        FROM cliente WHERE id = :cliente_id
    """), {"cliente_id": pedido.get("cliente_id")}).fetchone()
    
    cliente = dict(cliente_row._mapping) if cliente_row else None

    itens = conn.execute(text("""
        SELECT * FROM item_pedido 
        WHERE pedido_uuid = :uuid 
        ORDER BY id
    """), {"uuid": pedido.get("uuid")}).fetchall()

    items_payload = []
    total_pedido = 0.0

    for item in itens:
        item_dict = dict(item._mapping)
        total_item = round(float(item_dict["unit_price"]) * int(item_dict["quantity"]), 2)
        total_pedido += total_item

        items_payload.append({
            "id": item_dict["id"],
            "product_id": item_dict["product_id"],
            "product_name": item_dict["product_name"],
            "unit_price": float(item_dict["unit_price"]),
            "quantity": item_dict["quantity"],
            "category": {
                "id": item_dict.get("categoria_id") or "ELEC",
                "name": item_dict.get("categoria_nome") or "Eletronicos",
                "sub_category": {
                    "id": item_dict.get("subcategoria_id") or "GERAL",
                    "name": item_dict.get("subcategoria_nome") or "Geral"
                }
            },
            "total": total_item
        })

    return {
        "uuid": pedido.get("uuid"),
        "created_at": _format_datetime(pedido.get("created_at")),
        "channel": pedido.get("channel"),
        "total": round(total_pedido, 2),
        "status": pedido.get("status"),
        "customer": {
            "id": cliente["id"] if cliente else pedido.get("cliente_id"),
            "name": cliente["nome"] if cliente else None,
            "email": cliente["email"] if cliente else None,
            "document": cliente.get("documento") if cliente else "987.654.321-00"
        },
        "seller": {
            "id": pedido.get("seller_id"),
            "name": pedido.get("seller_nome"),
            "city": pedido.get("seller_cidade"),
            "state": pedido.get("seller_estado")
        },
        "items": items_payload,
        "shipment": {
            "carrier": pedido.get("shipment_carrier"),
            "service": pedido.get("shipment_service"),
            "status": pedido.get("shipment_status"),
            "tracking_code": pedido.get("shipment_tracking")
        },
        "payment": {
            "method": pedido.get("payment_method"),
            "status": pedido.get("payment_status"),
            "transaction_id": pedido.get("payment_transaction_id")
        },
        "metadata": _normalize_metadata(pedido.get("metadata"))
    }

def _validate_status(status):
    if status is None:
        return None
    normalized = status.lower()
    if normalized not in VALID_ORDER_STATUS:
        raise ValueError(f"Status invalido: {status}. Valores permitidos: {', '.join(sorted(VALID_ORDER_STATUS))}")
    return normalized

def _validate_sort(sort_by, sort_order):
    if sort_by not in VALID_ORDER_SORT_FIELDS:
        raise ValueError(f"sortBy invalido: {sort_by}")
    normalized_order = sort_order.lower()
    if normalized_order not in VALID_SORT_ORDER:
        raise ValueError(f"sortOrder invalido: {sort_order}")
    return VALID_ORDER_SORT_FIELDS[sort_by], normalized_order

@app.get("/orders/{uuid}")
async def get_order(uuid: str = Path(..., description="UUID do pedido")):
    engine = _get_engine()
    with engine.connect() as conn:
        pedido = conn.execute(text("SELECT * FROM pedido WHERE uuid = :uuid"), {"uuid": uuid}).fetchone()
        if not pedido:
            return JSONResponse(status_code=404, content={"error": "Pedido nao encontrado"})
        return _build_order_payload(conn, pedido)

@app.get("/orders")
async def list_orders(
    codigoCliente: int | None = Query(default=None, description="ID do cliente"),
    idProduto: int | None = Query(default=None, alias="product_id", description="ID do produto"),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=10, ge=1, le=100),
    sortBy: str = Query(default="created_at"),
    sortOrder: str = Query(default="desc")
):
    try:
        validated_status = _validate_status(status)
        order_column, order_direction = _validate_sort(sortBy, sortOrder)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})

    offset = (page - 1) * pageSize

    engine = _get_engine()
    with engine.connect() as conn:
        total_registros = conn.execute(text("""
            SELECT COUNT(*)
            FROM pedido p
            WHERE (:codigo_cliente IS NULL OR p.cliente_id = :codigo_cliente)
                AND (:status IS NULL OR p.status = :status)
                AND (
                    :id_produto IS NULL
                    OR EXISTS (
                        SELECT 1
                        FROM item_pedido i
                        WHERE i.pedido_uuid = p.uuid
                            AND i.product_id = :id_produto
                    )
                )
        """), {
            "codigo_cliente": codigoCliente,
            "id_produto": idProduto,
            "status": validated_status
        }).scalar() or 0

        pedidos = conn.execute(text(f"""
                        SELECT p.*,
                                     COALESCE(t.total_calc, 0) AS total_calc
                        FROM pedido p
                        LEFT JOIN (
                                SELECT pedido_uuid,
                                             SUM(unit_price * quantity) AS total_calc
                                FROM item_pedido
                                GROUP BY pedido_uuid
                        ) t ON t.pedido_uuid = p.uuid
                        WHERE (:codigo_cliente IS NULL OR p.cliente_id = :codigo_cliente)
                            AND (:status IS NULL OR p.status = :status)
                            AND (
                                :id_produto IS NULL
                                OR EXISTS (
                                    SELECT 1
                                    FROM item_pedido i
                                    WHERE i.pedido_uuid = p.uuid
                                        AND i.product_id = :id_produto
                                )
                            )
                        ORDER BY {order_column} {order_direction}
                        LIMIT :limit OFFSET :offset
                """), {
            "codigo_cliente": codigoCliente,
            "id_produto": idProduto,
            "status": validated_status,
            "limit": pageSize,
            "offset": offset
        }).fetchall()

        total_paginas = (int(total_registros) + pageSize - 1) // pageSize if total_registros else 0

        return {
            "orders": [_build_order_payload(conn, pedido) for pedido in pedidos],
            "pagination": {
                "page": page,
                "pageSize": pageSize,
                "totalRecords": int(total_registros),
                "totalPages": total_paginas,
                "sortBy": sortBy,
                "sortOrder": order_direction
            }
        }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)