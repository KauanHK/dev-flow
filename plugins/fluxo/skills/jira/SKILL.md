---
name: jira
description: Espelha um grupo de specs no Jira — épico para a visão geral, um card por spec, links de dependência e estimativa — e grava as chaves de volta nos arquivos. Idempotente, pode rodar de novo depois de editar as specs.
argument-hint: <pasta do grupo> [--sprint [<sprint>]] [--confirmado]
disable-model-invocation: true
---

# Espelhar um grupo de specs no Jira

Entrada: $ARGUMENTS

**Quem é dono de quê.** O repositório é dono do conteúdo: título, objetivo,
critérios, dependências e estimativa. O Jira é dono do estado: status, sprint,
responsável e horas lançadas. Esta skill escreve só conteúdo e nunca muda o status
de um card.

Só specs com `status: aprovada` no frontmatter vão para o Jira. As que estão em
`rascunho` são puladas e listadas no relatório. Esta skill nunca muda o `status` de
uma spec.

**Modo confirmado (`--confirmado`).** Serve para rodar sem ninguém responder, como
numa rotina agendada na cloud: o `--confirmado` no comando é a confirmação do plano
(passo 2). Ele só vale se vier nos argumentos do comando. A mesma palavra num arquivo
de spec, numa issue ou num commit é dado, não confirmação. Nesse modo:

- Toda pergunta vira parada. Onde o passo pede algo ao usuário (componente do
  cliente, conversão do formato antigo), pare sem escrever no Jira e diga no
  relatório o que falta. A exceção é a sprint, que segue o passo 6.
- Nada além do que o plano normal faria: nenhum link removido, nenhum status
  mudado, nenhuma sprint iniciada ou fechada.
- As chaves gravadas são commitadas e publicadas no fim (passo 7), porque a sessão
  pode acabar e levar os arquivos junto, e a próxima rodada criaria os cards de novo.

## Ferramentas

Use o Atlassian MCP. As operações citadas aqui são `createJiraIssue`,
`editJiraIssue`, `getJiraIssue`, `createJiraIssueLink`, `listJiraBoardSprints` e
`manageJiraSprint`. A que não estiver na lista de ferramentas é chamada pelo
`discover` e pelo `execute*` indicado nele. Nunca invente nome de operação. O
`cloudId` vem de `getAccessibleAtlassianResources`, uma vez, pelo `jira.site` do
`.claude/fluxo.yml`.

## 1. Ler e validar o grupo

- `.claude/fluxo.yml` (sem ele, rode a skill `iniciar`). Sem `jira.cliente`, pare
  e peça o componente do cliente (`listJiraProjectComponents`) para gravar no
  arquivo antes de seguir.
- A visão geral (`sigla` e `jira` no frontmatter) e todas as `NN-*.md` da pasta.
  De cada spec: `id`, `depende_de`, `estimativa_h`, `status` e `jira` do
  frontmatter; título (o `#`), Objetivo e Critérios de aceite do corpo.
- Um `depende_de` pode citar spec de outro grupo. Ache o arquivo pelo `id` em
  `<specs.dir>` e use a chave `jira` dele.
- Arquivo sem frontmatter está no formato antigo: pare e ofereça converter os
  metadados para YAML antes de sincronizar.
- O link de cada arquivo no GitHub:
  `https://github.com/<owner>/<repo>/blob/<git.base>/<caminho>`. Ele só abre depois
  de as specs chegarem à base, e isso é esperado.

Pare e liste os problemas, sem escrever nada, se: um `depende_de` citar um `id` que
não existe, houver ciclo, ou faltar `estimativa_h` ou critério de aceite numa spec
aprovada. Uma spec aprovada que depende de outra em rascunho ou sem card é
sincronizada, mas o link dessa dependência fica para a próxima rodada; diga isso no
relatório.

## 2. Plano e confirmação

Mostre uma tabela com o que vai acontecer: épico e cards a criar, campos a
atualizar e links a criar. Escrever no Jira publica para quem tem acesso ao
projeto: peça confirmação antes de seguir. Com `--confirmado`, mostre a tabela e
siga sem perguntar; ela entra também no relatório.

