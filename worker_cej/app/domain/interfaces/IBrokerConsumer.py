from abc import ABC, abstractmethod
from typing import Callable, Awaitable, Any

class IBrokerConsumer(ABC):

    @abstractmethod
    def onMessage(self, handler: Callable[[bytes], Awaitable[Any]]):
        """Configura la función que procesará cada mensaje recibido."""
        ...

    @abstractmethod
    async def connect(self):
        """Establece la conexión con el broker."""
        ...

    @abstractmethod
    async def startConsuming(self):
        """Inicia el consumo de mensajes de la cola."""
        ...