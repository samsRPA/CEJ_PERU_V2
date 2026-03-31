import asyncio
import logging

class ControlAutosRep:

    
    
    def __init__(self, table):
        self.table = table
        self.logger = logging.getLogger(__name__)


    async def isRadicacionProcessed(self, conn, radicacion: str) -> bool:
            """
            Verifica si ya existe un radicado en CONTROL_AUTOS_RAMA_1.
            Retorna True si hay filas (✅ procesado), False en caso contrario.
            """
            try:
                query = F"""
                    SELECT 1
                    FROM {self.table}
                    WHERE RADICACION = :radicacion
                    FETCH FIRST 1 ROWS ONLY
                """

                async def _execute():
                    async with conn.cursor() as cursor:
                        await cursor.execute(query, {"radicacion": radicacion})
                        rows= await cursor.fetchone()
                        return rows

                result = await _execute()

                if not result:
                    self.logger.info(f"🔎 radicado {radicacion} no se procesado, se recorrera completamente.")
                    return False

                return True

            except Exception as error:
                self.logger.error(f"❌ Error en radicacion_procesada: {error}")
                raise



    async def autoExists(self, conn, data: dict) -> bool:
        """
        Verifica existencia por RADICACION + FECHA_NOTIFICACION + CONSECUTIVO + ORIGEN.
        El consecutivo debe venir ya calculado desde el servicio.
        """
        sql = f"""
            SELECT 1
            FROM {self.table}
            WHERE FECHA_NOTIFICACION = :fecha_notificacion
            AND   RADICACION         = :radicacion
            AND   CONSECUTIVO        = :consecutivo
            AND   ORIGEN             = :origen
            FETCH FIRST 1 ROWS ONLY
        """
        binds = {
            "fecha_notificacion": data["FECHA_NOTIFICACION"],   # str 'DD-MM-YYYY'
            "radicacion":         data["RADICACION"],
            "consecutivo":        data["CONSECUTIVO"],
            "origen":             data["ORIGEN"],
        }
        try:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, binds)
                row = await cursor.fetchone()
            exists = row is not None
            if not exists:
                self.logger.info(
                    f"📄 No existe registro → RADICACION={binds['radicacion']} "
                    f"FECHA={binds['fecha_notificacion']} CONSECUTIVO={binds['consecutivo']}"
                )
            return exists
        except Exception as err:
            self.logger.error(
                f"🚨 Error verificando existencia RADICACION={binds['radicacion']}: {err}",
                exc_info=True,
            )
            raise



    async def insertAuto(
        self, conn, fecha_notificacion: str, radicacion: str, consecutivo: int,
        ruta_s3: str,  origen: str, tipo_documento: str, fecha_registro_tyba:str
    ) -> bool:
        """
        Inserta un documento en CONTROL_AUTOS_RAMA_1 con las columnas básicas.
        """
        try:
            query = f"""
                INSERT INTO {self.table} (
                    FECHA_NOTIFICACION,
                    RADICACION,
                    CONSECUTIVO,
                    RUTA_S3,
                    ORIGEN,
                    TIPO_DOCUMENTO,
                    FECHA_AUTO,
                    ESTADO_DESCARGA
                    
                ) VALUES (
                    TO_DATE(:fecha_notificacion, 'DD-MM-YYYY'),
                    :radicacion,
                    :consecutivo,
                    :ruta_s3,
                    :origen,
                    :tipo_documento,
                    TO_DATE(:fecha_auto, 'DD/MM/YYYY HH24:MI:SS'),
                    'SI'
                    
                )
            
                
            """

            async with conn.cursor() as cursor:
                await cursor.execute(query, {
                        "fecha_notificacion": fecha_notificacion,
                        "radicacion": radicacion,
                        "consecutivo": consecutivo,
                        "ruta_s3": ruta_s3,
                        "origen": origen,
                        "tipo_documento": tipo_documento,
                        "fecha_auto":fecha_registro_tyba
                })

            
            return True

        except Exception as error:
        
            self.logger.error(f"❌ Error en insertar_documento_simple: {error}")
            return False

    async def getMaxConsecutive(self, conn, data: dict) -> int:
            sql = f"""
                SELECT NVL(MAX(CONSECUTIVO), 0) AS MAX_CONSECUTIVO
                FROM {self.table}
                WHERE RADICACION = :RADICACION
                AND FECHA_NOTIFICACION = TO_DATE(:FECHA_NOTIFICACION, 'DD/MM/YYYY')
            """

            binds = {
                "RADICACION": data.get("RADICACION"),
                "FECHA_NOTIFICACION": data.get("FECHA_NOTIFICACION"),
            }

     
            try:
                max_consecutivo=None
    
                async with conn.cursor() as cursor:
                    await cursor.execute(sql, binds)
                    row = await cursor.fetchone()
                    max_consecutivo=row[0] if row else None
                        
                
                if not isinstance(max_consecutivo, (int, float)):
                    raise ValueError(f"El resultado del max_consecutivo no es numérico: {max_consecutivo}")
                    
    

                # 🔹 Log de resultado
                self.logger.info(
                    f"📄 Máximo consecutivo obtenido para RADICACION={binds['RADICACION']}: {max_consecutivo}"
                )

                return max_consecutivo

            except Exception as err:
                self.logger.error(
                    f"🚨 Error al obtener máximo consecutivo para RADICACION={binds['RADICACION']}: {err}",
                    exc_info=True
                )
                raise err



