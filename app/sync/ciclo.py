"""Um ciclo: conta, migra, conta de novo e grava (ou desfaz, no dry-run)."""
import logging

from psycopg2.extensions import connection as Conexao
from psycopg2.extensions import cursor as Cursor

from app.mapeamentos.tipos import Tabela
from app.queries import destino as qd

from . import passos

log = logging.getLogger("rpa")


class Ciclo:
    def __init__(self, ori: Cursor, dst: Cursor, conexao_destino: Conexao) -> None:
        self.ori = ori
        self.dst = dst
        self.conexao_destino = conexao_destino

    def contar(self) -> dict[Tabela, int]:
        contagens = {}

        for tabela in Tabela:
            self.dst.execute(qd.contar(tabela))
            contagens[tabela] = self.dst.fetchone()[0]

        return contagens

    def executar(self, dry_run: bool) -> None:
        try:
            antes = self.contar()
            passos.migrar(self.ori, self.dst)
            depois = self.contar()

            if dry_run:
                self.conexao_destino.rollback()
            else:
                self.conexao_destino.commit()

        except Exception:
            self.conexao_destino.rollback()
            raise

        novos = {t.value: depois[t] - antes[t] for t in Tabela if depois[t] != antes[t]}
        log.info("%s: %s", "dry-run (rollback)" if dry_run else "commit", novos or "nada novo")
