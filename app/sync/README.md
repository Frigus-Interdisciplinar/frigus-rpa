# sync

| Arquivo | O que tem |
|---|---|
| `passos.py` | uma função por assunto (`migrar_donos`, `migrar_estoques`...) e `migrar()`, que chama todas na ordem |
| `ciclo.py` | `Ciclo.executar()`: conta as linhas, migra, conta de novo, faz commit (ou rollback no `--dry-run`) e loga o que entrou |

## Ordem (importa, um passo usa o resultado do outro)

1. `migrar_donos` -> `{documento: Dono(user_id, group_id)}`
2. `migrar_estoques` -> `{(origem, id): stock_id}` e o estoque principal de cada dono
3. `migrar_produtos` -> `{produtos.id: products.id}`
4. `migrar_itens_estoque`, `migrar_receitas`, `migrar_listas`, `migrar_compras`, `migrar_assinaturas`

## Regra de ouro

Cada passo é **idempotente**: roda de novo e não duplica. Como cada um decide "já existe" está em `docs/tabelas.md` (coluna "Chave").

`Ciclo` recebe cursores e conexão prontos (injetados pelo Dishka em `app/container.py`) e não abre conexão sozinho.
