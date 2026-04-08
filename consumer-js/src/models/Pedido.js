const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const Pedido = sequelize.define('Pedido', {
  uuid: {
    type: DataTypes.STRING(50),
    primaryKey: true,
  },
  created_at: {
    type: DataTypes.DATE,
  },
  channel: {
    type: DataTypes.STRING(50),
  },
  status: {
    type: DataTypes.STRING(20),
  },
  cliente_id: {
    type: DataTypes.INTEGER,
  },
  seller_id: {
    type: DataTypes.INTEGER,
  },
  seller_nome: {
    type: DataTypes.STRING(255),
  },
  seller_cidade: {
    type: DataTypes.STRING(100),
  },
  seller_estado: {
    type: DataTypes.STRING(5),
  },
  shipment_carrier: {
    type: DataTypes.STRING(100),
  },
  shipment_service: {
    type: DataTypes.STRING(50),
  },
  shipment_status: {
    type: DataTypes.STRING(50),
  },
  shipment_tracking: {
    type: DataTypes.STRING(100),
  },
  payment_method: {
    type: DataTypes.STRING(50),
  },
  payment_status: {
    type: DataTypes.STRING(50),
  },
  payment_transaction_id: {
    type: DataTypes.STRING(100),
  },
  metadata: {
    type: DataTypes.JSONB,
  },
  indexed_at: {
    type: DataTypes.DATE,
    defaultValue: DataTypes.NOW,
  },
}, {
  tableName: 'pedido',
  timestamps: false,
});

module.exports = Pedido;
