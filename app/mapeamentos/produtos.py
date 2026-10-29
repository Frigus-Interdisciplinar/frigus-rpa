"""Tradução de categoria, armazenamento e unidade (origem -> destino)."""
from typing import get_args

from .tipos import Armazenamento, Categoria, CategoriaOrigem, Unidade, UnidadeOrigem

# O destino tem menos categorias, então é aproximação.
CATEGORIA: dict[CategoriaOrigem, Categoria] = {
    "LATICIONIOS": Categoria.DAIRY,
    "OVOS": Categoria.DAIRY,
    "SOBREMESAS": Categoria.DAIRY,
    "CARNES": Categoria.MEAT,
    "PESCADOS": Categoria.MEAT,
    "EMBUTIDOS": Categoria.MEAT,
    "CONGELADOS": Categoria.MEAT,
    "HORTALICAS": Categoria.VEGETABLE,
    "TUBERCULOS": Categoria.VEGETABLE,
    "FRUTAS": Categoria.FRUIT,
    "BEBIDAS": Categoria.BEVERAGE,
    "GRAOS": Categoria.GRAIN,
    "TEMPEROS": Categoria.GRAIN,
    "CONSERVAS_E_ENLATADOS": Categoria.GRAIN,
    "ALIMENTOS_PREPARADOS": Categoria.GRAIN,
}

# Quem não está aqui vai para FRIDGE.
ARMAZENAMENTO: dict[CategoriaOrigem, Armazenamento] = {
    "CONGELADOS": Armazenamento.FREEZER,
    "GRAOS": Armazenamento.PANTRY,
    "TEMPEROS": Armazenamento.PANTRY,
    "CONSERVAS_E_ENLATADOS": Armazenamento.PANTRY,
    "TUBERCULOS": Armazenamento.PANTRY,
}

UNIDADE: dict[UnidadeOrigem, Unidade] = {
    "kg": Unidade.KILOGRAM,
    "L": Unidade.LITER,
    "un": Unidade.UNIT,
    "cento": Unidade.UNIT,
    "dz": Unidade.DOZEN,
    "cx": Unidade.PACKAGE,
    "pct": Unidade.PACKAGE,
    "lata": Unidade.PACKAGE,
    "saco": Unidade.PACKAGE,
    "bd": Unidade.PACKAGE,
    "maço": Unidade.PACKAGE,
    "barril": Unidade.PACKAGE,
}

# Se alguém acrescentar um valor ao Literal e esquecer o mapa, quebra aqui, no import.
assert set(CATEGORIA) == set(get_args(CategoriaOrigem)), "CATEGORIA incompleta"
assert set(UNIDADE) == set(get_args(UnidadeOrigem)), "UNIDADE incompleta"


def categoria(valor: str) -> Categoria:
    if valor not in CATEGORIA:
        raise ValueError(f"categoria sem mapeamento: {valor!r}")

    return CATEGORIA[valor]


def armazenamento(categoria_origem: str) -> Armazenamento:
    return ARMAZENAMENTO.get(categoria_origem, Armazenamento.FRIDGE)


def unidade(valor: str) -> Unidade:
    # Unidade nova na origem não derruba o ciclo: vira PACKAGE (e some do radar).
    return UNIDADE.get(valor, Unidade.PACKAGE)
