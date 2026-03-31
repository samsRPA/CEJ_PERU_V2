from typing import Optional

from pydantic import BaseModel, field_validator
from datetime import datetime
class BotReq(BaseModel):
    nombre_completo: Optional[str] = None
    parte: str = None
    radicado: str = None
    demandante: Optional[str] = None
    parte_demandante: Optional[str] = None

   

    @property
    def folderName(self) -> str:
        return f"{self.radicado}"


    @classmethod
    def fromRaw(cls, rawBody: dict):
        return cls(**rawBody)
