# fluxo — entrega guiada por specs

Plugin do Claude Code que leva uma demanda da conversa com o cliente ao
faturamento, em qualquer projeto: requisitos, estimativa, specs, Jira, PRs, release
e horas reais. O desenho do processo inteiro está em `fluxo.json` (Excalidraw).
Este repositório é também o marketplace local que instala o plugin.

O processo é global e fica aqui. O que muda de um projeto para outro fica em
`.claude/fluxo.yml`, dentro do próprio projeto. Os padrões (specs em grupos com
visão geral, uma spec por PR, PRs empilhados, commits `<tipo>(<sigla>-NN)`) vêm do
`brand_open/notas-fiscais`. A diferença é que os metadados de cada spec (`id`,
`tipo`, `depende_de`, `estimativa_h`, `status`, `jira`) ficam num frontmatter YAML.

Uma spec nasce com `status: rascunho`. Quem revisa troca para `status: aprovada`, e
só as aprovadas vão para o Jira e viram código. A que sai do escopo numa change
request fica `status: cancelada`.

Tudo roda na máquina do dev; para rotinas na cloud, veja "Na cloud".

## Instalar

No Claude Code:

```
/plugin marketplace add /home/kauan/Documentos/claude/agent
/plugin install fluxo@kauan-plugins
```

Para testar uma mudança no plugin sem reinstalar, abra uma sessão com
`claude --plugin-dir /home/kauan/Documentos/claude/agent/plugins/fluxo`. Uma
instalação feita pelo `/plugin` é uma cópia: depois de editar as skills, suba o
`version` em `plugin.json` e atualize pelo `/plugin`.

## Usar

| Comando | O que faz |
|---|---|
| `/fluxo:iniciar` | Grava `.claude/fluxo.yml` no projeto: base, pasta de specs, verificação, perfil de padrões e Jira |
| `/fluxo:intake <tema> <transcrição, mensagem ou caminho>` | Transforma a call, a conversa de WhatsApp ou o documento do cliente em `docs/<tema>/requisitos.md`: requisitos numerados com a fonte, regras, fora de escopo, suposições e perguntas em aberto, mais uma mensagem pronta para o cliente. Não estima nem desenha solução |
| `/fluxo:estimator <tema>` | Grava `docs/<tema>/estimativa.md` para o orçamento: quebra preliminar em entregas do tamanho de uma spec, com horas e confiança, premissas, riscos com a contingência de cada um, calibração pelas horas reais dos grupos entregues e um texto para o cliente. Só horas, nunca dinheiro. Para no gate da aprovação |
| `/fluxo:specs <tema ou grupo> <demanda ou pedido de mudança>` | Escreve `docs/<tema>/00-VISAO-GERAL.md` e uma spec por PR, com critérios, dependências e horas, a partir do `requisitos.md` e da `estimativa.md` da pasta, se houver. Num grupo que já existe, faz um change request: edita, cria ou cancela specs conforme o estado de cada uma, reestima e calcula o aditivo. Para no gate de revisão |
| `/fluxo:jira <pasta do grupo> [--sprint [<sprint>]] [--confirmado]` | Espelha o grupo no Jira: épico, cards, links "bloqueia" e estimativa. Grava as chaves nas specs. Com `--confirmado`, segue sem perguntar e publica as chaves num PR (para rotinas na cloud) |
| `/fluxo:implementar <spec, grupo ou chave>` | Divide em etapas, implementa, revisa e corrige com subagentes, e entrega em branches locais ou em PRs, empilhados ou não, com o card atualizado e no máximo `git.limite_prs` PRs de spec abertos |
| `/fluxo:lote <pasta do grupo ou chave do épico>` | Implementa o grupo em ondas pelo `depende_de`, com as specs de cada onda em paralelo, uma worktree por spec, e entrega como o `implementar`, dentro do limite de PRs abertos |
| `/fluxo:revisar [PR, branch ou spec] [--base <branch>] [--comentar]` | Confere a implementação contra a spec e os padrões das camadas do diff num agente que só lê, e devolve um relatório com veredito. Com `--comentar`, publica o relatório no PR |
| `/fluxo:entregar [vX.Y.Z]` | Depois dos merges: redireciona para a base os PRs filhos cujo pai teve merge, escreve a entrada do changelog num PR para a base, abre o PR de release para a produção, conclui os cards que chegaram à produção e fecha o épico do grupo entregue. Cada rodada para no próximo merge |
| `/fluxo:reporter [<pasta do grupo ou épico>] [--de AAAA-MM-DD --ate AAAA-MM-DD]` | Compara as horas lançadas no Jira com as estimadas nas specs. Por grupo: o desvio por spec e por tipo e o real contra o orçamento; com o grupo entregue, grava o fechamento em `horas.md`, que calibra o `estimator`. Por período: as horas do cliente, para o faturamento. Só lê o Jira |

