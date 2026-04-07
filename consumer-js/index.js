require('dotenv').config();
const { PubSub } = require('@google-cloud/pubsub');
const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

const pubsub = new PubSub({ projectId: process.env.PROJECT_ID });
const subscription = pubsub.subscription(process.env.SUBSCRIPTION_NAME);

console.log('Consumer JS iniciado - aguardando mensagens do Pub/Sub...');

subscription.on('message', async (message) => {
  try {
    const data = JSON.parse(message.data.toString());
    const uuid = data.uuid || 'SEM-UUID';
    console.log(`Mensagem recebida: ${uuid}`);

    // Cálculo dos totais
    let total_pedido = 0;
    data.items.forEach(item => {
      item.total = Number((item.unit_price * item.quantity).toFixed(2));
      total_pedido += item.total;
    });
    data.total = Number(total_pedido.toFixed(2));

    const client = await pool.connect();

    try {
      // ==================== CLIENTE ====================
      await client.query(`
        INSERT INTO cliente (id, nome, email, documento)
        VALUES ($1, $2, $3, COALESCE(NULLIF($4, ''), '987.654.321-00'))
        ON CONFLICT (id) DO UPDATE SET
          nome = EXCLUDED.nome,
          email = EXCLUDED.email,
          documento = COALESCE(NULLIF(EXCLUDED.documento, ''), cliente.documento, '987.654.321-00')
      `, [data.customer.id, data.customer.name, data.customer.email, data.customer.document]);

      // ==================== PRODUTO ====================
      for (const item of data.items) {
        await client.query(`
          INSERT INTO produto (id, nome, categoria)
          VALUES ($1, $2, $3)
          ON CONFLICT (id) DO NOTHING
        `, [item.product_id, item.product_name, item.category?.name || null]);
      }

      // ==================== PEDIDO ====================
      await client.query(`
        INSERT INTO pedido (
          uuid, created_at, indexed_at, channel, total, status,
          cliente_id, seller_id, seller_nome, seller_cidade, seller_estado,
          shipment_carrier, shipment_service, shipment_status, shipment_tracking,
          payment_method, payment_status, payment_transaction_id, metadata
        )
        VALUES ($1, $2, NOW(), $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
        ON CONFLICT (uuid) DO NOTHING
      `, [
        uuid,
        data.created_at,
        data.channel,
        data.total,
        data.status,
        data.customer.id,
        data.seller.id,
        data.seller.name,
        data.seller.city,
        data.seller.state,
        data.shipment?.carrier || null,
        data.shipment?.service || null,
        data.shipment?.status || null,
        data.shipment?.tracking_code || null,
        data.payment?.method || null,
        data.payment?.status || null,
        data.payment?.transaction_id || null,
        JSON.stringify(data.metadata || {})
      ]);

      // ==================== ITENS DO PEDIDO ====================
      for (const item of data.items) {
        await client.query(`
          INSERT INTO item_pedido (
            pedido_uuid, product_id, product_name, unit_price, quantity,
            total_item, categoria_id, categoria_nome,
            subcategoria_id, subcategoria_nome
          )
          VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
          ON CONFLICT (pedido_uuid, product_id) DO NOTHING
        `, [
          uuid,
          item.product_id,
          item.product_name,
          item.unit_price,
          item.quantity,
          item.total,
          item.category?.id || null,
          item.category?.name || null,
          item.category?.sub_category?.id || null,
          item.category?.sub_category?.name || null
        ]);
      }

      console.log(`Pedido ${uuid} salvo com sucesso!`);
      message.ack();

    } finally {
      client.release();
    }

  } catch (err) {
    console.error('Erro ao processar mensagem:', err.message);
    message.nack();   // tenta novamente mais tarde
  }
});

subscription.on('error', err => {
  console.error('Erro na subscription:', err);
});