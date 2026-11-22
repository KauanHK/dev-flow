---
name: lote
description: Implementa um grupo de specs em paralelo na máquina do dev — monta as ondas pelo depende_de e roda as specs de cada onda ao mesmo tempo, cada uma na sua worktree, com o roteiro do implementar. Respeita o limite de PRs abertos e entrega em branches locais ou em PRs, empilhados ou não.
argument-hint: <pasta do grupo | chave do épico>
disable-model-invocation: true
---

# Implementar um grupo em lote

Entrada: $ARGUMENTS

## Quando usar

`/fluxo:lote` para um grupo com specs independentes entre si, que ganham tempo
rodando em paralelo. Para uma spec só, ou um grupo que vai em sequência, use o
`/fluxo:implementar`: ele já faz o grupo, e o lote só acrescenta o paralelismo.

## O roteiro

Leia `${CLAUDE_PLUGIN_ROOT}/skills/implementar/SKILL.md` inteiro. Ele é o roteiro
de cada spec, e tudo o que ele manda vale aqui, menos o que esta skill muda. Você é
o orquestrador e não escreve código; as regras do topo dele (merge, push, force
push, branches protegidas) valem igual.

O que muda: as specs de uma onda rodam ao mesmo tempo, cada uma numa worktree
própria, e o checkout principal não troca de branch. Dentro de uma spec, as etapas
continuam uma de cada vez.

## 1. Preparar

Siga os passos 1 a 4 do `implementar`: pré-condições, leitura das specs, perguntas
(base, entrega, empilhar) e base de cada spec, com o limite de PRs abertos. Se a
entrada for uma spec só, diga para usar o `/fluxo:implementar` e pare.

**Ondas.** Parta da tabela de ondas da visão geral e confira cada spec contra o
`depende_de`: uma spec só entra numa onda depois que todas as dependências foram
entregues numa onda anterior ou antes desta execução. Se a tabela contradiz o
`depende_de`, vale o `depende_de`, e o relatório diz isso. Sem tabela, monte as
ondas pelo `depende_de`.

**Paralelismo.** Com PRs e `git.limite_prs`, rodam numa onda as specs dela que
cabem nas vagas; as outras aguardam vaga, como no passo 4 do `implementar`. Sem
limite ou com branches locais, a onda inteira. Se o roteiro de verificação ou o
`CLAUDE.md` mostram que nem os testes de unidade rodam em paralelo (banco
compartilhado sem isolamento, porta fixa), os implementadores de uma onda rodam um
de cada vez, e o lote ainda ganha as worktrees isoladas.

## 2. Plano

Antes de começar, mostre as ondas:

| Onda | Spec | Base | Worktree |
|---|---|---|---|
| 1 | conta-01 | `dev` | `.claude/worktrees/conta-01` |
| 1 | conta-02 | `dev` | `.claude/worktrees/conta-02` |
| 2 | conta-03 | `feat/conta-01-trocar-senha` | `.claude/worktrees/conta-03` |

Embaixo: as que aguardam vaga ou merge, as que ficaram de fora, as canceladas numa
linha, as ondas que o `depende_de` corrigiu, as specs que rodam em sequência por
tocar os mesmos arquivos (pela visão geral; a divisão em etapas pode acrescentar
outras) e se os implementadores rodam um de cada vez. Mostre e siga, sem esperar
aprovação; pergunte só onde o `implementar` manda perguntar.

## 3. Worktrees

Uma por spec, em `<raiz do repositório>/.claude/worktrees/<id>`, o mesmo lugar do
`claude --worktree`. Crie as de uma onda no começo dela.

1. A pasta tem que estar fora do git: `git check-ignore -q .claude/worktrees/<id>`.
   Senão, acrescente `/.claude/worktrees/` em `.git/info/exclude`; nunca no
   `.gitignore` do projeto sem pedir.
2. `git worktree add -b <branch> <caminho> <ref da base>`, com a branch e a ref do
   passo 5 do `implementar`. Branch que já existe (retomada):
   `git worktree add <caminho> <branch>`. Worktree que já existe
   (`git worktree list`): reaproveite, se está na branch da spec; com mudança não
   commitada, pergunte.
