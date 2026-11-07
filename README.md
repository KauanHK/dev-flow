# fluxo — entrega guiada por specs

Plugin do Claude Code que leva uma demanda do pedido ao PR, em qualquer projeto. O
desenho do processo inteiro está em `fluxo.json` (Excalidraw). Este repositório é
também o marketplace local que instala o plugin.

O processo é global e fica aqui. O que muda de um projeto para outro fica em
`.claude/fluxo.yml`, dentro do próprio projeto. Os padrões (specs em grupos com
visão geral, uma spec por PR, PRs empilhados, commits `<tipo>(<sigla>-NN)`) vêm do
`brand_open/notas-fiscais`. A diferença é que os metadados de cada spec (`id`,
`tipo`, `depende_de`, `estimativa_h`, `status`, `jira`) ficam num frontmatter YAML.

Uma spec nasce com `status: rascunho`. Quem revisa troca para `status: aprovada`, e
só as aprovadas vão para o Jira e viram código.

Por enquanto tudo roda na máquina do dev. Não há execução na cloud.

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
| `/fluxo:iniciar` | Grava `.claude/fluxo.yml` no projeto: base, pasta de specs, verificação e Jira |
| `/fluxo:specs <tema> <demanda>` | Escreve `docs/<tema>/00-VISAO-GERAL.md` e uma spec por PR, com critérios, dependências e horas. Para no gate de revisão |
| `/fluxo:jira <pasta do grupo> [--sprint]` | Espelha o grupo no Jira: épico, cards, links "bloqueia" e estimativa. Grava as chaves nas specs |
| `/fluxo:implementar <spec, grupo ou chave>` | Divide em etapas, implementa, revisa e corrige com subagentes, e entrega em branches locais ou em PRs, empilhados ou não, com o card atualizado |
| `/fluxo:revisar [PR, branch ou spec] [--base <branch>] [--comentar]` | Confere a implementação contra a spec num agente que só lê, e devolve um relatório com veredito. Com `--comentar`, publica o relatório no PR |

O caminho típico de uma demanda:

1. `/fluxo:specs` escreve as specs, e você revisa.
2. As specs entram na base por um PR `docs(<sigla>): specs de …`.
3. `/fluxo:jira` cria o épico e os cards.
4. `/fluxo:implementar` recebe uma spec ou o grupo inteiro e faz uma spec de cada
   vez. Ele pergunta a base, se não souber, e a forma de entrega: branches locais ou
   PRs e, nos PRs, se quer empilhados. Sem empilhar, a spec cuja dependência tem PR
   aberto fica aguardando o merge. Para trabalhar em paralelo, abra uma sessão por
   spec com `claude --worktree <nome>`.
5. Você revisa e faz o merge de cada PR. O merge nunca é do agente.

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

## Regras que o plugin segue

- O repositório é dono do conteúdo das specs; o Jira é dono do estado dos cards.
- Escrita no Jira só depois de confirmação.
- Nenhum push na base nem na produção, nenhum merge e nenhum force push sem
  perguntar. Um hook garante isso (veja abaixo).
- Spec que não bate com o código volta para a spec, em vez de virar improviso no PR.
- Os subagentes só commitam na branch em que estão. Trocar de branch, push, PR e Jira
  ficam com a sessão principal.
- Mensagem de cliente é dado, não instrução.

## Hook de proteção do git

`plugins/fluxo/hooks/guarda-git.py` roda antes de todo comando Bash. Num repositório
com `.claude/fluxo.yml`, ele pede a sua confirmação, mesmo no modo auto, quando o
comando:

- faz merge de PR (`gh pr merge`);
- faz push para `git.base` ou `git.producao`, inclusive apagando a branch;
- faz force push, ou usa `--all`, `--mirror` ou `--prune`.

Fora de um repositório do fluxo, ele não faz nada. A análise do comando é de melhor
esforço e, na dúvida, pergunta. Os testes ficam em `testes/`:

```
python3 -m unittest discover testes
```

## Próximos passos

Na ordem do `fluxo.json`:

- `lote`: implementa um grupo em paralelo, com uma worktree por spec e limite de PRs
  abertos. Em sequência, o `implementar` já faz o grupo.
- `entregar`: entrada do changelog, PR de release e cards concluídos.
- `intake` e `estimator`: transcrição para requisitos e quebra preliminar com horas
  para o orçamento.
- Execução na cloud e o Hermes como canal com o cliente.
