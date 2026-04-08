const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const Cliente = sequelize.define('Cliente', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
  },
  nome: {
    type: DataTypes.STRING(255),
    allowNull: false,
  },
  email: {
    type: DataTypes.STRING(255),
  },
  documento: {
    type: DataTypes.STRING(20),
    allowNull: false,
    defaultValue: '987.654.321-00',
  },
}, {
  tableName: 'cliente',
  timestamps: false,
});

module.exports = Cliente;
