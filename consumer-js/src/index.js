require('dotenv').config();

const { sequelize } = require('./models');
const pubsub = require('./config/pubsub');
const { handleOrderMessage } = require('./handlers/orderHandler');

const SUBSCRIPTION_NAME = process.env.PUBSUB_SUBSCRIPTION || 'sub-grupo1';

async function start() {
  try {
    await sequelize.authenticate();
    console.log('Conectado ao PostgreSQL com sucesso.');

    const subscription = pubsub.subscription(SUBSCRIPTION_NAME);

    subscription.on('message', handleOrderMessage);

    subscription.on('error', (err) => {
      console.error('Erro na subscription:', err.message);
    });

    console.log(`Escutando mensagens na subscription: ${SUBSCRIPTION_NAME}`);
    console.log('Pressione Ctrl+C para encerrar.');
  } catch (err) {
    console.error('Erro ao iniciar consumer:', err.message);
    process.exit(1);
  }
}

start();
