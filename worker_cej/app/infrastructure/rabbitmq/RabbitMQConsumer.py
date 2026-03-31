import logging
import asyncio
from typing import Callable, Awaitable

import aio_pika
from aio_pika.exceptions import (
    AMQPConnectionError,
    ChannelClosed,
    MessageProcessError
)
from app.domain.interfaces.IBrokerConsumer import IBrokerConsumer

class RabbitMQConsumer(IBrokerConsumer):
    def __init__(self, host: str, port: int, queueName: str, prefetchCount: int, timeout:int = 10):
        self.host = host
        self.port = port
        self.queue = None
        self.channel = None
        self.timeout = timeout
        self.connection = None
        self.userCallback = None
        self.queueName = queueName
        self.prefetchCount = prefetchCount
        self.logger = logging.getLogger(__name__)
    
    def onMessage(self, callback: Callable[[bytes], Awaitable[None]]):
        self.userCallback = callback
    
    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(
                host = self.host,
                port = self.port,
                timeout = self.timeout
            )
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=self.prefetchCount)
            self.queue = await self.channel.declare_queue(
                self.queueName,
                durable=True
            )
            self.logger.info("🔵 Conectado a RabbitMQ - Consumer")

        except (AMQPConnectionError, ChannelClosed) as e:
            self.logger.error(f"🔴 Error crítico conectando al broker: {e}")
            raise

        except Exception as e:
            self.logger.error(f"🔴 Error inesperado conectando al consumer: {e}")
            raise
    
    async def _callback(self, message: aio_pika.IncomingMessage):
        async with message.process(ignore_processed=True):
            try:
                body = message.body

                if self.userCallback:
                    await self.userCallback(body)

            except MessageProcessError:
                self.logger.warning("🟡 Intento de NACK/ACK inválido.")
            
            except Exception as e:
                self.logger.error(f"🔴 Error procesando mensaje: {e}")
                try:
                    await message.nack(requeue=False)
                except MessageProcessError:
                    self.logger.warning("🟡 Mensaje ya estaba procesado.")
    
    async def startConsuming(self):

        if not self.userCallback:
            raise RuntimeError(
                "🔴 No se ha registrado un callback. Debe llamar a consumer.onMessage(func) antes de startConsuming()."
            )

        if not self.channel or not self.queue:
            await self.connect()

        try:
            await self.queue.consume(self._callback)
            self.logger.info("🎧 Esperando mensajes...")

            while True:
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            self.logger.info("👋 Consumo cancelado por el usuario.")

        except AMQPConnectionError as e:
            self.logger.error(f"🔴 Conexión con RabbitMQ perdida: {e}")

        except ChannelClosed as e:
            self.logger.error(f"🔴 El canal fue cerrado inesperadamente: {e}")

        except Exception as e:
            self.logger.error(f"🔴 Error inesperado en el consumo: {e}")
            raise

        finally:
            if self.channel:
                await self.channel.close()
                self.logger.info("🔌 Canal RabbitMQ cerrado.")

            if self.connection:
                await self.connection.close()
                self.logger.info("🔌 Conexión RabbitMQ cerrada.")