---
camada: banco
descricao: Models SQLAlchemy, repositórios, Unit of Work e migrações Alembic.
paths:
  - "**/adapters/db/**"
  - "**/app/core/db/**"
  - "**/migrations/**"
  - "**/alembic.ini"
---

# Banco de dados

SQLAlchemy 2.0 async sobre PostgreSQL, migrações com Alembic.

## Models

- Ficam em `adapters/db/models.py` do módulo, no estilo dos models que já existem.
- Chave primária UUID gerada com `uuid.uuid7()`.
- `created_at` e `updated_at` com `DateTime(timezone=True)` e
  `server_default=now()`. Toda data e hora no banco tem fuso.
- Tamanho de `String` pelo dado real (o leiaute do documento, a regra do campo),
  não um número redondo.

## Repositório

- Herda `BaseRepository[ModelT, EntityT, FiltersT]` do core e define `model`,
  `filters_type`, `_to_entity` e, quando há filtros, `_apply_filters`.
- **Converte model em entidade na fronteira.** Nenhum método devolve model; use
  case não vê SQLAlchemy.
- Par de leitura: `get_x_or_none` devolve `None`; `get_x` lança `NotFoundError`
  com uma mensagem em português que diga o que não foi achado.
- Dado que nunca pode chegar a uma resposta (hash de senha, segredo) fica fora da
  entidade, num método próprio.
- Consultas com `sa.select(...)`. Lista que carrega relação busca junto; não faça
  uma consulta por linha.

## Unit of Work

- `BaseUnitOfWork` do core: cria a sessão ao entrar, faz commit ao sair e rollback
  em exceção. A transação é o bloco `async with uow`; o use case não abre sessão.
- O UoW do módulo expõe os repositórios como propriedades (`uow.clientes`).
- `factories.make_unit_of_work` é o que o router injeta e o que os testes
  sobrescrevem com `app.dependency_overrides`.
- Escrita que precisa ser atômica com outra (o registro e o documento que o
  acompanha) acontece na mesma transação, não em duas.

## Migrações

```bash
uv run alembic revision --autogenerate -m "<o que muda, em português>"
uv run alembic upgrade head
uv run alembic downgrade -1 && uv run alembic upgrade head   # ida e volta
```

- **Revise o script gerado.** O autogenerate erra enum, `server_default`, índice
  e renomeação (que ele vê como drop + add). Apague os comentários de "please
  adjust" depois de revisar.
- Escreva `downgrade()` de verdade, que volta ao estado anterior.
- Coluna nova `NOT NULL` em tabela com dados: crie com default ou preencha na
  própria migração antes de apertar a restrição.
- **Uma cabeça só.** Antes de commitar, `uv run alembic heads` mostra uma
  revisão. Com specs empilhadas, a migração da spec de cima aponta para a da spec
  de baixo; se a base andou, ajuste o `down_revision` em vez de criar merge.
- Nunca edite migração que já entrou na base ou na produção: crie outra.
