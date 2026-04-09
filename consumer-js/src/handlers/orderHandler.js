const { sequelize, Cliente, Produto, Pedido, ItemPedido } = require('../models');

async function handleOrderMessage(message) {
  const messageId = message.id;
  let data;

  try {
    data = JSON.parse(message.data.toString());
  } catch (err) {
    console.error(`[${messageId}] Erro ao parsear JSON:`, err.message);
    message.ack();
    return;
  }

  const t = await sequelize.transaction();

  try {
    // 1. Upsert cliente
    if (data.customer) {
      await Cliente.upsert({
        id: data.customer.id,
        nome: data.customer.name,
        email: data.customer.email,
        documento: data.customer.document || '987.654.321-00',
      }, { transaction: t });
    }

    // 2. Upsert produtos (de cada item)
    if (data.items && Array.isArray(data.items)) {
      for (const item of data.items) {
        await Produto.upsert({
          id: item.product_id,
          nome: item.product_name,
          categoria_id: item.category?.id || null,
          categoria_nome: item.category?.name || null,
          subcategoria_id: item.category?.sub_category?.id || null,
          subcategoria_nome: item.category?.sub_category?.name || null,
        }, { transaction: t });
      }
    }

    // 3. Upsert pedido (trata duplicatas por UUID)
    await Pedido.upsert({
      uuid: data.uuid,
      created_at: data.created_at,
      channel: data.channel,
      status: data.status,
      cliente_id: data.customer?.id,
      seller_id: data.seller?.id,
      seller_nome: data.seller?.name,
      seller_cidade: data.seller?.city,
      seller_estado: data.seller?.state,
      shipment_carrier: data.shipment?.carrier,
      shipment_service: data.shipment?.service,
      shipment_status: data.shipment?.status,
      shipment_tracking: data.shipment?.tracking_code,
      payment_method: data.payment?.method,
      payment_status: data.payment?.status,
      payment_transaction_id: data.payment?.transaction_id,
      metadata: data.metadata || {},
      indexed_at: new Date(),
    }, { transaction: t });

    // 4. Deletar items antigos (caso de reprocessamento) e inserir novos
    await ItemPedido.destroy({
      where: { pedido_uuid: data.uuid },
      transaction: t,
    });

    if (data.items && Array.isArray(data.items)) {
      for (const item of data.items) {
        await ItemPedido.create({
          pedido_uuid: data.uuid,
          product_id: item.product_id,
          product_name: item.product_name,
          unit_price: item.unit_price,
          quantity: item.quantity,
          categoria_id: item.category?.id || null,
          categoria_nome: item.category?.name || null,
          subcategoria_id: item.category?.sub_category?.id || null,
          subcategoria_nome: item.category?.sub_category?.name || null,
        }, { transaction: t });
      }
    }

    await t.commit();
    message.ack();
    console.log(`[${messageId}] Pedido ${data.uuid} persistido com sucesso.`);
  } catch (err) {
    await t.rollback();
    console.error(`[${messageId}] Erro ao persistir pedido:`, err.message);
    message.nack();
  }
}

module.exports = { handleOrderMessage };
