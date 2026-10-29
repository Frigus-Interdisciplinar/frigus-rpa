"""Configuração lida do ambiente (.env)."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    source_dsn: str
    target_dsn: str
    intervalo_segundos: int

    @classmethod
    def do_ambiente(cls) -> "Settings":
        return cls(
            source_dsn=os.environ["SOURCE_DSN"],
            target_dsn=os.environ["TARGET_DSN"],
            intervalo_segundos=int(os.getenv("SYNC_INTERVAL_MINUTES", "60")) * 60,
        )
