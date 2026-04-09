const { PubSub } = require('@google-cloud/pubsub');

const pubsub = new PubSub({
  projectId: process.env.PUBSUB_PROJECT_ID,
});

module.exports = pubsub;
