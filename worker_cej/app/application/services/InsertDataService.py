import logging
import os

from app.domain.interfaces.IS3Manager import IS3Manager
from app.infrastructure.database.repositories.ControlAutosRep import ControlAutosRep
from app.domain.interfaces.IInsertDataService import IInsertDataService
from app.infrastructure.database.repositories.DatosRamaRep import DatosRamaRep
from app.infrastructure.database.repositories.ActorsRamaRep import ActorsRamaRep

class InsertDataService(IInsertDataService):
    
    def __init__(self, s3Manager:IS3Manager,  controlAutosRep:ControlAutosRep, datosRamaRep:DatosRamaRep, actorsRamaRep: ActorsRamaRep ):
        self.s3Manager = s3Manager
        self.controlAutosRep = controlAutosRep
        self.datosRamaRep = datosRamaRep
        self.actorsRamaRep = actorsRamaRep
        self.logger = logging.getLogger(__name__)

    async def  insertCaseReport(self,conn, radicado, dataName, dataValue):
        try:
         
            exists = await self.datosRamaRep.processDataRamaExists( conn=conn, radicado=radicado, dataName= dataName,dataValue=str(dataValue), origen="CEJ_PERU")

            if not exists:
                await self.datosRamaRep.insertProcessDataRama( conn=conn, radicado=radicado, dataName= dataName, dataValue=str(dataValue), usuario="CEJ_PERU", origen="CEJ_PERU")
                    
        except Exception :
            self.logger.exception("🔴 Error al insertar en datos proceso rama")
            raise

    async def  insertActorsRama(self,conn, radicado, subjectType, actorName):
        try:

            existsActor = await self.actorsRamaRep.actorRamaExists(conn,radicado,subjectType, actorName)  
    
            if not existsActor:
                await self.actorsRamaRep.insertActorRama(conn,radicado,subjectType, actorName)  
                
        except Exception :
            self.logger.exception("🔴 Error al insertar en actores rama")
            raise
        
    async def autoExists(self, conn, autoDate, radicado, origin, consecutiveMap) -> bool:

        formattedDate = autoDate.strftime("%d-%m-%Y")
        mapKey = f"{radicado}-{ formattedDate}"
        
        dataToCheck = {
            "FECHA_NOTIFICACION": autoDate,
            "RADICACION": radicado,
            "ORIGEN": origin
        }

        if mapKey in consecutiveMap:
            consecutivo = consecutiveMap[mapKey]
            consecutiveMap[mapKey] += 1
        else:
            max_consecutivo = await  self.controlAutosRep .getMaxConsecutive(conn, dataToCheck)
            consecutivo = max_consecutivo + 1
            consecutiveMap[mapKey] = consecutivo + 1

        dataToCheck["CONSECUTIVO"] = consecutivo

        existsAuto = await self.controlAutosRep.autoExists(conn, dataToCheck)

        return consecutivo, existsAuto

    
    async def insertAuto(self, autoDate, radicado,  origin, conn,  outputDir, originalFilePath,consecutivo):
        try:
            formattedDate = autoDate.strftime("%d-%m-%Y")
            registrationDateTyba = autoDate.strftime("%d-%m-%Y 00:00:00")
            fileNameBd = f"{formattedDate}_{radicado}_{consecutivo}.pdf"
            rutaS3 = fileNameBd.removesuffix(".pdf")
            newFilePath = os.path.join(outputDir, fileNameBd)

            os.replace(originalFilePath, newFilePath)

            # its_uploades_s3_auto = self.s3Manager.uploadFile(self,newFilePath)

            # if not its_uploades_s3_auto:
            #     self.logger.warning(f"⚠️ Error al subir {newFilePath} a S3 ")
            #     return None

            # insert_auto = await self.controlAutosRep.insertAuto(
            #     conn, formattedDate, radicado, consecutivo,
            #     rutaS3, origin, "pdf", registrationDateTyba
            # )

            # if not insert_auto:
            #     return None

            # self.logger.info(f" 🔵 Insertado  {origin} en control autos rama 1 con radicado {radicado}, fecha {formattedDate} y consecutivo {consecutivo} ")

            return newFilePath
        except Exception as e :
            self.logger.exception(f"🔴 Error al insertar autos {e}")
            return None