const { Sequelize } = require('sequelize');

const sequelize = new Sequelize(
  process.env.DB_NAME,
  process.env.DB_USER,
  process.env.DB_PASSWORD,
  {
    host: process.env.DB_HOST || 'localhost',
    port: process.env.DB_PORT || 5432,
    dialect: 'postgres',
    logging: false,
    pool: {
      max: 20,        // Máximo de conexões
      min: 5,         // Mínimo de conexões
      acquire: 60000, // Timeout para adquirir conexão (60s)
      idle: 10000,    // Timeout inativo (10s)
    },
    dialectOptions: {
      connectTimeout: 60000, // Timeout de conexão (60s)
    },
  }
);

module.exports = sequelize;
