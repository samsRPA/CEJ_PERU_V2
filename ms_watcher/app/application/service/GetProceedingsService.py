import pandas as pd
import logging
from app.domain.interfaces.IGetProceedingsService import IGetProceedingsService
from app.application.dto.ProceedingsDto import ProceedingsDto
import json

from app.domain.interfaces.IDataBase import IDataBase
from app.infrastucture.database.repositories.KeyCEJRepository import KeyCEJRepository

class GetProceedingsService(IGetProceedingsService):

    

    def __init__(self,db:IDataBase,repository:KeyCEJRepository):
        self.db = db
        self.repository = repository
        self.logger = logging.getLogger(__name__)

    async def get_proceedings(self):
        conn = None
        try:
            conn = await self.db.acquire_connection()
            raw_keys = await self.repository.get_keys_cej(conn)

            proceedings_list = []

            for row in raw_keys:
                # row = (PROCESO_ID, INSTANCIA_RADICACION, ..., DEMANDADO)

                instancia_radicacion = self._clean(row[1])
                demandado_raw = self._clean(row[5])
                demandante_raw = self._clean(row[4])
                # Extraer apellidos igual que en Excel
                demandado_apellidos = self._extract_surnames(demandado_raw)
                parte_demandante = self._extract_surnames( demandante_raw )

                dto = ProceedingsDto(
                    nombre_completo=demandado_raw ,
                    parte=demandado_apellidos,
                    radicado=instancia_radicacion,
                    demandante=demandado_apellidos,
                    parte_demandante=parte_demandante
                )
                proceedings_list.append(dto)
                break
       
            return proceedings_list
        
        finally:
            if conn:
                await self.db.release_connection(conn)

    def _clean(self, value):
        # Si llega una Serie → tomar primer elemento
        if isinstance(value, pd.Series):
            value = value.iloc[0] if not value.empty else ""

        if pd.isna(value):
            return ""

        value = str(value).strip()
        
        return " ".join(value.split())

    def _extract_surnames(self,nombre):
        
        partes = nombre.split() 

        if len(partes) == 1:
            return partes[0]

        if len(partes) == 2:
            return partes[1]

        if len(partes) == 3:
            return " ".join(partes[-2:])
        
        # 4 palabras o más → todo después de las primeras dos
        return " ".join(partes[2:])
