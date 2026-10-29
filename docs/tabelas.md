# Tabelas, campos e regras

**Origem** = dbFrigus (PostgreSQL, só leitura). **Destino** = Supabase.
SQL de leitura: `app/queries/origem.py`. Passos: `app/sync/passos.py`.

"Chave" = o que o sync usa para decidir se a linha já existe. Se existe, nada é feito (não atualiza).

## Visão rápida

| Origem (dbFrigus) | Destino (Supabase) | Passo |
|---|---|---|
| `usuario`, `empresa` | `users`, `groups`, `user_groups` | `migrar_donos` |
| `geladeira`, `frigorificos` | `stocks` | `migrar_estoques` |
| `produtos` | `products` | `migrar_produtos` |
| `produtosgeladeira`, `produtosfrigorifico` | `stock_products` | `migrar_itens_estoque` |
| `receita`, `ingredientes` | `recipes`, `recipe_ingredients` | `migrar_receitas` |
| `listacompras`, `produtolista` | `shopping_lists`, `shopping_list_products` | `migrar_listas` |
| `compra` | `business_expenses` | `migrar_compras` |
| `assinatura` | `subscriptions` | `migrar_assinaturas` |
| `endereco`, `marcasparceiras`, `notificacao` | — (sem equivalente, não copiados) | — |

Senhas não são copiadas. `notifications` (destino) só é contada: triggers de `stock_products` podem criar linhas lá.

## Conceito central: "dono"

Pessoa (`usuario`, id = `cpf`) e empresa (`empresa`, id = `cnpj`) viram a mesma coisa no destino: um **user** com um **grupo próprio**. O CPF/CNPJ aparece no código como `documento` e liga todas as outras tabelas ao dono.

---

## Donos -> `users`, `groups`, `user_groups`

| Destino | Campo | Vem de |
|---|---|---|
| `users` | `email` | `usuario.email` / `empresa.email` |
| | `name` | `usuario.nome + " " + sobrenome` / `empresa.nome` |
| | `account_type` | pessoa = `DOMESTIC`, empresa = `COMMERCIAL` |
| | `role` | fixo `USER` |
| `groups` | `owner_id` | id do user acima |
| | `name` | pessoa: `"Casa de " + nome` / empresa: `empresa.nome` |
| `user_groups` | `user_id`, `group_id` | ids acima |
| | `member_role` | fixo `EDITOR` |

- **Chave**: `users.email`; `groups.owner_id` (ignora grupos com `deleted_at`); `user_groups(user_id, group_id)`.

## Estoques -> `stocks`

| Campo | Vem de |
|---|---|
| `group_id` | grupo do dono (`geladeira.idusuario` / `frigorificos.idempresa`) |
| `name` | `geladeira.nome` / `frigorificos.nome` |

- **Chave**: `group_id + name` (ignora `deleted_at`).
- A lista de compras da origem não aponta para estoque. Por isso o sync guarda o **primeiro estoque** de cada dono (o "principal") e usa nas listas.

## Produtos -> `products`

| Campo | Vem de | Regra |
|---|---|---|
| `name` | `produtos.nome` | |
| `brand` | `produtos.marca` | |
| `unit_price` | `produtos.preco` | |
| `category` | `produtos.categoria` | tabela abaixo |
| `storage_place` | `produtos.categoria` | tabela abaixo |
| `unit_of_measure` | `produtos.unidademedida` | tabela abaixo |

- **Chave**: `name`.

### Categoria (`products.category`) — aproximação, o destino tem menos categorias

| Destino | Origem |
|---|---|
| `DAIRY` | LATICIONIOS, OVOS, SOBREMESAS |
| `MEAT` | CARNES, PESCADOS, EMBUTIDOS, CONGELADOS |
| `VEGETABLE` | HORTALICAS, TUBERCULOS |
| `FRUIT` | FRUTAS |
| `BEVERAGE` | BEBIDAS |
| `GRAIN` | GRAOS, TEMPEROS, CONSERVAS_E_ENLATADOS, ALIMENTOS_PREPARADOS |

