# dbFrigus -> Supabase

Copia dados do dbFrigus (origem, só leitura) para o Supabase (destino), de tempos em tempos.

```
pip install -r requirements.txt
cp .env.example .env     # preencha os DSNs
python main.py           # loop: sincroniza e dorme SYNC_INTERVAL_MINUTES
python main.py --once    # um ciclo só (cron / Agendador de Tarefas)
python main.py --dry-run # um ciclo só, mostra o que entraria e desfaz
```

## .env

| Variável | Para quê | Padrão |
|---|---|---|
| `SOURCE_DSN` | conexão com o dbFrigus | — |
| `TARGET_DSN` | conexão com o Supabase (use a direta ou o pooler em modo session, porta 5432) | — |
| `SYNC_INTERVAL_MINUTES` | pausa entre ciclos | 60 |

## Pastas

```
main.py            entrada: argumentos, loop e retry
app/config.py      lê o .env
app/container.py   Dishka: monta conexões e cursores
app/mapeamentos/   tipos (Enum/Literal) e tradução de valores
app/queries/       todo o SQL (PyPika): origem.py e destino.py
app/sync/          os passos da migração e o ciclo
docs/tabelas.md    tabela a tabela: origem, destino, campos e regras
```

Cada pasta de `app/` tem um README próprio.

## Como funciona, em 4 linhas

1. Cada ciclo abre conexões novas, lê a origem inteira e grava só o que ainda não existe no destino.
2. Tudo roda numa transação: erro = rollback, nada fica pela metade.
3. Se o banco cair (rede, conexão), o ciclo é repetido com espera crescente (3 tentativas, `@retry` em `main.py`). Erro de dado não é repetido.
4. Valor novo na origem sem tradução em `app/mapeamentos/` interrompe o ciclo com erro claro.

## Limites

- Só insere. Alterações e exclusões na origem não chegam ao destino.
- Cada ciclo relê a origem inteira.
- Fora da cópia: `endereco`, `marcasparceiras`, `notificacao` (sem equivalente) e senhas.
