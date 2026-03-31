import logging
from app.domain.interfaces.IDatabase import IDatabase
from app.domain.interfaces.IBrokerProducer import IBrokerProducer

from app.application.dto.CaseNumberDto import CaseNumberDto
from app.domain.interfaces.ICEJPeruService import ICEJPeruService
from app.infrastructure.database.repositories.CEJRep import CEJRep


class CEJPeruService(ICEJPeruService):
    def __init__(self, db: IDatabase, cejRep: CEJRep, producer: IBrokerProducer):
        self.db = db
        self.producer = producer
        self.cejRep = cejRep

    async def _getCaseNumber(self, caseNumber: str):
        conn = None
        try:
            conn = await self.db.acquireConnection()
            return await self.cejRep.getCaseNumber(conn, caseNumber)
        except Exception as e:
            raise e
        finally:
            if conn:
                await self.db.releaseConnection(conn)

    async def _getAllCaseNumbers(self):
        conn = None
        try:
            conn = await self.db.acquireConnection()
            return await self.cejRep.getAllCaseNumbers(conn)
        except Exception as e:
            raise e
        finally:
            if conn:
                await self.db.releaseConnection(conn)

    async def _publishPayload(self, case: CaseNumberDto):
        message = {
            "radicado":        case.radicado,
            "nombre_completo": case.nombre_completo,
            "parte":           case.parte,
            "demandante":      case.demandante,
            "parte_demandante": case.parte_demandante,
        }
        await self.producer.publishMessage(message)

    async def publishCaseNumber(self, caseNumber: str):
        try:
            rawRow = await self._getCaseNumber(caseNumber)
            case = CaseNumberDto.fromRaw(rawRow)
            await self._publishPayload(case)
        except Exception as e:
            logging.error(f"🔴 Error en publishCaseNumber: {e}")
            raise

    async def publishAllCaseNumbers(self):
        try:
            cases = await self._getAllCaseNumbers()
            for rawRow in cases:
                case = CaseNumberDto.fromRaw(rawRow)
                await self._publishPayload(case)
        except Exception as e:
            logging.error(f"🔴 Error en publishAllCaseNumbers: {e}")
            raise