3. Ambiente. Com `.worktreeinclude` no projeto, copie para a worktree os arquivos
   ignorados que ele lista (`git ls-files --others --ignored
   --exclude-from=.worktreeinclude`), como o `claude --worktree` faz. Copie também
   `.claude/fluxo.yml` e `.claude/rules/`, se o git os ignora: os subagentes leem
   da worktree. Prepare as dependências como o roteiro de verificação ou o
   `CLAUDE.md` mandam (`uv sync`, `npm ci`).
4. Se a verificação precisa de um arquivo ignorado que o `.worktreeinclude` não
   lista (um `.env`), pergunte ao usuário, uma vez para o lote. Não leia o conteúdo
   de `.env`.

O resto do passo 5 do `implementar` vale em cada worktree: trabalho retomado,
`rebase --onto` de dependência que entrou na base e card em andamento. Rode os
comandos de uma spec dentro da worktree dela (`cd <caminho> && …`): o git não
troca para uma branch que está em outra worktree.

Não use o `isolation: worktree` do `Agent`: a worktree dele não nasce da base da
spec nem dura de uma etapa para a outra.

## 4. Executar uma onda

Anote a hora (`date +%H:%M`) no começo e no fim de cada onda, para o relatório.

1. **Etapas.** Divida cada spec da onda como no passo 6 do `implementar`, lendo o
   código na worktree dela. Duas specs que tocam os mesmos arquivos não rodam em
   paralelo: a segunda começa depois que a primeira foi entregue. Mostre as etapas
   e essa ordem.
2. **Implementar.** Chame em paralelo, com várias chamadas `Agent` na mesma
   mensagem, um `fluxo:implementador` por spec da onda, cada um com a primeira
   etapa da sua spec. O prompt é o do passo 7, com a worktree no lugar da branch:
   "Você trabalha na worktree `<caminho>`, na branch `<branch>`. Comece todo
   comando Bash com `cd <caminho> &&` e use caminhos absolutos dentro dela." Os
   caminhos da spec, da visão geral e das regras do projeto são os da worktree.
   Quando um termina, confira a etapa (`git -C <caminho> status --porcelain` e
   `git -C <caminho> log`) e chame a etapa seguinte dessa spec.
3. **Verificar.** O passo 8 em cada worktree, uma de cada vez, porque portas,
   banco e containers podem ser compartilhados: desligue o que a verificação subiu
   antes da próxima. O commit dos critérios é feito na worktree.
4. **Revisar e corrigir.** O passo 9, com os revisores em paralelo e a worktree
   no prompt de cada um, antes da entrada: "A branch está na worktree
   `<caminho>`." Os corretores também rodam em paralelo, um por worktree, com o
   aviso do implementador. O limite de 2 ciclos é por spec.
5. **Entregar.** O passo 10, uma spec de cada vez, com os comandos dentro da
   worktree. Depois, `git worktree remove <caminho>`; a branch fica.

**Spec que para** (bloqueia depois de 2 ciclos, spec errada, trava): as outras da
onda terminam, e a worktree dela fica. Ao fim da onda, chame o usuário com o que
parou e espere a resposta. A onda seguinte não começa as specs que dependem da
parada.

## 5. Ondas seguintes

A base de cada spec segue a tabela do passo 4 do `implementar`. Com PRs empilhados
ou branches locais, a onda seguinte nasce das branches da anterior. Com PRs sem
empilhar, a spec que depende de PR aberto aguarda; quando só restam specs
aguardando, o lote termina e diz quais merges as destravam.

Rodar de novo continua de onde parou: spec com PR aberto ou merge é pulada, e a
worktree que já existe é reaproveitada.

## 6. Relatório

O do passo 11 do `implementar`, mais:

- as worktrees que ficaram, com o caminho e o motivo;
- as ondas que o `depende_de` corrigiu e as specs que rodaram em sequência por
  tocar os mesmos arquivos;
- o tempo de cada onda, pelas horas anotadas.