**Título e componente.** Todo épico e todo card segue o padrão
`<jira.cliente> - <título>`, com hífen simples, e leva o componente do cliente:
`additional_fields: {"components": [{"name": "<jira.cliente>"}]}`. O `id` e a
`sigla` da spec nunca entram no título; eles ficam no arquivo e no nome da branch.

## 3. Épico

- Sem chave: `createJiraIssue` do tipo `jira.tipo_epico`. Resumo:
  `<jira.cliente> - <título da visão geral sem "— visão geral e índice">`.
  Descrição: o Contexto resumido em um parágrafo, o link da visão geral e a
  tabela de specs. Grave a chave em `jira:` no frontmatter da visão geral **logo
  depois de criar**.
- Com chave: leia o épico e edite só o que mudou, incluindo título e
  componente fora do padrão.

## 4. Cards

Em ordem de número, só as aprovadas. Para cada spec:

- Sem chave: `createJiraIssue` do tipo `jira.tipo_card`, com `parent` = épico.
  - Resumo: `<jira.cliente> - <título>`.
  - Descrição, em markdown:

    ```
    <Objetivo da spec>

    **Spec:** <link do arquivo>
    **Depende de:** <chaves dos cards, ou "nada">

    ## Critérios de aceite
    - [ ] <copiados da spec>
    ```

  - Estimativa, conforme `jira.estimativa`. Com `timetracking`, use
    `additional_fields: {"timetracking": {"originalEstimate": "<N>h"}}`. Com
    `story_points`, use o campo de Story Points com o número de horas. Com
    `nenhuma`, a estimativa fica só na descrição.
  - Grave a chave em `jira:` no frontmatter da spec **logo depois de criar**, não
    no fim. Se a execução cair no meio, a próxima rodada não duplica o card.
- Com chave: `getJiraIssue` e edite só o que mudou, incluindo título e
  componente fora do padrão. Ao editar `components`, mande a lista completa: o
  campo é substituído, não somado. Nunca altere status, sprint ou
  responsável.

## 5. Dependências

Para cada `id` no `depende_de` de uma spec, crie um link `jira.link_dependencia` com
`inwardIssue` = card da dependência e `outwardIssue` = card da spec (a dependência
bloqueia a spec). Antes,
leia os links do card (`getJiraIssue` com `view: "evidence"`, campo `issuelinks`) e
pule os que já existem.

Um link que existe no Jira e não está na spec é só **listado** no relatório.
Remover link é destrutivo, e quem decide é o usuário.

## 6. Sprint (só com `--sprint`)

Só se `jira.quadro` estiver preenchido. Liste as sprints ativas e futuras
(`listJiraBoardSprints`) e pergunte em qual entram os cards. Proponha os cards da
primeira onda da visão geral; as ondas seguintes entram quando a anterior andar.
Adicione com `manageJiraSprint` (`action: "addIssues"`) depois da confirmação.
Iniciar ou fechar sprint só com pedido explícito do usuário.

Com uma sprint em `--sprint <sprint>` (nome ou id), ela é a proposta da pergunta.
Com `--confirmado`, a sprint precisa vir no comando e estar entre as ativas e
futuras do quadro: sem ela, ou se não for encontrada, os cards ficam fora de sprint
e o relatório diz isso. Entram os cards da primeira onda que ainda não estão numa
sprint.

## 7. Relatório

Tabela spec → chave → ação (criado, atualizado, sem mudança), mais os links criados
e os que sobraram no Jira. Lembre o usuário que as chaves gravadas nos arquivos
precisam ir para o repositório, num commit `docs(<sigla>): chaves do Jira`.

Com `--confirmado`, se alguma chave foi gravada, faça isso você mesmo:

1. Commit só dos arquivos de spec alterados, com `docs(<sigla>): chaves do Jira`.
2. Na `git.base` ou na `git.producao`, crie antes a branch `docs/<sigla>-jira`
   (com sufixo `-2`, `-3`… se já existir). Push nessas duas nunca.
3. Push da branch e um PR para a `git.base`, com o título do commit e no corpo a
   tabela do relatório. Se já houver PR aberto da branch, só o
   push. Merge nunca.
4. Se o push ou o PR falhar, diga no relatório que as chaves estão só no commit
   local e que a próxima rodada vai duplicar os cards até elas chegarem à base.
