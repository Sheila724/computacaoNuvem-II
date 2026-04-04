import json
import os
from datetime import datetime
from fastapi import FastAPI, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
import uvicorn

app = FastAPI(
    title="API Mensageria - FATEC",
    description="API para consulta de pedidos (GCP Pub/Sub + PostgreSQL)",
    version="1.0.0"
)

engine = create_engine(
    os.getenv("DB_URL", "postgresql+psycopg2://postgres:Gabi0510@localhost:5432/mensageria_pubsub")
)

VALID_ORDER_STATUS = {"created", "paid", "separated", "shipped", "delivered", "canceled"}
VALID_ORDER_SORT_FIELDS = {"created_at": "p.created_at", "total": "p.total", "status": "p.status"}
VALID_SORT_ORDER = {"asc", "desc"}

def _format_datetime(dt: datetime) -> str:
    if dt.tzinfo:
        return dt.isoformat().replace("+00:00", "Z")
    return dt.isoformat() + "Z"

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
    """), {"cliente_id": pedido["cliente_id"]}).fetchone()
    cliente = dict(cliente_row._mapping) if cliente_row else None

    itens = conn.execute(text("""
        SELECT * FROM item_pedido WHERE pedido_uuid = :uuid ORDER BY id
    """), {"uuid": pedido["uuid"]}).fetchall()

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
                "id": item_dict["categoria_id"],
                "name": item_dict["categoria_nome"],
                "sub_category": {
                    "id": item_dict["subcategoria_id"],
                    "name": item_dict["subcategoria_nome"]
                }
            },
            "total": total_item
        })

    return {
        "uuid": pedido["uuid"],
        "created_at": _format_datetime(pedido["created_at"]),
        "channel": pedido["channel"],
        "total": round(total_pedido, 2),
        "status": pedido["status"],
        "customer": {
            "id": cliente["id"] if cliente else pedido["cliente_id"],
            "name": cliente["nome"] if cliente else None,
            "email": cliente["email"] if cliente else None,
            "document": cliente["documento"] if cliente else None
        },
        "seller": {
            "id": pedido["seller_id"],
            "name": pedido["seller_nome"],
            "city": pedido["seller_cidade"],
            "state": pedido["seller_estado"]
        },
        "items": items_payload,
        "shipment": {
            "carrier": pedido["shipment_carrier"],
            "service": pedido["shipment_service"],
            "status": pedido["shipment_status"],
            "tracking_code": pedido["shipment_tracking"]
        },
        "payment": {
            "method": pedido["payment_method"],
            "status": pedido["payment_status"],
            "transaction_id": pedido["payment_transaction_id"]
        },
        "metadata": _normalize_metadata(pedido.get("metadata"))  
    }   

def _validate_status(status: str | None):
    if status is None:
        return None
    normalized = status.lower()
    if normalized not in VALID_ORDER_STATUS:
        raise ValueError(f"Status inválido: {status}. Valores permitidos: {', '.join(sorted(VALID_ORDER_STATUS))}")
    return normalized

def _validate_sort(sort_by: str, sort_order: str):
    if sort_by not in VALID_ORDER_SORT_FIELDS:
        raise ValueError(f"sortBy inválido: {sort_by}")
    normalized_order = sort_order.lower()
    if normalized_order not in VALID_SORT_ORDER:
        raise ValueError(f"sortOrder inválido: {sort_order}")
    return VALID_ORDER_SORT_FIELDS[sort_by], normalized_order

@app.get("/orders/{uuid}")
async def get_order(uuid: str = Path(..., description="UUID do pedido")):
    with engine.connect() as conn:
        pedido = conn.execute(text("SELECT * FROM pedido WHERE uuid = :uuid"), {"uuid": uuid}).fetchone()
        if not pedido:
            return JSONResponse(status_code=404, content={"error": "Pedido não encontrado"})
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

    with engine.connect() as conn:
        total_registros = conn.execute(text("""
            SELECT COUNT(DISTINCT p.uuid)
            FROM pedido p
            LEFT JOIN item_pedido i ON i.pedido_uuid = p.uuid
            WHERE (:codigo_cliente IS NULL OR p.cliente_id = :codigo_cliente)
              AND (:id_produto IS NULL OR i.product_id = :id_produto)
              AND (:status IS NULL OR p.status = :status)
        """),{
            "codigo_cliente": codigoCliente,
            "id_produto": idProduto,
            "status": validated_status
        }).scalar() or 0

        pedidos = conn.execute(text(f"""
            SELECT DISTINCT p.*
            FROM pedido p
            LEFT JOIN item_pedido i ON i.pedido_uuid = p.uuid
            WHERE (:codigo_cliente IS NULL OR p.cliente_id = :codigo_cliente)
              AND (:id_produto IS NULL OR i.product_id = :id_produto)
              AND (:status IS NULL OR p.status = :status)
            ORDER BY {order_column} {order_direction}
            LIMIT :limit OFFSET :offset
        """), {
            "codigo_cliente": codigoCliente,
            "Id_produto": idProduto,
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