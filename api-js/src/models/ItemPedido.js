const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const ItemPedido = sequelize.define('ItemPedido', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true,
  },
  pedido_uuid: {
    type: DataTypes.STRING(50),
  },
  product_id: {
    type: DataTypes.INTEGER,
  },
  product_name: {
    type: DataTypes.STRING(255),
  },
  unit_price: {
    type: DataTypes.DECIMAL(12, 2),
  },
  quantity: {
    type: DataTypes.INTEGER,
  },
  categoria_id: {
    type: DataTypes.STRING(20),
  },
  categoria_nome: {
    type: DataTypes.STRING(100),
  },
  subcategoria_id: {
    type: DataTypes.STRING(20),
  },
  subcategoria_nome: {
    type: DataTypes.STRING(100),
  },
}, {
  tableName: 'item_pedido',
  timestamps: false,
});

module.exports = ItemPedido;
