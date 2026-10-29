"""Passos da sincronização, na ordem em que rodam. Cada um lê da origem e grava no destino."""
import logging
from typing import NamedTuple

from psycopg2.extensions import cursor as Cursor
from psycopg2.extras import execute_batch

from app import mapeamentos
from app.mapeamentos.tipos import PapelMembro, PapelUsuario, StatusItemLista, StatusLista, Tabela
from app.queries import destino as qd
from app.queries import origem as qo

log = logging.getLogger("rpa")

Id = int | str  # users, groups e shopping_lists usam uuid (str); o resto, inteiro
NOME_LISTA = "Lista de compras"


class Dono(NamedTuple):
    user_id: str
    group_id: str


def ler(ori: Cursor, sql: str) -> list[dict]:
    ori.execute(sql)

    return ori.fetchall()


def obter_ou_criar(
    dst: Cursor, tabela: Tabela, chave: dict, extra: dict | None = None, soft_delete: bool = False
) -> Id:
    """Id da linha cujas colunas batem com `chave`; se não existe, insere `chave` + `extra`."""
    busca = qd.buscar_id(tabela, list(chave), soft_delete)
    dst.execute(busca, list(chave.values()))

    if linha := dst.fetchone():
        return linha[0]

    dados = chave | (extra or {})
    insercao = qd.inserir_retornando_id(tabela, list(dados))
    dst.execute(insercao, list(dados.values()))

    return dst.fetchone()[0]


def migrar_donos(ori: Cursor, dst: Cursor) -> dict[str, Dono]:
    """Cada dono (pessoa ou empresa) vira um user com um grupo próprio. Chave: email."""
    donos = {}

    for r in ler(ori, qo.donos()):
        user_id = obter_ou_criar(
            dst,
            Tabela.USERS,
            {"email": r["email"]},
            {"name": r["nome"], "account_type": r["tipo"], "role": PapelUsuario.USER},
        )

        group_id = obter_ou_criar(
            dst,
            Tabela.GROUPS,
            {"owner_id": user_id},
            {"name": r["grupo"]},
            soft_delete=True,
        )

        vinculo = qd.inserir_ignorando_conflito(
            Tabela.USER_GROUPS,
            ["user_id", "group_id", "member_role"],
            ["user_id", "group_id"],
        )
        dst.execute(vinculo, (user_id, group_id, PapelMembro.EDITOR))

        donos[r["documento"]] = Dono(user_id, group_id)

    return donos


def migrar_estoques(
    ori: Cursor, dst: Cursor, donos: dict[str, Dono]
) -> tuple[dict[tuple[str, int], Id], dict[str, Id]]:
    """Geladeira (pessoa) e frigorífico (empresa) viram stocks do grupo do dono.

    Devolve {(tabela de origem, id): stock_id} e {dono: primeiro stock_id}, porque as
    listas de compra da origem não apontam para estoque nenhum.
    """
    estoques = {}
    principal = {}

    for r in ler(ori, qo.estoques()):
        stock_id = obter_ou_criar(
            dst,
            Tabela.STOCKS,
            {"group_id": donos[r["documento"]].group_id, "name": r["nome"]},
            soft_delete=True,
        )

        estoques[r["origem"], r["id"]] = stock_id
        principal.setdefault(r["documento"], stock_id)

    return estoques, principal


def migrar_produtos(ori: Cursor, dst: Cursor) -> dict[int, Id]:
    """Devolve {produtos.id: products.id}. Chave: nome."""
    produtos = {}

    for r in ler(ori, qo.produtos()):
        extra = {
            "brand": r["marca"],
            "unit_price": r["preco"],
            "category": mapeamentos.categoria(r["categoria"]),
            "storage_place": mapeamentos.armazenamento(r["categoria"]),
            "unit_of_measure": mapeamentos.unidade(r["unidademedida"]),
        }

        produtos[r["id"]] = obter_ou_criar(dst, Tabela.PRODUCTS, {"name": r["nome"]}, extra)

    return produtos


