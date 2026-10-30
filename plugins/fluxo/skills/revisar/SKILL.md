---
name: revisar
description: Revisa a implementação de uma spec contra a própria spec, num agente separado que só lê — critérios de aceite com evidência, desenho, escopo, regras do grupo, commits e corpo do PR — e devolve um relatório com veredito. Use antes da revisão humana de um PR do fluxo, ou quando o usuário pedir para revisar um PR ou uma branch contra a spec.
argument-hint: "[número do PR | branch | spec | chave do Jira] [--comentar]"
context: fork
agent: fluxo:revisor
background: false
allowed-tools:
  - Bash(git fetch *)
  - Bash(git diff *)
  - Bash(git log *)
  - Bash(git show *)
  - Bash(git branch *)
  - Bash(git rev-parse *)
  - Bash(gh pr view *)
  - Bash(gh pr diff *)
  - Bash(gh pr list *)
---

# Revisar uma spec implementada

Entrada: $ARGUMENTS

O resultado é um relatório para quem vai revisar o PR. Você não corrige nada: quem
corrige é a sessão que implementou, com o relatório na mão.

## 1. Achar o alvo

Leia `.claude/fluxo.yml` na raiz do repositório (`git.base`, `specs.dir`,
`changelog`). Sem ele, pare e diga que o repositório não está no fluxo.

Descubra a branch, o PR e a spec a partir da entrada:

| Entrada | Como achar |
|---|---|
| vazia | a branch atual |
| número | `gh pr view <n> --json number,title,body,url,state,baseRefName,headRefName` |
| branch | a branch; o PR dela, se houver, por `gh pr list --head <branch> --state all` |
| caminho de spec | o `id` do frontmatter; a branch por `git branch -a --list '*/<id>-*'` |
| chave do Jira | a spec com essa chave em `jira:`; daí, como um caminho de spec |

A branch de uma spec se chama `<tipo>/<id>-<slug>`. Do nome da branch sai o `id`, e
a spec é o arquivo com esse `id` no frontmatter. Para achar a spec por um campo do
frontmatter: `grep -rlE '^id: *<id>( |$)' <specs.dir>`, ou `'^jira: *<CHAVE>( |$)'`
para a chave do Jira. Branch fora desse padrão ou sem spec: pare e diga o que
faltou.

**Base do diff.** Com PR, a base dele. Sem PR, a branch de uma dependência ainda
aberta (como o `/fluxo:implementar` escolhe) ou `git.base`. Rode `git fetch origin`
e leia `git diff origin/<base>...<branch>` e `git log origin/<base>..<branch>`.
Use a ref remota da branch quando ela não existir localmente.

## 2. Ler a spec

- A visão geral do grupo **inteira**: decisões (pelos IDs), regras que valem para
  todas as specs, ondas e versões.
- A spec: Desenho, Fora de escopo e Critérios de aceite.
- As specs do `depende_de`, só o que elas entregam e esta usa.
- O `CLAUDE.md` do projeto, pelas convenções.

## 3. Conferir

Leia o diff inteiro e, quando precisar de contexto, o arquivo em volta. Confira:

1. **Critérios de aceite.** Um por um: atendido, parcial, não atendido ou não
   verificável. A evidência é o código que implementa (`arquivo:linha`) e o teste
   que prova (nome do teste). Teste que existe mas não verifica o comportamento do
   critério conta como sem teste. Critério marcado `[x]` na spec ou no PR sem
   evidência é achado.
2. **Desenho.** Cada decisão da spec foi seguida? Divergência vira achado, dizendo
   se o código deve voltar ao Desenho ou se a spec deve ser atualizada.
3. **Escopo.** Algo no diff que a spec não pede ou que está em "Fora de escopo":
   refactor de passagem, arquivo sem relação, mudança de formatação em massa.
4. **Regras do grupo e do projeto.** As regras da visão geral, as decisões citadas
   e o `CLAUDE.md`.
5. **Defeitos evidentes.** Só os que você consegue mostrar no diff: condição
   invertida, erro não tratado num caminho que o critério cobre, rota sem a
   autorização que as vizinhas têm. Não é uma caça a bugs; para isso existe o
   `/code-review`.
6. **Commits e versão.** Mensagens no padrão do repositório
   (`<tipo>(<id>): …`), o último marcando os critérios. O changelog só muda se a
   seção de versões da visão geral disser que esta spec sai sozinha.
7. **PR**, se houver. Base certa (empilhado sobre a dependência aberta, ou
   `git.base`; nunca a produção, a menos que `git.base` seja a própria produção),
   link para a spec, critérios com evidência e a linha `Jira: <CHAVE>` quando a
   spec tiver card. O que o PR afirma e o código não confirma é achado.

Não rode o roteiro de verificação inteiro: isso é do `/fluxo:implementar` e do CI.
Rode um teste específico só quando a dúvida sobre um critério depender disso.

## 4. Relatório

Devolva só o relatório, neste formato:

```markdown
## Revisão de <id> — <título da spec>

<PR #N (<head> → <base>) ou "Branch <branch> sem PR (diff contra <base>)">

**Veredito:** <pronto para revisão humana | ajustes antes da revisão humana |
volta para a spec> — <uma frase com o porquê>

### Critérios de aceite

| # | Critério | Situação | Evidência |
|---|---|---|---|
| 1 | <resumo do critério> | atendido | `api/conta.py:42`; `test_troca_senha_errada` |

### Achados

1. **[bloqueia]** `<arquivo:linha>` — <o problema e o que acontece por causa
   dele>. <O que fazer.>
2. **[ajuste]** …
3. **[nota]** …

### Spec

<Divergências que pedem mudança na spec, com a mudança proposta. Remova a seção se
não houver.>
```

- **bloqueia:** critério não atendido, defeito, regra quebrada ou mudança fora do
  escopo com risco. Qualquer um destes leva o veredito a "ajustes antes da
  revisão humana".
- **ajuste:** vale corrigir, mas não impede a revisão humana.
- **nota:** informação para quem revisa, sem ação.
- O veredito é "volta para a spec" quando o problema está na spec, não no código.

Sem achados, diga isso numa linha em vez de deixar a seção vazia.

## 5. Comentar no PR (só com `--comentar`)

Se a entrada tiver `--comentar` e houver PR, publique o relatório como comentário:
`gh pr comment <n> --body-file -`, com o relatório no stdin por heredoc e a
primeira linha
`Revisão automática do fluxo (/fluxo:revisar), antes da revisão humana.` Nunca
use `gh pr review`: aprovar ou pedir mudanças é decisão de quem revisa. Sem
`--comentar`, não publique nada.
