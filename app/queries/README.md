# queries

Todo o SQL do projeto, escrito em PyPika. Cada função **devolve um texto SQL**; nada aqui conecta no banco.

| Arquivo | O que tem |
|---|---|
| `origem.py` | selects no dbFrigus. Pessoas/empresas e geladeiras/frigoríficos são unidos (`UNION ALL`) no mesmo formato |
| `destino.py` | busca de id, inserts e contagem no Supabase |

## Parâmetros

- `%s`: posicional, na ordem das colunas.
- `%(nome)s`: nomeado, quando o mesmo valor aparece mais de uma vez (nos inserts com `NOT EXISTS`).

## Como evita duplicar

- `inserir_ignorando_conflito`: `ON CONFLICT DO NOTHING` na restrição única.
- `inserir_item_estoque`, `inserir_despesa`, `inserir_assinatura`: `INSERT ... SELECT ... WHERE NOT EXISTS`.
- `buscar_id` + `inserir_retornando_id`: "acha ou cria" (usado em `obter_ou_criar`, em `app/sync/passos.py`).

Para ver o SQL gerado: `python -c "from app.queries import origem; print(origem.donos())"`.
