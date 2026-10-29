"""Selects da origem (dbFrigus, somente leitura). Cada função devolve SQL (str); nada aqui acessa o banco."""
from pypika import PostgreSQLQuery as Query
from pypika import Field, Table
from pypika.functions import Coalesce, Concat
from pypika.terms import ValueWrapper

from app.mapeamentos.tipos import TipoConta


def donos() -> str:
    """Pessoas (usuario) e empresas, no mesmo formato."""
    u, e = Table("usuario"), Table("empresa")

    pessoas = Query.from_(u).select(
        u.cpf.as_("documento"),
        Concat(u.nome, " ", u.sobrenome).as_("nome"),
        u.email,
        ValueWrapper(TipoConta.DOMESTIC.value).as_("tipo"),
        Concat("Casa de ", u.nome).as_("grupo"),
    )
    empresas = Query.from_(e).select(
        e.cnpj,
        e.nome,
        e.email,
        ValueWrapper(TipoConta.COMMERCIAL.value),
        e.nome,
    )

    return pessoas.union_all(empresas).get_sql()


def estoques() -> str:
    """Geladeiras (pessoas) e frigoríficos (empresas), no mesmo formato."""
    g, f = Table("geladeira"), Table("frigorifico")

    geladeiras = Query.from_(g).select(
        ValueWrapper("geladeira").as_("origem"),
        g.id,
        g.idusuario.as_("documento"),
        g.nome,
    )
    frigorificos = Query.from_(f).select(
        ValueWrapper("frigorifico"),
        f.id,
        f.idempresa,
        f.nome,
    )

    return geladeiras.union_all(frigorificos).orderby("id").get_sql()


def produtos() -> str:
    produtos = Query.from_("produto").select(
        "id", "nome", "marca", "preco", "categoria", "unidademedida",
    )

    return produtos.get_sql()


def itens_estoque() -> str:
    """Produtos dentro de geladeiras e frigoríficos, no mesmo formato."""
    g, f = Table("itemgeladeira"), Table("itemfrigorifico")
    colunas = ("quantidade", "dtvalidade", "lote")

    da_geladeira = Query.from_(g).select(
        ValueWrapper("geladeira").as_("origem"),
        g.idgeladeira.as_("estoque"),
        g.idproduto.as_("idprodutos"),
        *(g[c] for c in colunas),
    )
    do_frigorifico = Query.from_(f).select(
        ValueWrapper("frigorifico"),
        f.idfrigorifico,
        f.idproduto,
        *(f[c] for c in colunas),
    )

    return da_geladeira.union_all(do_frigorifico).get_sql()


def receitas() -> str:
    receitas = Query.from_("receita").select("id", "nome", "descricao", "modopreparo")

    return receitas.get_sql()


def ingredientes() -> str:
    ingredientes = Query.from_("ingrediente").select("idreceita", Field("idproduto").as_("idprodutos"), "quantidade")

    return ingredientes.get_sql()


def listas() -> str:
    l = Table("listacompras")

    listas = Query.from_(l).select(
        l.id,
        Coalesce(l.idusuario, l.idempresa).as_("documento"),
        l.dtlista.as_("data"),
    )

    return listas.get_sql()


def itens_lista() -> str:
    itens = Query.from_("itemlista").select("idlistacompras", Field("idproduto").as_("idprodutos"), "quantidade")

    return itens.get_sql()


def compras() -> str:
    c = Table("compra")

    compras = Query.from_(c).select(
        Coalesce(c.idusuario, c.idempresa).as_("documento"),
        c.ondecomprou.as_("fornecedor"),
        c.dtcompra.as_("data"),
        c.valorcompra.as_("valor"),
    )

    return compras.get_sql()


def assinaturas() -> str:
    a = Table("assinatura")

    assinaturas = Query.from_(a).select(
        Coalesce(a.idusuario, a.idempresa).as_("documento"),
        a.tipoassinatura,
    )

    return assinaturas.get_sql()
