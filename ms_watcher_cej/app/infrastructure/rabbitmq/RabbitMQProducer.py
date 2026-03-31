import json
import logging

import aio_pika

from app.domain.interfaces.IBrokerProducer import IBrokerProducer

class RabbitMQProducer(IBrokerProducer):
    def __init__(self, host:str, port, queueName:str):
        self.host = host
        self.port = port
        self.queueName = queueName
        self.connection = None
        self.channel = None

    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(
                host=self.host,
                port=self.port,
                timeout=5 
            )
            self.channel = await self.connection.channel()
            await self.channel.declare_queue(self.queueName, durable=True)
            logging.info("🔵 Conectado a RabbitMQ - Producer")
        except Exception as e:
            logging.error(f"🔴 Error conectando al Producer: {e}")
            raise

    async def publishMessage(self, message: dict):
        try:
            body = json.dumps(message).encode()
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body = body,
                    delivery_mode = aio_pika.DeliveryMode.NOT_PERSISTENT
                ),
                routing_key=self.queueName,
            )
            logging.info(f"📤 Mensaje enviado a {self.queueName} - {message}")
        except Exception as e:
            logging.exception("❌ Error enviando mensaje")
            raise

    async def close(self):
        if self.connection:
            await self.connection.close()
            logging.info("🔌 Conexión con RabbitMQ cerrada")
