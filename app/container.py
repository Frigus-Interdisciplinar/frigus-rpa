"""Dishka: de onde vêm as dependências. Escopo APP = vive o processo todo; REQUEST = um ciclo."""
from collections.abc import Iterator
from typing import NewType

import psycopg2
from dishka import Provider, Scope, make_container, provide
from psycopg2.extensions import connection as Conexao
from psycopg2.extensions import cursor as Cursor
from psycopg2.extras import RealDictCursor

from app.config import Settings
from app.sync.ciclo import Ciclo

# Duas conexões do mesmo tipo: o NewType deixa o Dishka distinguir uma da outra.
ConexaoOrigem = NewType("ConexaoOrigem", Conexao)
ConexaoDestino = NewType("ConexaoDestino", Conexao)
CursorOrigem = NewType("CursorOrigem", Cursor)
CursorDestino = NewType("CursorDestino", Cursor)


class ConfigProvider(Provider):
    scope = Scope.APP

    @provide
    def settings(self) -> Settings:
        return Settings.do_ambiente()


class BancoProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def conexao_origem(self, s: Settings) -> Iterator[ConexaoOrigem]:
        conexao = psycopg2.connect(s.source_dsn, cursor_factory=RealDictCursor)
        conexao.set_session(readonly=True)

        try:
            yield ConexaoOrigem(conexao)
        finally:
            conexao.close()

    @provide
    def conexao_destino(self, s: Settings) -> Iterator[ConexaoDestino]:
        conexao = psycopg2.connect(s.target_dsn)

        try:
            yield ConexaoDestino(conexao)
        finally:
            conexao.close()

    @provide
    def cursor_origem(self, conexao: ConexaoOrigem) -> CursorOrigem:
        return CursorOrigem(conexao.cursor())

    @provide
    def cursor_destino(self, conexao: ConexaoDestino) -> CursorDestino:
        return CursorDestino(conexao.cursor())

    @provide
    def ciclo(self, ori: CursorOrigem, dst: CursorDestino, conexao: ConexaoDestino) -> Ciclo:
        return Ciclo(ori, dst, conexao)


def criar_container():
    return make_container(ConfigProvider(), BancoProvider())
