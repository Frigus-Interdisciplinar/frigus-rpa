"""Tradução de plano de assinatura (origem -> destino)."""
from typing import get_args

from .tipos import Plano, PlanoOrigem

PLANO: dict[PlanoOrigem, Plano] = {
    "FREE": Plano.FREE,
    "PLUS": Plano.PLUS,
    "FAMILIA": Plano.FAMILY,
    "COMERCIAL": Plano.COMMERCIAL,
}

assert set(PLANO) == set(get_args(PlanoOrigem)), "PLANO incompleto"


def plano(valor: str) -> Plano:
    if valor not in PLANO:
        raise ValueError(f"plano sem mapeamento: {valor!r}")

    return PLANO[valor]
