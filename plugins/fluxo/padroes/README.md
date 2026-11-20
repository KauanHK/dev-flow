# Padrões de código por camada

O que os subagentes do `/fluxo:implementar` seguem ao escrever código, separado por
camada para que cada etapa leia só o que toca. Um **perfil** é uma pasta com um
arquivo por camada; o projeto escolhe o seu em `padroes:` no `.claude/fluxo.yml`.

| Perfil | Stack | Origem |
|---|---|---|
| `fastapi-react` | FastAPI + SQLAlchemy async + PostgreSQL, React + TS + Vite + TanStack Query | `brand_open/notas-fiscais` |

## Formato

Cada arquivo tem o mesmo frontmatter de uma regra do Claude Code
(`.claude/rules/*.md`), para que um padrão possa ir para o projeto sem conversão:

```yaml
---
camada: banco                     # igual ao nome do arquivo
descricao: Models, repositórios, Unit of Work e migrações.
paths:                            # os arquivos que esta camada cobre
  - "**/adapters/db/**"
---
```

## Precedência

Do mais geral para o mais específico; onde dois divergem, vale o de baixo.

1. `padroes/<perfil>/<camada>.md`, no plugin.
2. `.claude/rules/<camada>.md` no projeto, com o mesmo nome: **complementa** o
   padrão. Com `substitui: true` no frontmatter, troca o padrão inteiro.
3. `.claude/rules/<outro>.md` sem par no plugin: regra só do projeto, lida quando
   os `paths:` dela cobrem os arquivos da etapa.

`CLAUDE.md` do projeto, specs e visão geral do grupo valem mais que qualquer padrão.

## Acrescentar um perfil ou uma camada

- Perfil novo: uma pasta com os arquivos das camadas, uma linha na tabela acima e
  a detecção dele na skill `iniciar`.
- Camada nova: um arquivo no perfil. O `implementar` e o `revisar` descobrem as
  camadas pelos arquivos da pasta, sem lista fixa.
- Escreva só o que é do perfil, e não de um projeto: regra de negócio, nome de
  módulo e histórico ficam no `CLAUDE.md` ou em `.claude/rules/` do projeto.
