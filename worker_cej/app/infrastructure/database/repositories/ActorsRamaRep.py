import logging


class ActorsRamaRep:

    
    
    def __init__(self, table):
        self.table = table
        self.logger = logging.getLogger(__name__)


    async def insertActorRama(self, conn, caseNumber: str, subjectType: str, actorName: str) -> None:
      
        try:
            query = """
            INSERT INTO ACTORES_RAMA (
                RADICADO_RAMA,
                TIPO_SUJETO,
                NOMBRE_ACTOR,
                FECHA_CREACION_REGISTRO,
                ORIGEN_DATOS
            ) VALUES (
                :caseNumber,
                :subjectType,
                :actorName,
                SYSDATE,
                :dataSource
            )
            """

            async with conn.cursor() as cursor:
                await cursor.execute(
                    query,
                    {
                        "caseNumber": caseNumber,
                        "subjectType": subjectType,
                        "actorName": actorName,
                        "dataSource": "CEJ_PERU"
                    }
                )

            self.logger.info(
                f"✅ Insertado en ACTORES_RAMA | "
                f"numeroProceso={caseNumber}, tipoSujeto={subjectType}, nombreActor={actorName}"
            )

        except Exception as error:
            self.logger.error(
                f"❌ Error  inserting into ACTORES_RAMA | "
                f"caseNumber={caseNumber}, subjectType={subjectType}, actorName={actorName}: {error}"
            )
            raise


    async def actorRamaExists(self, conn, caseNumber: str, subjectType: str, actorName: str) -> bool:
    
        try:
            query = """
                SELECT 1
                FROM ACTORES_RAMA
                WHERE RADICADO_RAMA = :caseNumber
                AND TIPO_SUJETO = :subjectType
                AND NOMBRE_ACTOR = :actorName
                AND ORIGEN_DATOS = :dataSource
                FETCH FIRST 1 ROWS ONLY
            """

            async with conn.cursor() as cursor:
                await cursor.execute(
                    query,
                    {
                        "caseNumber": caseNumber,
                        "subjectType": subjectType,
                        "actorName": actorName,
                        "dataSource": "CEJ_PERU",
                    }
                )
                row = await cursor.fetchone()

            if row:
                return True

       
            return False

        except Exception as error:
            self.logger.error(
                f"❌ Error checking existence in ACTORES_RAMA | "
                f"caseNumber={caseNumber}, subjectType={subjectType}, actorName={actorName}: {error}"
            )
            raise