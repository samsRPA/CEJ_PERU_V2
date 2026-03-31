# app/domain/exceptions.py
class BlockedByBotManagerError(Exception):
    """Se lanza cuando Radware bloquea la IP/sesión."""
    pass