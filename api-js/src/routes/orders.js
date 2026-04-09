const { Router } = require('express');
const { Op } = require('sequelize');
const { Pedido, Cliente, ItemPedido } = require('../models');

const router = Router();

const VALID_STATUS = new Set(['created', 'paid', 'separated', 'shipped', 'delivered', 'canceled']);
const VALID_SORT_FIELDS = new Set(['created_at', 'total', 'status']);

function formatDatetime(dt) {
  if (!dt) return null;
  let str = dt instanceof Date ? dt.toISOString() : String(dt);
  str = str.split('.')[0];
  str = str.replace('+00:00', 'Z').replace('-03:00', 'Z');
  if (!str.endsWith('Z')) str += 'Z';
  return str;
}

function buildOrderPayload(pedido) {
  const items = (pedido.items || []).map((item, idx) => {
    const total = parseFloat(item.unit_price) * parseInt(item.quantity);
    return {
      id: idx + 1,
      product_id: item.product_id,
      product_name: item.product_name,
      unit_price: parseFloat(item.unit_price),
      quantity: item.quantity,
      category: {
        id: item.categoria_id || 'ELEC',
        name: item.categoria_nome || 'Eletronicos',
        sub_category: {
          id: item.subcategoria_id || 'GERAL',
          name: item.subcategoria_nome || 'Geral',
        },
      },
      total: Math.round(total * 100) / 100,
    };
  });

  const totalPedido = items.reduce((sum, item) => sum + item.total, 0);

  const cliente = pedido.cliente;
  const metadata = typeof pedido.metadata === 'string'
    ? JSON.parse(pedido.metadata)
    : (pedido.metadata || {});

  return {
    uuid: pedido.uuid,
    created_at: formatDatetime(pedido.created_at),
    channel: pedido.channel,
    total: Math.round(totalPedido * 100) / 100,
    status: pedido.status,
    customer: {
      id: cliente ? cliente.id : pedido.cliente_id,
      name: cliente ? cliente.nome : null,
      email: cliente ? cliente.email : null,
      document: cliente ? cliente.documento : '987.654.321-00',
    },
    seller: {
      id: pedido.seller_id,
      name: pedido.seller_nome,
      city: pedido.seller_cidade,
      state: pedido.seller_estado,
    },
    items,
    shipment: {
      carrier: pedido.shipment_carrier,
      service: pedido.shipment_service,
      status: pedido.shipment_status,
      tracking_code: pedido.shipment_tracking,
    },
    payment: {
      method: pedido.payment_method,
      status: pedido.payment_status,
      transaction_id: pedido.payment_transaction_id,
    },
    metadata,
  };
}

// GET /orders/:uuid
router.get('/:uuid', async (req, res, next) => {
  try {
    const pedido = await Pedido.findByPk(req.params.uuid, {
      include: [
        { model: Cliente, as: 'cliente' },
        { model: ItemPedido, as: 'items', order: [['id', 'ASC']] },
      ],
    });

    if (!pedido) {
      return res.status(404).json({ error: 'Pedido nao encontrado' });
    }

    res.json(buildOrderPayload(pedido));
  } catch (err) {
    next(err);
  }
});

// GET /orders
router.get('/', async (req, res, next) => {
  try {
    const {
      codigoCliente,
      product_id,
      status,
      page = 1,
      pageSize = 10,
      sortBy = 'created_at',
      sortOrder = 'desc',
    } = req.query;

    const pageNum = Math.max(1, parseInt(page));
    const pageSizeNum = Math.min(100, Math.max(1, parseInt(pageSize)));

    // Validar status
    if (status && !VALID_STATUS.has(status.toLowerCase())) {
      return res.status(400).json({
        error: `Status invalido: ${status}. Valores permitidos: ${[...VALID_STATUS].sort().join(', ')}`,
      });
    }

    // Validar sortBy
    if (!VALID_SORT_FIELDS.has(sortBy)) {
      return res.status(400).json({ error: `sortBy invalido: ${sortBy}` });
    }

    const normalizedOrder = (sortOrder || 'desc').toLowerCase();
    if (!['asc', 'desc'].includes(normalizedOrder)) {
      return res.status(400).json({ error: `sortOrder invalido: ${sortOrder}` });
    }

    // Construir where clause
    const where = {};
    if (codigoCliente) where.cliente_id = parseInt(codigoCliente);
    if (status) where.status = status.toLowerCase();

    // Se filtrar por product_id, precisamos de subquery
    let pedidoUuids = null;
    if (product_id) {
      const items = await ItemPedido.findAll({
        attributes: ['pedido_uuid'],
        where: { product_id: parseInt(product_id) },
        raw: true,
      });
      pedidoUuids = items.map(i => i.pedido_uuid);
      where.uuid = { [Op.in]: pedidoUuids };
    }

    const offset = (pageNum - 1) * pageSizeNum;

    const { count: totalRecords, rows: pedidos } = await Pedido.findAndCountAll({
      where,
      include: [
        { model: Cliente, as: 'cliente' },
        { model: ItemPedido, as: 'items' },
      ],
      order: [[sortBy, normalizedOrder]],
      limit: pageSizeNum,
      offset,
      distinct: true,
    });

    const totalPages = totalRecords > 0 ? Math.ceil(totalRecords / pageSizeNum) : 0;

    res.json({
      orders: pedidos.map(buildOrderPayload),
      pagination: {
        page: pageNum,
        pageSize: pageSizeNum,
        totalRecords,
        totalPages,
        sortBy,
        sortOrder: normalizedOrder,
      },
    });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
