"""Sincroniza dbFrigus (origem, somente leitura) -> Supabase (destino), de tempos em tempos.

    python main.py            # loop, a cada SYNC_INTERVAL_MINUTES (padrão 60)
    python main.py --once     # um ciclo só
    python main.py --dry-run  # um ciclo só, com rollback

Tabelas, campos e regras: docs/tabelas.md. Visão geral: README.md.
"""
import sys
import time

from dishka import Container
from dotenv import load_dotenv
from loguru import logger
from psycopg2 import InterfaceError, OperationalError
from tenacity import RetryCallState, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import Settings
from app.container import criar_container
from app.sync.ciclo import Ciclo

def avisa_nova_tentativa(estado: RetryCallState) -> None:
    logger.warning("banco indisponível, tentativa {} falhou; tentando de novo", estado.attempt_number)


@retry(
    retry=retry_if_exception_type((OperationalError, InterfaceError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=5, max=60),
    before_sleep=avisa_nova_tentativa,
    reraise=True,
)
def rodar_ciclo(container: Container, dry_run: bool) -> None:
    """Tenta de novo só quando o banco some (rede, conexão caída). Erro de dado não repete."""
    with container() as request:  # conexões novas a cada tentativa
        request.get(Ciclo).executar(dry_run)


def main() -> None:
    load_dotenv()

    dry_run = "--dry-run" in sys.argv
    uma_vez = dry_run or "--once" in sys.argv

    container = criar_container()
    settings = container.get(Settings)

    try:
        while True:
            try:
                rodar_ciclo(container, dry_run)
            except Exception:
                if uma_vez:
                    raise
                logger.exception("ciclo falhou, tenta de novo em {}s", settings.intervalo_segundos)  # não derruba o loop

            if uma_vez:
                break

            time.sleep(settings.intervalo_segundos)
    finally:
        container.close()


if __name__ == "__main__":
    main()
