---
camada: testes
descricao: Testes unitários e de integração com pytest, dublês, banco de teste e tipagem.
paths:
  - "**/tests/**"
  - "**/conftest.py"
---

# Testes

pytest com `pytest-asyncio` em `asyncio_mode = "auto"`: teste e fixture async não
levam `@pytest.mark.asyncio`.

```bash
uv run pytest tests/unit                                 # rápido, sem banco
uv run pytest tests/integration                          # precisa de TEST_DATABASE_URL
uv run pytest tests/unit/modules/<dominio>/test_x.py::test_y
```

## O que testar

- **Cada critério de aceite tem um teste que falharia sem a mudança.** Teste que
  passa antes e depois não prova o critério.
- Caso de erro junto do caso feliz: o `404`, o `409`, o `422` e a regra violada.
- Um comportamento por teste, e o nome diz qual (`test_troca_senha_atual_errada`),
  em português ou inglês conforme os vizinhos.
- Teste que falha por defeito real não se conserta mudando o teste.

## Onde

A árvore de `tests/` espelha a de `app/`:

- `tests/unit/...`: domínio, use cases, integrações e core. Sem banco e sem rede.
- `tests/integration/modules/<dominio>/`: a rota de ponta a ponta, por HTTP, no
  Postgres de teste.

## Unitário

- Use case com UoW falso (`Fake<Modulo>UnitOfWork` no `conftest.py` do pacote),
  com os repositórios em `AsyncMock`. Confira o resultado e as chamadas que
  importam para o critério, não cada chamada.
- Integração externa nunca vai à rede: o teste troca o port por um dublê.
  Certificado, chave e arquivo de exemplo são gerados no teste ou ficam em
  `fixtures/`, nunca reais.
- Estado de processo (singletons, caches, limitadores) volta ao zero numa fixture
  `autouse`, para o resultado não depender da ordem.
- Valor padrão de um objeto de teste fica numa fábrica (`make_<coisa>(**overrides)`)
  escrita uma vez, e o teste passa só o que importa para ele.

## Integração

- Postgres real com o schema migrado. A URL vem de `TEST_DATABASE_URL`, sem
  default. Cada teste roda numa transação com savepoint que sofre rollback.
- Pelas fixtures do `conftest.py`: `client` (`httpx.AsyncClient` sobre a app, com
  `make_unit_of_work` sobrescrito) e `auth_headers`.
- Sem `TEST_DATABASE_URL` disponível, diga que os testes de integração não
  rodaram. Nunca os dê como passando.

## Tipagem

Os testes seguem o mesmo mypy `strict` que `app/`: teste e fixture anotados,
inclusive o `-> None`, e o parâmetro de fixture com o tipo que ela devolve. Dublê
que não implementa o contrato inteiro de propósito entra por `cast`, com
comentário, nunca por `type: ignore` genérico.

## Frontend

Sem suíte de testes no frontend, a verificação dele é `npm run lint` e
`npm run build`. Não crie uma suíte por conta própria; se a spec pedir teste de
tela, é teste manual, citado como tal.
