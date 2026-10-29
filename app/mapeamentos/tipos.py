"""Tipos dos dois lados: Literal para o que vem da origem, StrEnum para o que vai ao destino."""
from enum import StrEnum
from typing import Literal

# ---- origem (dbFrigus): valores que existem hoje nas colunas ----

CategoriaOrigem = Literal[
    "LATICIONIOS", "OVOS", "SOBREMESAS",
    "CARNES", "PESCADOS", "EMBUTIDOS", "CONGELADOS",
    "HORTALICAS", "TUBERCULOS",
    "FRUTAS",
    "BEBIDAS",
    "GRAOS", "TEMPEROS", "CONSERVAS_E_ENLATADOS", "ALIMENTOS_PREPARADOS",
]

UnidadeOrigem = Literal["kg", "L", "un", "cento", "dz", "cx", "pct", "lata", "saco", "bd", "maço", "barril"]

PlanoOrigem = Literal["FREE", "PLUS", "FAMILIA", "COMERCIAL"]

OrigemEstoque = Literal["geladeira", "frigorifico"]


# ---- destino (Supabase) ----

class Tabela(StrEnum):
    USERS = "users"
    GROUPS = "groups"
    USER_GROUPS = "user_groups"
    STOCKS = "stocks"
    PRODUCTS = "products"
    STOCK_PRODUCTS = "stock_products"
    RECIPES = "recipes"
    RECIPE_INGREDIENTS = "recipe_ingredients"
    SHOPPING_LISTS = "shopping_lists"
    SHOPPING_LIST_PRODUCTS = "shopping_list_products"
    BUSINESS_EXPENSES = "business_expenses"
    SUBSCRIPTIONS = "subscriptions"
    NOTIFICATIONS = "notifications"  # só é contada: triggers de stock_products escrevem nela


class Categoria(StrEnum):  # products.category
    DAIRY = "DAIRY"
    MEAT = "MEAT"
    VEGETABLE = "VEGETABLE"
    FRUIT = "FRUIT"
    BEVERAGE = "BEVERAGE"
    GRAIN = "GRAIN"


class Armazenamento(StrEnum):  # products.storage_place
    FRIDGE = "FRIDGE"
    FREEZER = "FREEZER"
    PANTRY = "PANTRY"


class Unidade(StrEnum):  # products.unit_of_measure
    KILOGRAM = "KILOGRAM"
    LITER = "LITER"
    UNIT = "UNIT"
    DOZEN = "DOZEN"
    PACKAGE = "PACKAGE"


class Plano(StrEnum):  # plans.plan_code
    FREE = "FREE"
    PLUS = "PLUS"
    FAMILY = "FAMILY"
    COMMERCIAL = "COMMERCIAL"


class TipoConta(StrEnum):  # users.account_type
    DOMESTIC = "DOMESTIC"
    COMMERCIAL = "COMMERCIAL"


class PapelUsuario(StrEnum):  # users.role
    USER = "USER"


class PapelMembro(StrEnum):  # user_groups.member_role
    EDITOR = "EDITOR"


class StatusLista(StrEnum):  # shopping_lists.status
    OPEN = "OPEN"


class StatusItemLista(StrEnum):  # shopping_list_products.status
    PENDING = "PENDING"


class StatusAssinatura(StrEnum):  # subscriptions.status (tipo subscription_status_enum)
    ACTIVE = "ACTIVE"


class CategoriaDespesa(StrEnum):  # business_expenses.category
    COMPRAS = "COMPRAS"
