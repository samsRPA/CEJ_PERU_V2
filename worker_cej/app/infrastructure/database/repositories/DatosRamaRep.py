import logging


class DatosRamaRep():

    
    
    def __init__(self, table):
        self.table = table
        self.logger = logging.getLogger(__name__)


    async def insertProcessDataRama( self, conn, radicado: str, dato_nombre: str, dato_valor: str,usuario: str, origen: str) -> None:
           
        try:
            query = f"""
                    INSERT INTO {self.table} (
                        RADICADO,
                        DATO_NOMBRE,
                        DATO_VALOR,
                        USUARIO,
                        ORIGEN,
                        FECHA
                    ) VALUES (
                        :radicado,
                        :dato_nombre,
                        :dato_valor,
                        :usuario,
                        :origen,
                        SYSDATE
                    )
                """

            async with conn.cursor() as cursor:
                await cursor.execute(
                    query,
                    {
                        "radicado": radicado,
                        "dato_nombre": dato_nombre,
                        "dato_valor": dato_valor,
                        "usuario": usuario,
                        "origen": origen,
                    }
                    )

                

            self.logger.info(
                f"✅ Insertado en DATOS_PROCESOS_RAMA | "
                f"Radicado={radicado}, Dato={dato_nombre}"
            )

        except Exception as error:
            self.logger.error(
                f"❌ Error insertando en DATOS_PROCESOS_RAMA "
                f"(Radicado={radicado}, Dato={dato_nombre}): {error}"
                )
            raise

    async def processDataRamaExists(self,conn,radicado: str,dato_nombre: str,dato_valor: str,origen: str ) -> bool:
    
        try:
            query = f"""
                SELECT 1
                FROM {self.table}
                WHERE RADICADO = :radicado
                AND DATO_NOMBRE = :dato_nombre
                AND DATO_VALOR = :dato_valor
                AND ORIGEN = :origen
                FETCH FIRST 1 ROWS ONLY
            """

            async with conn.cursor() as cursor:
                await cursor.execute(
                    query,
                    {
                        "radicado": radicado,
                        "dato_nombre": dato_nombre,
                        "dato_valor": dato_valor,
                        "origen": origen,
                    }
                )
                row = await cursor.fetchone()

            if row:
                return True

            self.logger.info(
                f"🆕 No existe dato en DATOS_PROCESOS_RAMA | "
                f"Radicado={radicado}, Dato={dato_nombre}, Origen={origen}"
            )
            return False

        except Exception as error:
            self.logger.error(
                f"❌ Error validando existencia en DATOS_PROCESOS_RAMA "
                f"(Radicado={radicado}, Dato={dato_nombre}, Origen={origen}): {error}"
            )
            raise
