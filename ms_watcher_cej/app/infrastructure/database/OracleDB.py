import logging
import oracledb

from app.domain.interfaces.IDatabase import IDatabase

class OracleDB(IDatabase):
    def __init__(self, user: str, password: str, host: str, port: int, dbName: str):
        self._user = user
        self._password = password
        self._host = host
        self._port = port
        self._service_name = dbName
        self._pool = None

    @property
    def isConnected(self) -> bool:
        return self._pool is not None

    async def connect(self) -> None:
        try:
            dsn = f"{self._host}:{self._port}/{self._service_name}"
            self._pool = oracledb.create_pool_async(
                user=self._user,
                password=self._password,
                dsn=dsn,
                min=1,
                max=3,
                increment=1,
                getmode=oracledb.POOL_GETMODE_WAIT,
                homogeneous=True,
            )
            logging.info("🔵 Pool de Oracle creado exitosamente.")
        except Exception as e:
            logging.error(f"🔴 Error al crear el pool de Oracle: {e}")
            raise e

    async def acquireConnection(self):
        if not self._pool:
            raise Exception("Pool no inicializado, llama a connect primero")
        conn = await self._pool.acquire()
        return conn

    async def releaseConnection(self, conn):
        try:
            await conn.rollback()
        except Exception:
            pass
        finally:
            await self._pool.release(conn)

    async def commit(self, conn):
        try:
            await conn.commit()
        except Exception as e:
            raise e

    async def closeConnection(self):
        if self._pool:
            await self._pool.close()
            self._pool = None
            logging.info("🔌 Conexión a Oracle cerrada correctamente.")
