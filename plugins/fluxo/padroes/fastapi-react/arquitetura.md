---
camada: arquitetura
descricao: Organização do backend em módulos hexagonais, direção das dependências e convenções de Python.
paths:
  - "**/app/core/**"
  - "**/app/modules/**"
  - "**/app/integrations/**"
  - "**/app/api/**"
---

# Arquitetura do backend

FastAPI assíncrono, SQLAlchemy 2.0 async e PostgreSQL, em arquitetura hexagonal
(ports & adapters) por módulo de domínio. Python gerenciado com `uv`.

## Camadas de `app/`

- **`app/core/`**: infraestrutura compartilhada e sem domínio (sessão, repositório
  e UoW base, paginação, segurança, settings, exceções, handlers). **Nunca importa
  de `app/modules`**: a dependência aponta dos módulos para o core.
- **`app/modules/<dominio>/`**: um slice hexagonal por domínio, independente dos
  outros.
- **`app/integrations/<servico>/`**: clients de serviços externos. O módulo
  depende deles por um port; a integração nunca importa o módulo.
- **`app/api/`**: composição. `router.py` é o único ponto que conhece todos os
  módulos; workers e checagens de subida também moram aqui, para que o core não
  precise importar módulos.

## Anatomia de um módulo

```
domain/entities.py      → entidades (dataclasses frozen) e comandos de domínio
application/
  ports/                → Protocols (Repository, UnitOfWork)
  dtos/                 → commands (entrada dos use cases) e filters (paginação)
  use_cases/            → uma classe por operação
adapters/
  http/                 → router, schemas Pydantic, dependencies
  db/                   → models, repository, unit_of_work, factories
```

Um domínio novo replica o módulo mais completo do projeto. Se o projeto tiver a
skill `novo-modulo`, siga-a.

## Fluxo de uma request

Router → monta o `*Command` a partir do schema → instancia o use case com o
`UnitOfWork` injetado → o use case abre `async with uow` e opera por
`uow.<repositorio>` → devolve entidade de domínio → o router serializa no `*Read`.

## Regras

- **Use case** recebe o `uow` no construtor e depende só dos ports. Nunca vê model
  SQLAlchemy, schema Pydantic nem integração concreta.
- **Ports** são `Protocol`s estruturais: os adapters os satisfazem sem herdar.
- **Entidades e comandos** são dataclasses frozen. IDs com `uuid.uuid7()`.
- **Update parcial** usa o sentinel `UNSET` (`app/core/types.py`) para separar
  "campo ausente" de "valor `None`"; `BaseUpdateCommand.defined_values()` devolve
  só o que veio.
- **Erros** são as exceções de `app/core/exceptions.py` (`NotFoundError`,
  `ConflictError`, …). O handler as converte em `{code, message, details}`.
- **Datas de negócio** nunca com `date.today()` ou `datetime.now()` sem fuso: o
  container roda em UTC. Use as funções de data do core no fuso do negócio.
  Carimbo técnico (auditoria, expiração) é `datetime.now(UTC)`.
- **Settings** por pydantic-settings lendo `.env`. Variável nova entra também no
  `.env.example`; segredo e certificado nunca vão para o repositório.
- **Qualidade:** ruff (linha 88, aspas duplas) e mypy `strict` saem limpos.
  `type: ignore` só com o código do erro (`[attr-defined]`) e um comentário na
  mesma linha dizendo por quê.
- **Idioma:** docstrings, comentários e mensagens de erro em português.

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy .
```
