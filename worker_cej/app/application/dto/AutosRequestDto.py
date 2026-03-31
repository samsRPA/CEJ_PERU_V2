import json

from pydantic import BaseModel
from pydantic import ValidationError

class AutosRequestDto(BaseModel):
    uuid:str
    fecha:str
    radicado:str
    #consecutivo:int
    cod_despacho_rama:str
    actuacion_rama:str 
    anotacion_rama:str 
    origen_datos: str
    fecha_registro_tyba: str
    
    



