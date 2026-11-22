---
name: implementar
description: Implementa uma spec ou um grupo de specs na máquina do dev — divide em etapas, implementa, revisa e corrige com subagentes, e entrega em branches locais ou em PRs, empilhados ou não, com o card do Jira atualizado.
argument-hint: <caminho da spec ou do grupo | chave do Jira>
disable-model-invocation: true
---

# Implementar specs

Entrada: $ARGUMENTS

Você é o orquestrador: lê as specs, pergunta o que falta, divide o trabalho, chama os
subagentes, confere o resultado e entrega. **Você não escreve o código da
implementação nem da correção:** isso é dos subagentes.

Merge é sempre de uma pessoa: nunca faça merge, nunca dê push em `git.base` nem em
`git.producao`, e nunca dê force push numa branch que já tem PR sem perguntar.

## 1. Pré-condições

- `.claude/fluxo.yml` existe (sem ele, rode a skill `iniciar`).
- `git status --porcelain` está vazio. Se não estiver, pare e pergunte: não misture
  trabalho em andamento com a spec.
- Rode `git fetch origin`.

## 2. Ler as specs

Descubra o que será entregue:

| Entrada | O que entregar |
|---|---|
| arquivo de spec | essa spec |
| pasta de um grupo | as specs do grupo |
| chave do Jira | o arquivo que tem essa chave em `jira:`; se for um `00-VISAO-GERAL.md` (épico), o grupo; senão, a spec |

Para achar o arquivo de uma chave: `grep -rlE '^jira: *<CHAVE>( |$)' <specs.dir>`.

- Os metadados estão no frontmatter YAML: `id`, `tipo`, `depende_de`, `status` e
  `jira`. Spec com `status: rascunho` não vira código: entrada de uma spec só, pare e
  pergunte; num grupo, ela e as que dependem dela ficam de fora, e você avisa.
- Leia a visão geral do grupo **inteira**: decisões, regras que valem para todas as
  specs e versões. Leia cada spec e as do `depende_de`, que podem estar em outro
  grupo (ache pelo `id` em `<specs.dir>`).
- Num grupo, ordene as specs pelo `depende_de` e pelas ondas da visão geral.

Para cada `id` a entregar e cada dependência, procure a branch
(`git branch -a --list '*/<id>-*'`) e o PR dela
(`gh pr list --head <branch> --state all`). Spec com merge feito já foi entregue:
pule. Spec com PR aberto também, com duas ressalvas: se uma dependência dela teve
merge, refaça a base (passo 5) e pare nisso; se a entrada é só essa spec, pergunte se
é para retomar o trabalho.

## 3. Perguntar o que falta

Faça as perguntas juntas, com `AskUserQuestion`, antes de mudar qualquer coisa. Não
pergunte o que a entrada ou a conversa já responderam.

1. **Branch base.** Pergunte só se não souber: `git.base` está vazio, ou a branch
   não existe nem local nem em `origin`.
2. **Entrega.** Branches locais, sem push nem PR, ou PRs.
3. **PRs empilhados.** Só se a entrega for por PRs e alguma spec depender de outra
   ainda sem merge; sem isso, a resposta não mudaria nada.

Com entrega por PRs, `gh auth status` precisa estar ok.

## 4. Escolher a base de cada spec

A base de uma spec depende do estado das dependências e da entrega:

| Situação da dependência | Branches locais | PRs empilhados | PRs sem empilhar |
|---|---|---|---|
| PR com merge feito | ok; segue | ok; segue | ok; segue |
| PR aberto | sobre a branch dela | sobre a branch dela | a spec fica aguardando |
| só branch, sem PR | sobre a branch dela | se está nesta execução, sobre a branch dela; senão, pergunte | se está nesta execução, a spec fica aguardando; senão, pergunte |
| sem branch nem PR, e fora desta execução | pare | pare | pare |

Sem dependência aberta, a base é `git.base`. Com **duas** dependências abertas em
branches diferentes, pergunte: uma branch nasce de uma base só.

**Spec aguardando:** ela e as que dependem dela não são feitas nesta execução. Siga
com as outras e liste as aguardando no relatório, dizendo qual merge cada uma espera
e que basta rodar de novo depois dele.

Mostre ao usuário, antes de começar, as specs na ordem com a base de cada uma e as
que ficaram de fora. Depois, repita os passos 5 a 10 para cada spec, uma de cada vez.
Se você parar por causa de uma spec, chame o usuário e não siga para a próxima sem a
resposta dele.

## 5. Branch

Nome: `<tipo>/<id>-<slug>`, com o `tipo` do frontmatter e o slug do nome do arquivo
(`feat/conta-01-trocar-senha`).

