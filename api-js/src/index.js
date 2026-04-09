require('dotenv').config();

const express = require('express');
const cors = require('cors');
const { sequelize } = require('./models');
const ordersRouter = require('./routes/orders');
const errorHandler = require('./middlewares/errorHandler');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

app.use('/orders', ordersRouter);

app.use(errorHandler);

async function start() {
  try {
    await sequelize.authenticate();
    console.log('Conectado ao PostgreSQL com sucesso.');

    app.listen(PORT, () => {
      console.log(`API rodando em http://localhost:${PORT}`);
    });
  } catch (err) {
    console.error('Erro ao iniciar API:', err.message);
    process.exit(1);
  }
}

start();