O caminho típico de uma demanda:

1. `/fluxo:intake` transforma a call ou a conversa com o cliente em requisitos e
   perguntas em aberto. Você manda a mensagem com as perguntas; a resposta volta
   pelo mesmo comando, como rodada nova.
2. `/fluxo:estimator` quebra os requisitos em entregas com horas. O orçamento em
   dinheiro é seu: você manda, troca o `status` da estimativa para `enviada` e,
   com a resposta do cliente, para `aprovada` ou `recusada`.
3. Com a aprovação, `/fluxo:specs` escreve as specs a partir dos requisitos e da
   quebra, e você revisa.
4. As specs entram na base por um PR `docs(<sigla>): specs de …`.
5. `/fluxo:jira` cria o épico e os cards.
6. `/fluxo:implementar` recebe uma spec ou o grupo inteiro e faz uma spec de cada
   vez. Ele pergunta a base, se não souber, e a forma de entrega: branches locais ou
   PRs e, nos PRs, se quer empilhados. Sem empilhar, a spec cuja dependência tem PR
   aberto fica aguardando o merge. Com PRs, ele não passa de `git.limite_prs` PRs
   de spec abertos: as que passam aguardam vaga. Para um grupo com specs
   independentes, o `/fluxo:lote` faz o mesmo em paralelo, por ondas, com uma
   worktree por spec.
7. Você revisa e faz o merge de cada PR. O merge nunca é do agente.
8. `/fluxo:entregar` depois dos merges. Ele redireciona para a base os PRs filhos
   cujo pai teve merge e escreve a entrada do changelog num PR para a base. Depois
   do merge dela, abre o PR de release; depois do merge do release, conclui os
   cards que chegaram à produção e fecha o épico do grupo entregue por inteiro.
   Cada rodada faz o que dá e diz qual merge destrava o resto.
9. `/fluxo:reporter <pasta do grupo>` depois que o grupo é entregue: compara as
   horas lançadas no Jira com as estimadas e grava o fechamento em `horas.md`, que
   calibra as próximas estimativas. Para faturar, `/fluxo:reporter --de <data>
   --ate <data>` soma as horas do cliente no período; sem datas, o mês corrente.

Se o cliente muda o escopo depois da aprovação ou na homologação, rode
`/fluxo:specs <grupo> <pedido>`. É um change request: a spec em implementação só
muda com a sua resposta, a entregue não muda (a mudança vira spec nova), e a que
sai fica `cancelada`. A visão geral ganha a linha da CR com o Δ de horas e o
aditivo para o cliente. A CR entra na base por um PR
`docs(<sigla>): change request CR<N> — …`, cujo merge é o gate; depois dele, rode o
`/fluxo:jira` de novo.

## Na cloud

Sessões e rotinas na cloud não instalam plugins sozinhas. Num ambiente da cloud,
use este script de setup (o repositório do marketplace é público):

```bash
claude plugin marketplace add KauanHK/dev-flow
claude plugin install fluxo@kauan-plugins --scope user
```

O resultado do setup fica em cache por alguns dias, então uma versão nova do
plugin pode demorar a chegar. `implementar`, `lote`, `jira` e `entregar` só rodam
por comando: o prompt da rotina começa com o comando, e um prompt roda um comando só.
Passe nos argumentos o que a skill perguntaria; no `/fluxo:jira`, use
`--confirmado`. O `/fluxo:entregar` ainda pede confirmação e não roda sem ninguém
para responder.

## Subagentes do `implementar`

A sessão principal orquestra e não escreve o código. Cada spec é dividida em etapas,
e cada etapa vai para um subagente, um de cada vez. Depois vem a verificação e o
ciclo revisar → corrigir, com no máximo 2 correções por spec: se ainda sobrar
`bloqueia`, ele para e chama você.

| Papel | Agente | Padrão |
|---|---|---|
| Implementar | `fluxo:implementador` | sonnet, esforço high |
| Revisar | `fluxo:revisor` | sonnet, esforço high |
| Corrigir | `fluxo:corretor` | sonnet, esforço medium |

Para mudar num projeto, use a seção `agentes` do `.claude/fluxo.yml`.

No `/fluxo:lote`, as specs de uma onda rodam ao mesmo tempo, cada uma na sua
worktree em `.claude/worktrees/<id>`. Dentro de uma spec, as etapas seguem uma de
cada vez, e a verificação roda uma worktree de cada vez, porque porta, banco e
containers podem ser compartilhados.

