const sequelize = require('../config/database');
const Cliente = require('./Cliente');
const Produto = require('./Produto');
const Pedido = require('./Pedido');
const ItemPedido = require('./ItemPedido');

// Associacoes
Pedido.belongsTo(Cliente, { foreignKey: 'cliente_id', as: 'cliente' });
Cliente.hasMany(Pedido, { foreignKey: 'cliente_id' });

Pedido.hasMany(ItemPedido, { foreignKey: 'pedido_uuid', sourceKey: 'uuid', as: 'items' });
ItemPedido.belongsTo(Pedido, { foreignKey: 'pedido_uuid', targetKey: 'uuid' });

ItemPedido.belongsTo(Produto, { foreignKey: 'product_id', as: 'produto' });
Produto.hasMany(ItemPedido, { foreignKey: 'product_id' });

module.exports = { sequelize, Cliente, Produto, Pedido, ItemPedido };
