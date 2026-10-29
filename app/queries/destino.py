"""Buscas, inserts e contagens do destino (Supabase). Cada função devolve SQL (str); nada aqui acessa o banco.

Parâmetros: %s (posicional) ou %(nome)s (nomeado, quando o mesmo valor aparece mais de uma vez).
"""
from pypika import Parameter, Table
from pypika import PostgreSQLQuery as Query
from pypika.functions import Cast, Concat, Count
from pypika.terms import ExistsCriterion, ValueWrapper

from app.mapeamentos.tipos import CategoriaDespesa, StatusAssinatura

P = Parameter("%s")


def nomeado(nome: str) -> Parameter:
    return Parameter(f"%({nome})s")


def buscar_id(tabela: str, colunas: list[str], soft_delete: bool = False) -> str:
    """select id da linha onde todas as `colunas` batem (%s, na ordem)."""
    t = Table(tabela)
    busca = Query.from_(t).select("id").limit(1)

    for coluna in colunas:
        busca = busca.where(t.field(coluna) == P)

    if soft_delete:
        busca = busca.where(t.deleted_at.isnull())

    return busca.get_sql()


def inserir_retornando_id(tabela: str, colunas: list[str]) -> str:
    insercao = Query.into(tabela).columns(*colunas).insert(*[P] * len(colunas))

    return insercao.returning("id").get_sql()


def inserir_ignorando_conflito(tabela: str, colunas: list[str], conflito: list[str]) -> str:
    """Insert posicional que não faz nada se a restrição única `conflito` já existe."""
    insercao = Query.into(tabela).columns(*colunas).insert(*[P] * len(colunas))

    return insercao.on_conflict(*conflito).do_nothing().get_sql()


def inserir_item_estoque() -> str:
    """Nomeados: stock_id, product_id, quantidade, dtvalidade, lote. Pula se já existe."""
    p, sp = Table("products"), Table("stock_products").as_("sp")

    ja_existe = Query.from_(sp).select(1).where(
        (sp.stock_id == nomeado("stock_id"))
        & (sp.product_id == p.id)
        & (sp.batch == nomeado("lote"))
    )

    insercao = (
        Query.into("stock_products")
        .columns("product_id", "stock_id", "quantity", "expire_date", "category", "batch")
        .from_(p)
        .select(
            p.id,
            nomeado("stock_id"),
            nomeado("quantidade"),
            nomeado("dtvalidade"),
            p.category,
            nomeado("lote"),
        )
        .where((p.id == nomeado("product_id")) & ExistsCriterion(ja_existe).negate())
    )

    return insercao.get_sql()


def inserir_despesa() -> str:
    """Nomeados: group_id, user_id, fornecedor, valor, data. Pula se já existe."""
    grupo = Cast(nomeado("group_id"), "uuid")
    be = Table("business_expenses")

    ja_existe = Query.from_(be).select(1).where(
        (be.group_id == grupo)
        & (be.supplier == nomeado("fornecedor"))
        & (be.expense_date == nomeado("data"))
        & (be.amount == nomeado("valor"))
    )

    insercao = (
        Query.into("business_expenses")
        .columns("group_id", "created_by", "description", "category", "amount", "expense_date", "supplier")
        .select(
            grupo,
            Cast(nomeado("user_id"), "uuid"),
            Concat("Compra em ", nomeado("fornecedor")),
            ValueWrapper(CategoriaDespesa.COMPRAS.value),
            nomeado("valor"),
            nomeado("data"),
            nomeado("fornecedor"),
        )
        .where(ExistsCriterion(ja_existe).negate())
    )

    return insercao.get_sql()


def inserir_assinatura() -> str:
    """Nomeados: user_id, plano. Pula se o usuário já tem alguma assinatura."""
    user_id = Cast(nomeado("user_id"), "uuid")
    pl, s = Table("plans"), Table("subscriptions")

    sem_assinatura = Query.from_(s).select(1).where(s.user_id == user_id)

    insercao = (
        Query.into("subscriptions")
        .columns("user_id", "plan_id", "status")
        .from_(pl)
        .select(
            user_id,
            pl.id,
            Cast(ValueWrapper(StatusAssinatura.ACTIVE.value), "subscription_status_enum"),
        )
        .where((pl.plan_code == nomeado("plano")) & ExistsCriterion(sem_assinatura).negate())
    )

    return insercao.get_sql()


def contar(tabela: str) -> str:
    return Query.from_(Table(tabela)).select(Count("*")).get_sql()