def migrar_itens_estoque(
    ori: Cursor, dst: Cursor, estoques: dict[tuple[str, int], Id], produtos: dict[int, Id]
) -> None:
    """Chave: estoque + produto + lote. O status vem de trigger do destino, não é copiado."""
    itens = []

    for r in ler(ori, qo.itens_estoque()):
        itens.append(r | {
            "stock_id": estoques[r["origem"], r["estoque"]],
            "product_id": produtos[r["idprodutos"]],
            "lote": str(r["lote"]),
        })

    execute_batch(dst, qd.inserir_item_estoque(), itens)


def migrar_receitas(ori: Cursor, dst: Cursor, produtos: dict[int, Id]) -> None:
    """Chave da receita: nome (receitas com o mesmo nome têm o mesmo conteúdo na origem)."""
    receitas = {}

    for r in ler(ori, qo.receitas()):
        extra = {"description": r["descricao"], "instructions": r["modopreparo"]}

        receitas[r["id"]] = obter_ou_criar(dst, Tabela.RECIPES, {"name": r["nome"]}, extra)

    ingredientes = []

    for r in ler(ori, qo.ingredientes()):
        ingredientes.append((
            receitas[r["idreceita"]],
            produtos[r["idprodutos"]],
            r["quantidade"],
        ))

    insercao = qd.inserir_ignorando_conflito(
        Tabela.RECIPE_INGREDIENTS,
        ["recipe_id", "product_id", "quantity"],
        ["recipe_id", "product_id"],
    )
    execute_batch(dst, insercao, ingredientes)


def migrar_listas(
    ori: Cursor, dst: Cursor, principal: dict[str, Id], produtos: dict[int, Id]
) -> None:
    """A lista usa o primeiro estoque do dono; sem estoque, é ignorada. Chave: estoque + data."""
    listas = {}

    for r in ler(ori, qo.listas()):
        if r["documento"] not in principal:
            log.warning("lista %s ignorada, dono sem estoque", r["id"])
            continue

        chave = {"stock_id": principal[r["documento"]], "date": r["data"], "name": NOME_LISTA}

        extra = {"status": StatusLista.OPEN}

        listas[r["id"]] = obter_ou_criar(dst, Tabela.SHOPPING_LISTS, chave, extra)

    itens = []

    for r in ler(ori, qo.itens_lista()):
        if r["idlistacompras"] not in listas:
            continue

        itens.append((
            listas[r["idlistacompras"]],
            produtos[r["idprodutos"]],
            r["quantidade"],
            StatusItemLista.PENDING,
        ))

    insercao = qd.inserir_ignorando_conflito(
        Tabela.SHOPPING_LIST_PRODUCTS,
        ["list_id", "product_id", "quantity", "status"],
        ["list_id", "product_id"],
    )
    execute_batch(dst, insercao, itens)


def migrar_compras(ori: Cursor, dst: Cursor, donos: dict[str, Dono]) -> None:
    """Compra vira despesa do grupo do dono. Chave: grupo + fornecedor + data + valor."""
    despesas = []

    for r in ler(ori, qo.compras()):
        dono = donos[r["documento"]]

        despesas.append(r | {"user_id": dono.user_id, "group_id": dono.group_id})

    execute_batch(dst, qd.inserir_despesa(), despesas)


def migrar_assinaturas(ori: Cursor, dst: Cursor, donos: dict[str, Dono]) -> None:
    """Só cria se o dono ainda não tem assinatura. O plano vem de plans.plan_code."""
    assinaturas = []

    for r in ler(ori, qo.assinaturas()):
        assinaturas.append({
            "user_id": donos[r["documento"]].user_id,
            "plano": mapeamentos.plano(r["tipoassinatura"]),
        })

    execute_batch(dst, qd.inserir_assinatura(), assinaturas)


def migrar(ori: Cursor, dst: Cursor) -> None:
    donos = migrar_donos(ori, dst)
    estoques, principal = migrar_estoques(ori, dst, donos)
    produtos = migrar_produtos(ori, dst)

    migrar_itens_estoque(ori, dst, estoques, produtos)
    migrar_receitas(ori, dst, produtos)
    migrar_listas(ori, dst, principal, produtos)
    migrar_compras(ori, dst, donos)
    migrar_assinaturas(ori, dst, donos)
