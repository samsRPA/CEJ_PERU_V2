
import logging
import oracledb 
import json
import os
class DocumentsRepository():

    
    def __init__(self, table_car):
        self.table_car = table_car
        self.logger = logging.getLogger(__name__)


    async def insert_document(
        self, conn, fecha_notificacion: str, radicacion: str, consecutivo: int,
        ruta_s3: str, url_auto: str, origen: str, tipo_documento: str, fecha_registro_tyba:str
    ) -> bool:
        """
        Inserta un documento en CONTROL_AUTOS_RAMA_1 con las columnas básicas.
        """
        try:
            query = f"""
                INSERT INTO CONTROL_AUTOS_RAMA_1 (
                    FECHA_NOTIFICACION,
                    RADICACION,
                    CONSECUTIVO,
                    RUTA_S3,
                    URL_AUTO,
                    ORIGEN,
                    TIPO_DOCUMENTO,
                    FECHA_AUTO
                    
                ) VALUES (
                    TO_DATE(:fecha_notificacion, 'DD-MM-YYYY'),
                    :radicacion,
                    :consecutivo,
                    :ruta_s3,
                    :url_auto,
                    :origen,
                    :tipo_documento,
                    TO_DATE(:fecha_auto, 'DD/MM/YYYY HH24:MI:SS')
                    
                )
            
                
            """

            async with conn.cursor() as cursor:
                await cursor.execute(query, {
                        "fecha_notificacion": fecha_notificacion,
                        "radicacion": radicacion,
                        "consecutivo": consecutivo,
                        "ruta_s3": ruta_s3,
                        "url_auto": url_auto,
                        "origen": origen,
                        "tipo_documento": tipo_documento,
                        "fecha_auto":fecha_registro_tyba
                })

            

            return True

        except Exception as error:
            await conn.rollback()
            self.logger.error(f"❌ Error en insertar_documento_simple: {error}")
            return False



    async def exists_document(self, conn, data: dict) -> bool:
        """
        Verifica si existe un documento en la tabla CONTROL_AUTOS_RAMA_1 
        según la fecha de notificación, radicación y consecutivo.
        Retorna True si existe, False si no.
        """
        sql = """
            SELECT 1
            FROM CONTROL_AUTOS_RAMA_1
            WHERE FECHA_NOTIFICACION = :fecha_notificacion
            AND RADICACION = :radicacion
            AND CONSECUTIVO = :consecutivo
            FETCH FIRST 1 ROWS ONLY
        """

        binds = {
            "fecha_notificacion": data.get("FECHA_NOTIFICACION"),
            "radicacion": data.get("RADICACION"),
            "consecutivo": data.get("CONSECUTIVO"),
        }

        try:
          

            async with conn.cursor() as cursor:
                await cursor.execute(sql, binds)
                row = await cursor.fetchone()

            exists = row is not None

            # 🔹 Log de resultado
            if exists:
                self.logger.info(f"📄 Documento existente para RADICACION={binds['radicacion']}, fecha ={binds['fecha_notificacion']} consecutivo ={binds['consecutivo']}")
            else:
                f"CONSECUTIVO={binds['consecutivo']}"
                f"CONSECUTIVO={binds['consecutivo']}"
                self.logger.info(f"📄 No se encontró documento para RADICACION={binds['radicacion']} , fecha ={binds['fecha_notificacion']} consecutivo ={binds['consecutivo']}")

            return exists

        except Exception as err:
            self.logger.error(
                f"🚨 Error al verificar existencia de documento RADICACION={binds.get('radicacion')}: {err}",
                exc_info=True
            )
            raise


    async def exists_action(self, conn, data: dict) -> bool:
        """
        Verifica si existe un documento en la tabla CONTROL_AUTOS_RAMA_1 
        según la fecha de notificación, radicación y consecutivo.
        Retorna True si existe, False si no.
        """
        sql = """
            SELECT 1
            FROM actuaciones_rama
            WHERE RADICADO_RAMA = :radicado
            AND COD_DESPACHO_RAMA = :cod_despacho_rama
            AND FECHA_ACTUACION = :fecha_actuacion
            AND ACTUACION_RAMA = :actuacion_rama
            AND ANOTACION_RAMA = :anotacion_rama
            AND ORIGEN_DATOS = :origen
            
            


        """

        binds = {
        "radicado": data.get("radicado"),
        "cod_despacho_rama": data.get("cod_despacho_rama"),
        "fecha_actuacion": data.get("fecha"),
        "actuacion_rama": data.get("actuacion_rama"),
        "anotacion_rama": data.get("anotacion_rama"),
        "origen": data.get("origen_datos"),
    }


        try:
          

            async with conn.cursor() as cursor:
                await cursor.execute(sql, binds)
                row = await cursor.fetchone()

            exists = row is not None

            if exists:
                self.logger.info(
                "📄 Actuación existente | "
                f"RADICADO={binds['radicado']} | "
                f"DESPACHO={binds['cod_despacho_rama']} | "
                f"FECHA={binds['fecha_actuacion']} | "
                f"ACTUACION={binds['actuacion_rama']}"
            )
            else:
                self.logger.info(
                    "📄 Actuación NO encontrada | "
                    f"RADICADO={binds['radicado']} | "
                    f"DESPACHO={binds['cod_despacho_rama']} | "
                    f"FECHA={binds['fecha_actuacion']} | "
                    f"ACTUACION={binds['actuacion_rama']}"
                )
            return exists

        except Exception as err:
            self.logger.error(
                f"🚨 Error al verificar existencia de documento RADICACION={binds.get('radicacion')}: {err}",
                exc_info=True
            )
            raise



   
    async def get_max_consecutive(self, conn, data: dict) -> int:
        sql = f"""
            SELECT NVL(MAX(CONSECUTIVO), 0) AS MAX_CONSECUTIVO
            FROM {self.table_car}
            WHERE RADICACION = :RADICACION
              AND FECHA_NOTIFICACION = TO_DATE(:FECHA_NOTIFICACION, 'DD/MM/YYYY')
        """

        binds = {
            "RADICACION": data.get("RADICACION"),
            "FECHA_NOTIFICACION": data.get("FECHA_NOTIFICACION"),
        }

        # 🔹 Log de inicio
        self.logger.info(
            f"🔍 Obteniendo máximo consecutivo para RADICACION={binds['RADICACION']} "
            f"y FECHA_NOTIFICACION={binds['FECHA_NOTIFICACION']}"
        )

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



    async def insertar_dato_proceso_rama( self, conn, radicado: str, dato_nombre: str, dato_valor: str,usuario: str, origen: str) -> None:
        """
        Inserta un registro en la tabla DATOS_PROCESOS_RAMA.
        """
        try:
            query = """
                INSERT INTO DATOS_PROCESOS_RAMA (
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


    async def dato_proceso_rama_existe(self,conn,radicado: str,dato_nombre: str,dato_valor: str,origen: str ) -> bool:
        """
        Verifica si ya existe un registro en DATOS_PROCESOS_RAMA
        usando RADICADO, DATO_NOMBRE, DATO_VALOR y ORIGEN.
        Retorna True si existe, False si no.
        """
        try:
            query = """
                SELECT 1
                FROM DATOS_PROCESOS_RAMA
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


    async def insertar_actor_rama( self, conn, radicado: str, tipo_sujeto: str, nombre_actor: str) -> None:
        """
        Inserta un registro en la tabla DATOS_PROCESOS_RAMA.
        """
        try:
            query = """
            INSERT INTO ACTORES_RAMA (
                RADICADO_RAMA,
                TIPO_SUJETO,
                NOMBRE_ACTOR,
                FECHA_CREACION_REGISTRO,
                ORIGEN_DATOS
            ) VALUES (
                :radicado,
                :tipo_sujeto,
                :nombre_actor,
                SYSDATE,
                :origen_datos
            )
    """

            async with conn.cursor() as cursor:
                await cursor.execute(
                    query,
                   {
                "radicado": radicado,
                "tipo_sujeto": tipo_sujeto,
                "nombre_actor": nombre_actor,
                "origen_datos": "CEJ_PERU"
            }
                )

            

            self.logger.info(
                f"✅ Insertado en ACTORES RAMA | "
                f"Radicado={radicado}, tipo sujeto ={tipo_sujeto}, nombre_actor = {nombre_actor}"
            )

        except Exception as error:
            self.logger.error(
                f"❌ Error insertando en  ACTORES RAMA | "
                f"Radicado={radicado}, tipo sujeto ={tipo_sujeto}, nombre_actor = {nombre_actor}): {error}"
            )
            raise



    async def actor_rama_existe( self, conn, radicado: str, tipo_sujeto: str, nombre_actor: str)  -> bool:
        """
        Verifica si ya existe un registro en DATOS_PROCESOS_RAMA
        usando RADICADO, DATO_NOMBRE, DATO_VALOR y ORIGEN.
        Retorna True si existe, False si no.
        """
        try:
            query = """
                SELECT 1
                FROM ACTORES_RAMA
                WHERE RADICADO_RAMA = :radicado
                AND TIPO_SUJETO = :tipo_sujeto
                AND NOMBRE_ACTOR = :nombre_actor
                AND ORIGEN_DATOS = :origen
                FETCH FIRST 1 ROWS ONLY
            """

            async with conn.cursor() as cursor:
                await cursor.execute(
                    query,
                    {
                        "radicado": radicado,
                        "tipo_sujeto": tipo_sujeto,
                        "nombre_actor": nombre_actor,
                        "origen": "CEJ_PERU",
                    }
                )
                row = await cursor.fetchone()

            if row:
              
                return True

            self.logger.info(
                f"🆕 No existe dato en DATOS_PROCESOS_RAMA | "
                 f"Radicado={radicado}, tipo sujeto ={tipo_sujeto}, nombre_actor = {nombre_actor}"
            )
            return False

        except Exception as error:
            self.logger.error(
                f"❌ Error validando existencia en DATOS_PROCESOS_RAMA "
                f"Radicado={radicado}, tipo sujeto ={tipo_sujeto}, nombre_actor = {nombre_actor}: {error}"
            )
            raise