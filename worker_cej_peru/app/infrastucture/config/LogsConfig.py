import logging
from pathlib import Path
from logging import FileHandler
from zoneinfo import ZoneInfo
from datetime import datetime
import asyncio

from app.application.dto.HoyPathsDto import HoyPathsDto


class ColombiaFormatter(logging.Formatter):
    def converter(self, timestamp):
        dt = datetime.fromtimestamp(timestamp, tz=ZoneInfo("America/Bogota"))
        return dt

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()


def setup_logger(log_path: Path):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = FileHandler(log_path, encoding="utf-8")
    stream_handler = logging.StreamHandler()

    formatter = ColombiaFormatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'  # formato clásico con hora Colombia
    )

    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


async def start_logger():
    """Monitorea el cambio de día y reinicia los logs solo de lunes a viernes"""
    logger = logging.getLogger()
    zona = ZoneInfo("America/Bogota")

    fecha_actual = datetime.now(zona).date()

    while True:
        await asyncio.sleep(60)  # Verifica cada 60 segundos
        ahora = datetime.now(zona)
        nueva_fecha = ahora.date()

        if nueva_fecha != fecha_actual:
            dia_semana = ahora.weekday()  # 0=lunes, 6=domingo

            if dia_semana < 5:  # lunes (0) a viernes (4)
                logging.info("📅 Cambio de día hábil detectado. Reiniciando archivo de log.")
                paths = HoyPathsDto.build().dict()
                setup_logger(paths["logs_file"])
            else:
                logging.info("📅 Cambio de día (fin de semana). No se crea log.")

            fecha_actual = nueva_fecha