- A branch não existe: `git switch -c <branch> <ref da base>`. A ref é
  `origin/<base>`, ou `<base>` se ela só existir localmente.
- A branch já existe: é trabalho retomado. Entre nela e leia `git log <base>..HEAD`
  e os critérios já marcados antes de continuar. O que já foi feito sai das etapas.

**Dependência que entrou na base.** Se a branch foi empilhada sobre uma dependência
cujo PR já teve merge, ela ainda carrega os commits da dependência, que entraram
na base com outro hash (squash ou rebase). Refaça a base antes de continuar:

1. O último commit da dependência: `gh pr view <PR da dependência> --json
   headRefOid`.
2. `git rebase --onto origin/<git.base> <esse commit> <branch>`. Conflito que não
   for mecânico: pare e mostre ao usuário.
3. Se a branch já tem PR, `gh pr edit <n> --base <git.base>` e
   `git push --force-with-lease`. O hook do fluxo pede confirmação do force push:
   diga ao usuário que é a troca de base.

Card do Jira, se a spec tiver `jira`: mova para `jira.status.em_andamento` (liste as
transições do card e use a que leva a esse status). Sem transição disponível, avise
e siga.

## 6. Dividir em etapas

Leia o código que a spec toca e divida o trabalho em etapas. Cada etapa é um passo
que fica de pé sozinho, com testes passando, e lista:

- o que entrega;
- os arquivos que toca;
- os critérios de aceite que atende;
- os padrões que valem para ela (abaixo).

Spec pequena é uma etapa só; não divida por dividir. Todo critério de aceite precisa
estar em alguma etapa. Mostre as etapas ao usuário e siga, sem esperar aprovação.

**Padrões da etapa.** O subagente lê só os padrões das camadas que a etapa toca,
para não carregar o que não usa. Monte a lista de arquivos assim:

1. Perfil: `padroes` do `fluxo.yml`. Sem a chave, ou `nenhum`, não há camadas do
   plugin; sem a chave, avise uma vez que `/fluxo:iniciar` a acrescenta. As
   camadas são os arquivos de `${CLAUDE_PLUGIN_ROOT}/padroes/<perfil>/`.
2. Camadas da etapa: as que têm um padrão em `paths:` (no frontmatter) que cobre
   algum arquivo da etapa. Etapa que escreve teste inclui `testes`.
3. Para cada camada: o arquivo do plugin e, se existir, `.claude/rules/<camada>.md`
   do projeto. Se a regra do projeto tiver `substitui: true`, fica só ela.
4. As outras regras de `.claude/rules/` cujos `paths:` cobrem algum arquivo da
   etapa (as que não têm `paths:` valem para todas).

Use caminhos absolutos. Mostre as camadas de cada etapa junto com as etapas.

**Spec errada volta para a spec.** Se o código contradiz o que a spec afirma (o
arquivo não existe, a função faz outra coisa, o desenho não fecha), pare. Descreva
a divergência e proponha a correção da spec ao usuário. Não improvise um desenho
novo dentro da branch.

## 7. Implementar

Para cada etapa, na ordem, chame um subagente `fluxo:implementador` com a ferramenta
`Agent` e espere terminar antes de chamar o próximo: os subagentes dividem o mesmo
checkout, então nunca rode dois ao mesmo tempo.

**Modelo e esforço.** Os padrões estão na definição de cada agente:

| Papel | Agente | Padrão | Chave no `fluxo.yml` |
|---|---|---|---|
| implementar | `fluxo:implementador` | sonnet, high | `agentes.implementar` |
| revisar | `fluxo:revisor` | sonnet, high | `agentes.revisar` |
| corrigir | `fluxo:corretor` | sonnet, medium | `agentes.corrigir` |

Se a chave do papel tiver `modelo` ou `esforco`, passe o valor nos parâmetros `model`
e `effort` do `Agent`. Sem a chave, não passe esses parâmetros.

**O prompt do implementador** traz, porque ele começa sem contexto:

- o caminho da spec e da visão geral, e os das specs do `depende_de`;
- a etapa: o que entrega, arquivos e critérios;
- os padrões da etapa (passo 6), dizendo quais são do plugin e quais do projeto;
- o que as etapas anteriores já fizeram;
- a branch em que ele está;
- o comando para testar a etapa, se a verificação do projeto indicar um;
- se esta spec pode mexer no changelog: só se a seção de versões da visão geral
  disser que ela sai sozinha numa versão. PR de spec não abre versão.

Depois de cada etapa, confira: `git status --porcelain` vazio, commits novos em
`git log`, e a etapa entregue. Se o subagente relatar que a spec diverge do código,
pare como no passo 6. Se ele travar em outra coisa, chame o usuário em vez de
insistir.

## 8. Verificar

