
from app.domain.interfaces.IScrapperService import IScrapperService

import logging
from app.application.dto.HoyPathsDto import HoyPathsDto

from app.domain.interfaces.IDataBase import IDataBase
from app.domain.interfaces.ICEJScrapperService import ICEJScrapperService
from app.application.dto.ProceedingsRequestDto import ProceedingsRequestDto


class ScrapperService(IScrapperService):


  
    def __init__(self,body: ProceedingsRequestDto,cej_scrapper:ICEJScrapperService, ):
        self.body = body
        self.cej_scrapper=cej_scrapper
        self.logger= logging.getLogger(__name__)

    async def runScrapper(self):
        
        try:   
          
            # Construir el DTO que espera run_multi
            case_information = ProceedingsRequestDto(
                nombre_completo= self.body.nombre_completo,
                #identificacion_cliente=self.body.identificacion_cliente,
                
                parte=self.body.parte,
                radicado=self.body.radicado,
                demandante=self.body.demandante,
                parte_demandante=self.body.parte_demandante,
            )

            # Campo obligatorio sí o sí
            if not case_information.parte or str(case_information.parte).strip() == "":
                self.logger.warning(f"El campo 'parte' es obligatorio.")
                return {"error": "El campo 'parte' es obligatorio."}


            await self.cej_scrapper.scrapper(case_information)

        except Exception as e:
            self.logger.error(f"❌ Error : {e}")
            raise e
       
