const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const Produto = sequelize.define('Produto', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
  },
  nome: {
    type: DataTypes.STRING(255),
    allowNull: false,
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
  tableName: 'produto',
  timestamps: false,
});

module.exports = Produto;