Categoria desconhecida: **erro**, o ciclo para.

### Armazenamento (`products.storage_place`) — calculado a partir da categoria de origem

| Destino | Origem |
|---|---|
| `FREEZER` | CONGELADOS |
| `PANTRY` | GRAOS, TEMPEROS, CONSERVAS_E_ENLATADOS, TUBERCULOS |
| `FRIDGE` | todo o resto |

### Unidade (`products.unit_of_measure`)

| Destino | Origem |
|---|---|
| `KILOGRAM` | kg |
| `LITER` | L |
| `UNIT` | un, cento |
| `DOZEN` | dz |
| `PACKAGE` | cx, pct, lata, saco, bd, maço, barril e qualquer valor novo |

## Itens de estoque -> `stock_products`

Origem: `produtosgeladeira` (pessoa) e `produtosfrigorifico` (empresa), no mesmo formato.

| Campo | Vem de |
|---|---|
| `stock_id` | estoque correspondente (`idgeladeira` / `idfrigorificos`) |
| `product_id` | `idprodutos` -> `products.id` |
| `quantity` | `quantidade` |
| `expire_date` | `dtvalidade` |
| `batch` | `lote` (convertido para texto) |
| `category` | copiada de `products.category` |

- **Chave**: `stock_id + product_id + batch`.
- O status do item **não é copiado**: um trigger do destino calcula.

## Receitas -> `recipes`, `recipe_ingredients`

| Destino | Campo | Vem de |
|---|---|---|
| `recipes` | `name` | `receita.nome` |
| | `description` | `receita.descricao` |
| | `instructions` | `receita.modopreparo` |
| `recipe_ingredients` | `recipe_id`, `product_id` | `ingredientes.idreceita`, `idprodutos` |
| | `quantity` | `ingredientes.quantidade` |

- **Chave**: `recipes.name` (receitas com o mesmo nome têm o mesmo conteúdo na origem); `recipe_ingredients(recipe_id, product_id)`.

## Listas de compras -> `shopping_lists`, `shopping_list_products`

| Destino | Campo | Vem de |
|---|---|---|
| `shopping_lists` | `stock_id` | estoque principal do dono (`idusuario` ou `idempresa`) |
| | `date` | `listacompras.dtlista` |
| | `name` | fixo `"Lista de compras"` |
| | `status` | fixo `OPEN` |
| `shopping_list_products` | `list_id`, `product_id` | `produtolista.idlistacompras`, `idprodutos` |
| | `quantity` | `produtolista.quantidade` |
| | `status` | fixo `PENDING` |

- **Chave**: `shopping_lists(stock_id, date, name)`; `shopping_list_products(list_id, product_id)`.
- Dono **sem estoque**: a lista é ignorada (aparece um aviso no log) e seus itens também.

## Compras -> `business_expenses`

| Campo | Vem de |
|---|---|
| `group_id`, `created_by` | grupo e user do dono (`compra.idusuario` ou `idempresa`) |
| `supplier` | `compra.ondecomprou` |
| `description` | `"Compra em " + ondecomprou` |
| `category` | fixo `COMPRAS` |
| `amount` | `compra.valorcompra` |
| `expense_date` | `compra.dtcompra` |

- **Chave**: `group_id + supplier + expense_date + amount`.

## Assinaturas -> `subscriptions`

| Campo | Vem de |
|---|---|
| `user_id` | user do dono (`assinatura.idusuario` ou `idempresa`) |
| `plan_id` | `plans.id` onde `plans.plan_code` = plano traduzido |
| `status` | fixo `ACTIVE` |

| Plano no destino (`plans.plan_code`) | Origem (`assinatura.tipoassinatura`) |
|---|---|
| `FREE` | FREE |
| `PLUS` | PLUS |
| `FAMILY` | FAMILIA |
| `COMMERCIAL` | COMERCIAL |

- **Chave**: o user não ter **nenhuma** assinatura. Se já tem, não cria outra (mesmo de plano diferente).
- Plano desconhecido: **erro**, o ciclo para.
