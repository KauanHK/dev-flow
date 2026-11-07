---
name: iniciar
description: Configura o plugin fluxo num repositório. Descobre a branch base, a pasta de specs, o roteiro de verificação e o projeto do Jira, e grava `.claude/fluxo.yml`. Use quando o usuário pedir para iniciar, configurar ou preparar o fluxo num projeto, ou quando outra skill do fluxo não encontrar `.claude/fluxo.yml`.
---

# Iniciar o fluxo num repositório

O plugin é global; o que muda de um projeto para outro fica em `.claude/fluxo.yml`,
na raiz do repositório. Esta skill escreve esse arquivo a partir do modelo
`fluxo.yml` desta pasta. Os comentários do modelo explicam cada chave.

Se `.claude/fluxo.yml` já existir, mostre o conteúdo e pergunte o que mudar em vez
de reescrever.

## 1. Repositório

- `git remote get-url origin` precisa apontar para o GitHub, e `gh auth status`
  precisa estar ok. Sem isso o `/fluxo:implementar` não abre PR: avise e siga.
- **Base:** se existir `dev` (local ou em `origin`), `git.base = dev` e
  `git.producao = main`. Senão, as duas são a branch padrão
  (`gh repo view --json defaultBranchRef`).
- **Specs:** procure `*/00-VISAO-GERAL.md` abaixo de `docs/`. A pasta que contém os
  grupos é `specs.dir`. Sem nenhum, use `docs`.
- **Verificação:** se existir `.claude/skills/verify/SKILL.md`, use o caminho dele.
  Senão, monte a lista de comandos de lint, type-check, testes e build a partir do
  `CLAUDE.md` e dos manifestos (`package.json`, `pyproject.toml`, `Makefile`).
  Confirme a lista com o usuário.
- **Changelog:** `CHANGELOG.md` na raiz, se existir e o `CLAUDE.md` descrever a
  regra de versão. Senão, deixe vazio.
- **Agentes:** não pergunte. Mantenha a seção `agentes` comentada, com os padrões do
  modelo, a menos que o usuário peça outro modelo ou esforço.

## 2. Jira

Use as ferramentas do Atlassian MCP. Se uma operação citada aqui não estiver na
lista de ferramentas, ache o nome exato com `discover`; nunca invente um.

1. `getAccessibleAtlassianResources`: o site vai para `jira.site`.
2. Liste os projetos visíveis e pergunte qual é o deste repositório
   (`AskUserQuestion`). A chave vai para `jira.projeto`.
3. Cliente (`listJiraProjectComponents`): o projeto costuma ser compartilhado
   entre clientes, e o componente diz de quem é o card. Pergunte qual componente
   é o cliente deste repositório. O nome exato vai para `jira.cliente`: ele é o
   componente de todo épico e card, e o prefixo do título (`<cliente> - <título>`).
4. Tipos de issue do projeto (`listJiraProjectIssueTypesMetadata` ou
   `getJiraProjectIssueTypesMetadata`): escolha o tipo de épico e o de card. Em
   projeto em português eles costumam ser `Epic` e `Tarefa`. Pergunte se houver
   mais de um candidato a card (`Task`, `Story`, `História`).
5. Link de dependência (`listJiraIssueLinkTypes`): o tipo cujo sentido é
   "bloqueia". Quase sempre é `Blocks`.
6. Estimativa: se o tipo de card tiver o campo `timetracking`, use
   `timetracking`. Senão, se tiver Story Points, `story_points`. Senão,
   `nenhuma`.
7. Statuses (`listJiraStatuses`): o status de "em andamento" e o de "em
   revisão". O de revisão nem sempre tem esse nome (no DES é
   `Implantação/Testes`): mostre ao usuário os outros statuses da categoria "em
   andamento" e pergunte qual recebe o card quando o PR abre. Se nenhum servir,
   deixe `status.em_revisao` vazio.
8. Quadro (`listJiraBoards`): se o projeto tiver um board scrum, grave o id em
   `jira.quadro`. Sem board scrum, deixe vazio, e o fluxo não mexe em sprint.

## 3. Gravar

Escreva `.claude/fluxo.yml` com os valores descobertos, mantendo os comentários do
modelo. Mostre o arquivo final. Lembre que ele vai para o git: é configuração do
projeto e não tem segredo.