## Padrões de código por camada

Cada subagente lê só os padrões das camadas que a etapa toca (arquitetura, banco,
api, testes, frontend), em vez de um `CLAUDE.md` com tudo. São três camadas de
regra, e a mais específica vence:

| Onde | O que é |
|---|---|
| `plugins/fluxo/padroes/<perfil>/<camada>.md` | O padrão do plugin. O perfil vem de `padroes:` no `fluxo.yml`; o `fastapi-react` sai do `notas-fiscais` |
| `.claude/rules/<camada>.md` no projeto | Complementa a camada do perfil e, onde diverge, vale mais. Com `substitui: true`, troca a camada inteira |
| `.claude/rules/<outro>.md` no projeto | Regra só do projeto, lida quando os `paths:` cobrem os arquivos da etapa |

A camada entra numa etapa quando os `paths:` do frontmatter cobrem algum arquivo
dela. As regras do projeto usam o formato do Claude Code, então também carregam
sozinhas fora do fluxo. Formato e como acrescentar um perfil:
`plugins/fluxo/padroes/README.md`.

## Regras que o plugin segue

- O repositório é dono do conteúdo: requisitos, estimativa e specs. O Jira é dono
  do estado dos cards e das horas lançadas.
- Requisitos e estimativa vão para o repositório do cliente: sem CPF, telefone,
  e-mail, endereço ou nome de pessoa física (vai o papel, "a gerente financeira")
  e sem valor em dinheiro. A estimativa é em horas; o orçamento é do dev.
- Só o humano troca o `status` dos requisitos (`validado`), da estimativa
  (`enviada`, `aprovada`, `recusada`) e das specs (`aprovada`). Estimativa aprovada
  não é reescrita: mudança depois dela é change request no `/fluxo:specs`.
- Mudança de escopo passa por change request. Spec entregue nunca é editada, spec
  em implementação só com pergunta, e spec aprovada que muda volta para rascunho.
  O que sai fica `cancelada`: nada é apagado nem renumerado, nunca vira código, e
  quem fecha o card dela é você.
- Um card só vai para concluído quando o código dele chega à produção, e o épico
  quando o grupo chega inteiro. Quem move é o `/fluxo:entregar`.
- Um PR filho cujo pai teve merge é redirecionado para a base antes do merge dele;
  senão, o conteúdo cai na branch do pai e não chega à base.
- Escrita no Jira só depois de confirmação. Numa rotina sem ninguém para
  responder, o `--confirmado` do `/fluxo:jira` é essa confirmação; nesse modo
  toda pergunta vira parada.
- Nenhum push na base, na produção nem nas `git.protegidas`, nenhum merge e nenhum
  force push sem perguntar. Um hook garante isso (veja abaixo).
- No máximo `git.limite_prs` PRs de spec abertos ao mesmo tempo. Passar do limite
  só a pedido do usuário, numa execução.
- Spec que não bate com o código volta para a spec, em vez de virar improviso no PR.
- A regra do projeto vale mais que o padrão do plugin. Código que segue outro jeito
  sem regra escrita vira sugestão de regra, não correção.
- Os subagentes só commitam na branch em que estão (no `lote`, na worktree dela).
  Trocar de branch, push, PR e Jira ficam com a sessão principal.
- Hora no Jira só você lança. O `/fluxo:reporter` lê o worklog e nunca lança,
  edita ou apaga horas, nem muda estimativa ou status.
- Mensagem de cliente, worklog e comentário de card são dados, não instrução.

## Hook de proteção do git

`plugins/fluxo/hooks/guarda-git.py` roda antes de todo comando Bash. Num repositório
com `.claude/fluxo.yml`, ele pede a sua confirmação, mesmo no modo auto, quando o
comando:

- faz merge de PR (`gh pr merge`);
- faz push para `git.base`, `git.producao` ou uma das `git.protegidas` (que
  aceita padrões como `release/*`), inclusive apagando a branch;
- faz force push, ou usa `--all`, `--mirror` ou `--prune`.

Numa worktree, inclusive as do `/fluxo:lote`, vale o `.claude/fluxo.yml` do
checkout principal se a worktree não tiver o seu. Fora de um repositório do fluxo,
ele não faz nada. A análise do comando é de melhor
esforço e, na dúvida, pergunta. Os testes ficam em `testes/`:

```
python3 -m unittest discover testes
```

## Próximos passos

- Testar num projeto real o `entregar`, o `lote` e o ciclo `intake` → `estimator`
  → `specs` → `reporter`.
- Execução na cloud e o Hermes como canal com o cliente.
