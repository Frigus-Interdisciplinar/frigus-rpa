# mapeamentos

Define os valores válidos de cada lado e como um vira o outro.

| Arquivo | O que tem |
|---|---|
| `tipos.py` | `Literal` = valores que vêm da origem. `StrEnum` = valores aceitos no destino (e nomes das tabelas) |
| `produtos.py` | categoria, armazenamento e unidade |
| `planos.py` | plano de assinatura |

## Regras

- Os mapas são `origem -> destino`, tipados: `dict[CategoriaOrigem, Categoria]`. O editor/mypy avisa se o valor não existe.
- Ao importar, um `assert` confere se o mapa cobre **todos** os valores do `Literal`. Esqueceu um? Quebra na hora, não no meio da sincronização.
- Valor desconhecido que chega em runtime:
  - categoria e plano: **erro** (`ValueError`), o ciclo para.
  - unidade: vira `PACKAGE` (decisão antiga, mantida).
  - armazenamento: o que não está no mapa vai para `FRIDGE`.

## Como mudar

- **Mudar uma regra**: edite o valor no dicionário (`produtos.py` ou `planos.py`).
- **Valor novo na origem**: acrescente no `Literal` de `tipos.py` e no mapa. Sem os dois, o import falha.
- **Valor novo no destino**: acrescente no `StrEnum` de `tipos.py`.
- **Constantes fixas do sync** (`USER`, `EDITOR`, `OPEN`, `PENDING`, `ACTIVE`, `COMPRAS`) também são enums aqui, para não ter texto solto no código.

As tabelas de tradução completas estão em `docs/tabelas.md`.
