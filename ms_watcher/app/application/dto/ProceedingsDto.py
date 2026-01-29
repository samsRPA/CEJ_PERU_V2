from typing import Optional
from pydantic import BaseModel

class ProceedingsDto(BaseModel):
    nombre_completo:Optional[str] = None
    parte: Optional[str] = None
    radicado: Optional[str] = None
    demandante: Optional[str] = None
    parte_demandante: Optional[str] = None
    
    
