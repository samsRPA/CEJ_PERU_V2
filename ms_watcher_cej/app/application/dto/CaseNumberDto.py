import re
from typing import Optional
from pydantic import BaseModel


class CaseNumberDto(BaseModel):

    nombre_completo: Optional[str] = None
    parte: str = None
    radicado: str = None
    demandante: Optional[str] = None
    parte_demandante: Optional[str] = None

    @classmethod
    def fromRaw(cls, row: tuple) -> "CaseNumberDto":
        if not row or not row[0]:
            raise ValueError("Resultado de la consulta CaseNumberDto vacío o inválido.")

        instancia_radicacion = cls._clean(row[1])
        demandado_raw = cls._clean(row[5])
        demandante_raw = cls._clean(row[4])

        demandado_apellidos = cls._extract_surnames(demandado_raw)
        parte_demandante = cls._extract_surnames(demandante_raw)

        return cls(
            nombre_completo=demandado_raw,
            parte=demandado_apellidos,
            radicado=instancia_radicacion,
            demandante=demandado_apellidos,
            parte_demandante=parte_demandante,
        )

    @staticmethod
    def _clean(value) -> str:
        if value is None:
            return ""
        value = str(value).strip()
        return " ".join(value.split())

    @staticmethod
    def _extract_surnames(nombre: str) -> str:
        partes = nombre.split()

        if len(partes) <= 1:
            return partes[0] if partes else ""
        if len(partes) == 2:
            return partes[1]
        if len(partes) == 3:
            return " ".join(partes[-2:])

        # 4 palabras o más → todo después de las primeras dos
        return " ".join(partes[2:])