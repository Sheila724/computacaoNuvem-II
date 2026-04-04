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

        