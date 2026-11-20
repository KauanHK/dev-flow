---
camada: api
descricao: Routers FastAPI, schemas Pydantic, injeção de dependências, autenticação e erros HTTP.
paths:
  - "**/adapters/http/**"
  - "**/app/api/**"
  - "**/app/core/handlers.py"
  - "**/app/core/security/**"
---

# API REST

## Router

- Um router por módulo em `adapters/http/router.py`, registrado em
  `app/api/router.py` com prefixo e tags.
- **Router fino:** schema → `*Command` → use case com o `uow` → entidade → `*Read`.
  Regra de negócio não mora no router.
- Autenticado por padrão: `APIRouter(dependencies=[Depends(get_current_actor)])`.
  Rota pública é exceção explícita, com o motivo na docstring.
- `status_code` explícito quando não é 200: `201` na criação, `204` sem corpo.
- Docstring da rota em português: é ela que aparece no Swagger.
- Lista paginada com as dependências e o `PaginatedResponse` do core, nunca com
  `limit`/`offset` soltos.

## Schemas

- Em `adapters/http/schemas.py`: `<Nome>Create`, `<Nome>Update` e `<Nome>Read`.
- Update parcial: `model_dump(exclude_unset=True)` vira o comando com `UNSET`.
  Campo ausente não é o mesmo que `null`.
- Validação de formato (máscara, tamanho, enum) no schema, com mensagem em
  português. Regra que depende de estado (duplicidade, transição) no use case.
- O `*Read` nunca expõe dado sensível; ele sai da entidade, que já não o tem.

## Dependências

- Aliases `Annotated` em `adapters/http/dependencies.py`
  (`ClientesUnitOfWorkDep`, `ActorDep`), usados nas assinaturas das rotas.

## Erros

- Levante as exceções do core; o handler responde `{code, message, details}` com o
  status certo. Não use `HTTPException` para erro de negócio.
- **`401` é só sessão inválida.** O frontend trata `401` como sessão expirada e
  desloga. Senha atual errada, regra violada ou estado que não permite a operação
  respondem `422` ou `409`.
- `code` é estável e em `snake_case` (`emitter_not_configured`): o frontend decide
  por ele, não pelo texto.

## Contrato com o frontend

Mudou o contrato de uma rota (campo, status, código de erro), atualize os tipos em
`frontend/src/features/<dominio>/types.ts` na mesma spec, se ela cobre o
frontend. Se não cobre, cite a mudança no relato.
