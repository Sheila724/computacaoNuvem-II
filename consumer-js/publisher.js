// ================================================
// PUBLISHER COM MENU - Pedidos DIFERENTES
// ================================================

require('dotenv').config();
const { PubSub } = require('@google-cloud/pubsub');
const readline = require('readline');

const pubsub = new PubSub({ projectId: process.env.PROJECT_ID });
const topicName = 'pedidos-topic';

const topic = pubsub.topic(topicName);

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const clientes = [
  { id: 7788, name: "Maria Oliveira", email: "maria@email.com" },
  { id: 4455, name: "João Silva", email: "joao@email.com" },
  { id: 1122, name: "Ana Costa", email: "ana@email.com" },
  { id: 3344, name: "Pedro Santos", email: "pedro@email.com" }
];

const produtos = [
  { id: 9001, name: "Smartphone X", price: 2500 },
  { id: 9002, name: "Fone Bluetooth", price: 350 },
  { id: 9003, name: "Notebook Pro", price: 4500 },
  { id: 9004, name: "Mouse Gamer", price: 180 }
];

function perguntar(texto) {
  return new Promise(resolve => rl.question(texto, resolve));
}

async function publishOrder() {
  const cliente = clientes[Math.floor(Math.random() * clientes.length)];
  const numItens = Math.floor(Math.random() * 3) + 1; // 1 a 3 itens

  let items = [];
  let totalPedido = 0;

  for (let i = 0; i < numItens; i++) {
    const prod = produtos[Math.floor(Math.random() * produtos.length)];
    const qty = Math.floor(Math.random() * 3) + 1;
    const itemTotal = prod.price * qty;
    totalPedido += itemTotal;

    items.push({
      "id": i + 1,
      "product_id": prod.id,
      "product_name": prod.name,
      "unit_price": prod.price,
      "quantity": qty,
      "category": {
        "id": "ELEC",
        "name": "Eletrônicos",
        "sub_category": { "id": "GERAL", "name": "Geral" }
      }
    });
  }

  const statuses = ["created", "paid", "separated", "shipped"];
  const status = statuses[Math.floor(Math.random() * statuses.length)];

  const order = {
    "uuid": `ORD-TESTE-${Date.now()}`,
    "created_at": new Date().toISOString(),
    "channel": Math.random() > 0.5 ? "mobile_app" : "web",
    "status": status,
    "customer": cliente,
    "seller": {
      "id": 55,
      "name": "Tech Store",
      "city": "São Paulo",
      "state": "SP"
    },
    "items": items,
    "shipment": {
      "carrier": "Correios",
      "service": "SEDEX",
      "status": "shipped",
      "tracking_code": `BR${Math.floor(100000000 + Math.random() * 900000000)}`
    },
    "payment": {
      "method": Math.random() > 0.5 ? "pix" : "credit_card",
      "status": "approved",
      "transaction_id": `pay_${Date.now()}`
    },
    "metadata": {
      "source": "publisher_teste",
      "ip_address": "192.168.1.100"
    }
  };

  try {
    const dataBuffer = Buffer.from(JSON.stringify(order));
    const messageId = await topic.publish(dataBuffer);

    console.log(`Pedido enviado! UUID: ${order.uuid}`);
    console.log(`   Cliente: ${cliente.name} | Status: ${status} | Itens: ${numItens} | Total: R$ ${totalPedido}`);
    console.log('   ────────────────────────────────');

  } catch (error) {
    console.error('Erro:', error.message);
  }
}

async function menu() {
  console.log("\nPUBLISHER - Gerador de Pedidos Variados\n");

  while (true) {
    console.log("1 → Enviar 1 pedido aleatório");
    console.log("2 → Enviar 3 pedidos aleatórios");
    console.log("3 → Enviar 5 pedidos aleatórios");
    console.log("4 → Enviar 10 pedidos aleatórios");
    console.log("0 → Sair");

    const opcao = await perguntar("Escolha uma opção: ");

    if (opcao === "0") {
      console.log("Encerrando...");
      rl.close();
      break;
    }

    let quantidade = 1;
    if (opcao === "2") quantidade = 3;
    if (opcao === "3") quantidade = 5;
    if (opcao === "4") quantidade = 10;

    console.log(`\nEnviando ${quantidade} pedidos variados...\n`);

    for (let i = 1; i <= quantidade; i++) {
      await publishOrder();
      await new Promise(r => setTimeout(r, 600)); // pequena pausa
    }

    console.log(`\n${quantidade} pedidos enviados com sucesso!\n`);
  }
}

menu();