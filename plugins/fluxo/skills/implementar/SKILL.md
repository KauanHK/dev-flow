---
name: implementar
description: Implementa uma spec de ponta a ponta na máquina do dev — branch na base certa, código com testes, verificação, commits, critérios marcados, PR empilhado quando há dependência aberta e card do Jira atualizado.
argument-hint: <caminho da spec | chave do Jira>
disable-model-invocation: true
---

# Implementar uma spec

Entrada: $ARGUMENTS

Uma execução implementa **uma** spec e termina num PR aberto. Merge é sempre de uma
pessoa: nunca faça merge, nunca dê push em `git.base` nem em `git.producao`, e
nunca dê force push numa branch que já tem PR sem perguntar.

## 1. Pré-condições

- `.claude/fluxo.yml` existe (sem ele, rode a skill `iniciar`).
- `git status --porcelain` está vazio. Se não estiver, pare e pergunte: não misture
  trabalho em andamento com a spec.
- `gh auth status` está ok. Rode `git fetch origin`.

## 2. Ler a spec

- Se a entrada for uma chave do Jira, ache a spec com
  `grep -rlE '^jira: *<CHAVE>( |$)' <specs.dir>`.
- Os metadados estão no frontmatter YAML: `id`, `tipo`, `depende_de`, `status` e
  `jira`. Com `status: rascunho`, pare e pergunte: spec não aprovada não vira código.
- Leia a visão geral do grupo **inteira**: decisões, regras que valem para todas as
  specs e versões. Leia a spec e as specs do `depende_de`, que podem estar em outro
  grupo (ache pelo `id` em `<specs.dir>`).

## 3. Escolher a base

Para cada `id` do `depende_de`, procure a branch (`git branch -a --list '*/<id>-*'`)
e o PR dela (`gh pr list --head <branch> --state all`).

| Situação da dependência | O que fazer |
|---|---|
| PR com merge feito | ok; segue |
| PR aberto | a base passa a ser a branch dela (stack) |
| sem branch nem PR | pare: a dependência não foi feita |

Sem dependência aberta, a base é `git.base`. Com **duas** dependências abertas em
branches diferentes, pare e pergunte: um PR tem uma base só.

## 4. Branch

Nome: `<tipo>/<id>-<slug>`, com o `tipo` do frontmatter e o slug do nome do arquivo
(`feat/conta-01-trocar-senha`).

- A branch não existe: `git switch -c <branch> origin/<base>`.
- A branch já existe: é trabalho retomado. Entre nela e leia `git log <base>..HEAD`
  e os critérios já marcados antes de continuar.

Card do Jira: mova para `jira.status.em_andamento` (liste as transições do card e
use a que leva a esse status). Sem transição disponível, avise e siga.

## 5. Plano

Antes de escrever código, liste os arquivos que vai tocar, cada um ligado aos
critérios de aceite que ele atende.

**Spec errada volta para a spec.** Se o código contradiz o que a spec afirma (o
arquivo não existe, a função faz outra coisa, o desenho não fecha), pare. Descreva
a divergência e proponha a correção da spec ao usuário. Não improvise um desenho
novo dentro do PR.

## 6. Implementar

- Siga o `CLAUDE.md` do projeto e as skills do projeto que se aplicam (em
  `.claude/skills/`). Na dúvida sobre um padrão, leia um arquivo equivalente que já
  existe.
- Testes junto com o código, um critério de aceite por vez.
- Commits pequenos, um passo lógico cada. Siga o padrão do repositório
  (`git log -20 --format=%s`), que normalmente é `<tipo>(<id>): <o que muda>`
  em português, com corpo explicando o porquê quando ele não for óbvio.
- Só mexa no changelog (`changelog` da config) se a seção de versões da visão geral
  disser que esta spec sai sozinha numa versão. PR de spec não abre versão.

## 7. Verificar

Rode o roteiro de `verificacao` da config: se for um caminho, leia o arquivo e siga;
se for uma lista, rode os comandos. Tudo verde antes do PR.

O que não deu para verificar (teste de integração sem banco, teste manual de tela)
vira nota explícita no PR. Nunca marque como feito o que não foi verificado.

## 8. Critérios e revisão própria

- Marque `[x]` na spec só os critérios verificados. Commit:
  `docs(<id>): marca critérios de aceite`.
- Releia `git diff <base>...HEAD` contra a spec. Todo o Desenho foi feito? Entrou
  algo que está em "Fora de escopo"? Corrija antes de abrir o PR.

## 9. PR

`git push -u origin <branch>` e `gh pr create --base <base>`, com título
`<tipo>(<id>): <título da spec>` e o corpo assim, em português:

```markdown
Implementa a [spec NN de <grupo> — <título>](<link da spec na branch>). <Uma ou duas
frases do problema e do que muda para quem usa.> <Versão: "não abre versão; a
entrada do changelog vai num PR próprio quando o grupo fechar", ou "sai sozinha na
vX.Y.Z".>

<Se empilhado: "Empilhado sobre #N (spec MM): revisar e fazer merge depois dele.">

### O que muda

**<Lado ou peça>.** <Prosa: o que mudou e por quê, citando classes, rotas e
arquivos.>

### Critérios de aceite

- [x] <critério da spec> (<a evidência: qual teste, ou "conferido no código; falta
  o teste manual">)
- [ ] <critério não atendido> (<por quê>)

Jira: <CHAVE>
```

## 10. Jira e relatório

- Card: link remoto para o PR (`createJiraIssueRemoteIssueLink`), comentário curto
  com o PR e o que ficou pendente, e transição para `jira.status.em_revisao` se
  estiver configurado. Operações fora da lista de ferramentas vêm do `discover` do
  Atlassian MCP.
- Para o usuário: o link do PR, a base, as pendências e, se houver, o que precisa
  mudar na spec.