Rode você mesmo o roteiro de `verificacao` da config: se for um caminho, leia o
arquivo e siga; se for uma lista, rode os comandos. O relatório do subagente não
substitui a verificação. Se algo falhar, chame um `fluxo:corretor` com a saída da
falha e rode de novo. Tudo verde antes de seguir.

O que não deu para verificar (teste de integração sem banco, teste manual de tela)
vira nota explícita no PR ou no relatório. Nunca marque como feito o que não foi
verificado.

Marque `[x]` na spec só os critérios verificados. Commit:
`docs(<id>): marca critérios de aceite`.

## 9. Revisar e corrigir

**Revisar.** Chame um subagente `fluxo:revisor` com a ferramenta `Agent` e este
prompt: `Leia ${CLAUDE_PLUGIN_ROOT}/skills/revisar/SKILL.md e siga. Os padrões do
plugin estão em ${CLAUDE_PLUGIN_ROOT}/padroes. Entrada: <branch> --base <base>`. Ele
monta sozinho os padrões a partir do diff. Ele não viu a implementação, só lê e devolve um relatório com
veredito. Não passe a ele o que os outros subagentes relataram.

**Decidir.** Leia o relatório e confira os achados no código:

- Veredito "volta para a spec": pare, como no passo 6.
- Achado `bloqueia` ou `ajuste` com que você concorda: vai para a correção.
- Achado de que você discorda: não mexa; explique em "Notas da revisão" no PR ou no
  relatório.
- Sem nada para corrigir: siga para a entrega.

**Corrigir.** Chame um subagente `fluxo:corretor` com o caminho da spec, a branch,
os achados escolhidos, com `arquivo:linha` e o que fazer, e os padrões das camadas
dos arquivos dos achados, montados como no passo 6. A falha da verificação no
passo 8 leva os padrões dos arquivos que falharam. Depois, verifique de novo
como no passo 8, ajuste as marcações de critério que mudaram e volte a "Revisar".

**Limite: 2 ciclos de correção.** Se depois da segunda correção a revisão ainda
trouxer `bloqueia` com que você concorda, pare e chame o usuário com o relatório e o
que já foi tentado. Se sobrar só `ajuste`, siga e registre em "Notas da revisão".

## 10. Entregar

### Branches locais

Sem push, sem PR e sem transição para `em_revisao`. A branch fica pronta para a
próxima spec empilhar sobre ela. Guarde para o relatório as notas que iriam no PR.

### PRs

`git push -u origin <branch>` e `gh pr create --base <base>`. Se a branch já tem PR,
não crie outro: atualize o corpo com `gh pr edit`. O título é
`<tipo>(<id>): <título da spec>` e o corpo é assim, em português:

```markdown
Implementa a [spec NN de <grupo> — <título>](<link da spec na branch>). <Uma ou duas
frases do problema e do que muda para quem usa.> <Versão: "não abre versão; a
entrada do changelog vai num PR próprio, pelo `/fluxo:entregar`", ou "sai sozinha
na vX.Y.Z".>

<Se empilhado: "Empilhado sobre #N (spec MM): revisar e fazer merge depois dele.">

### O que muda

**<Lado ou peça>.** <Prosa: o que mudou e por quê, citando classes, rotas e
arquivos.>

### Critérios de aceite

- [x] <critério da spec> (<a evidência: qual teste, ou "conferido no código; falta
  o teste manual">)
- [ ] <critério não atendido> (<por quê>)

### Notas da revisão

<Só se sobrou achado do /fluxo:revisar sem correção: o achado e por que ficou.
Remova a seção se não houver.>

Jira: <CHAVE>
```

Se a spec tiver `jira`, no card: link remoto para o PR
(`createJiraIssueRemoteIssueLink`), comentário curto com o PR e o que ficou pendente,
e transição para `jira.status.em_revisao` se estiver configurado. Operações fora da
lista de ferramentas vêm do `discover` do Atlassian MCP.

## 11. Relatório

Quando todas as specs terminarem, diga ao usuário:

- o que foi entregue: cada branch ou PR, com a base;
- com PRs empilhados, a ordem de merge, de baixo para cima, e que cada PR filho tem
  que ser redirecionado para `git.base` depois do merge do pai: o
  `/fluxo:entregar` faz isso para todas as pilhas, e rodar de novo o
  `/fluxo:implementar` na spec também;
- que, depois dos merges, o `/fluxo:entregar` escreve o changelog, abre o PR de
  release e conclui os cards que chegarem à produção;
- as specs aguardando ou de fora, e o que cada uma espera;
- as pendências e as notas da revisão;
- onde o projeto segue outro jeito que o padrão do plugin sem regra que o
  registre, com a regra de `.claude/rules/` que você sugere;
- o que precisa mudar nas specs, se houver.
