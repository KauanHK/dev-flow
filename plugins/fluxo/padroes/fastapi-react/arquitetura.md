---
camada: arquitetura
descricao: Organização do backend em módulos hexagonais, composição, direção das dependências e convenções de Python.
paths:
  - "**/app/core/**"
  - "**/src/core/**/*.py"
  - "**/app/modules/**"
  - "**/src/modules/**/*.py"
  - "**/app/integrations/**"
  - "**/src/integrations/**/*.py"
  - "**/app/api/**"
  - "**/src/api/**/*.py"
  - "**/app/main.py"
  - "**/src/main.py"
---

# Arquitetura do backend

FastAPI assíncrono, SQLAlchemy 2.0 async e PostgreSQL, em arquitetura hexagonal
(ports & adapters) por módulo de domínio. Python gerenciado com `uv`.

## Camadas de `src/`

O pacote do backend é `src/`. Projeto mais antigo que use `app/` segue as mesmas
regras com o outro nome; os `paths:` cobrem os dois. Os de `src/` pegam só `.py`,
para não casar com `frontend/src/`.

- **`src/core/`**: infraestrutura compartilhada e sem domínio (sessão, repositório
  e UoW base, paginação, segurança, settings, exceções, handlers). **Nunca importa
  de `src/modules`**: a dependência aponta dos módulos para o core.
- **`src/modules/<dominio>/`**: um slice hexagonal por domínio, independente dos
  outros.
- **`src/integrations/<servico>/`**: clients de serviços externos. O módulo
  depende deles por um port; a integração nunca importa o módulo.
- **`src/api/`**: a composição da subida. `router.py` é o único ponto que conhece
  todos os módulos; `background.py` (workers) e `startup_checks.py` (checagens de
  subida) seguem a mesma ideia. Veja "Composição".

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

## Composição

Composição é o código que conhece as peças concretas (módulos, adapters,
integrações) e as liga; o resto recebe pronto o que ela monta. É um papel, não uma
pasta, e acontece em três pontos:

- **Na subida:** `src/api/` monta o router raiz, os workers e as checagens; a
  fábrica da app (`create_app` e o `lifespan`) junta isso ao core, e `src/main.py`
  a chama. Módulo ou worker opcional entra ou não aqui, por settings, em vez de
  uma flag espalhada pelos handlers.
- **Na request:** `adapters/db/factories.py` cria o UoW,
  `adapters/http/dependencies.py` o expõe por `Depends`, e a rota instancia o use
  case com ele.
- **No worker:** o worker é um ponto de entrada, como a rota, e monta o use case
  que roda.

Regras:

- **Só a entrada importa a composição.** Nenhum módulo, integração ou outro
  arquivo do core importa `src/api/`: pelo `router.py`, viriam junto todos os
  módulos. *(recomendação)* A fábrica da app fica em `src/main.py` ou em
  `src/api/`, e não em `src/core/`, porque é ela que importa `src/api/`.
- **O use case recebe pelo construtor tudo o que usa:** o `uow`, a fábrica do UoW
  de outro módulo (`Callable[[], <Modulo>UnitOfWork]`) e o port da integração. A
  escolha da implementação por settings é uma fábrica que a composição chama.
  *(recomendação)* Sem default que monte o concreto (`provider or get_provider()`,
  `factory or make_unit_of_work`): quem passa é a rota, por `Depends` como o
  `uow`, ou o worker. O default leva o adapter para dentro da application, e o
  teste passa a precisar de `patch`, porque `dependency_overrides` só troca o que
  vem por `Depends`.

## Regras

- **Use case** recebe as dependências no construtor e depende só dos ports. Nunca
  vê model SQLAlchemy, schema Pydantic nem integração concreta.
- **Ports** são `Protocol`s estruturais: os adapters os satisfazem sem herdar.
- **Entidades e comandos** são dataclasses frozen. IDs com `uuid.uuid7()`.
- **Update parcial** usa o sentinel `UNSET` (`src/core/types.py`) para separar
  "campo ausente" de "valor `None`"; `BaseUpdateCommand.defined_values()` devolve
  só o que veio.
- **Erros** são as exceções de `src/core/exceptions.py` (`NotFoundError`,
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
