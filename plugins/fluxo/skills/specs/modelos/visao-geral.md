---
sigla: <sigla>              # curta e única no projeto: conta, robustez. Prefixo do id das specs
jira:                       # chave do épico, preenchida pelo /fluxo:jira
---

# <Assunto> — visão geral e índice

Documento de entrada. Toda spec numerada abaixo pressupõe que você leu **este**
arquivo. <Se valerem decisões de outros grupos, cite: "Pressupõe também as decisões
D3–D9 de `docs/nfse/specs/00-VISAO-GERAL.md`, que continuam valendo.">

## Contexto

<De onde veio a demanda (cliente, data, canal), o que está em jogo e o que foi
conferido no código. Separe o que foi verificado do que é suposição.>

## Decisões já tomadas

| # | Decisão | Porquê |
|---|---|---|
| X1 | **<A decisão, numa frase forte.>** <Detalhe.> | <O motivo, e o que daria errado sem ela.> |

## Specs

| Spec | O que entrega | Depende de | Estimativa |
|---|---|---|---|
| [01](01-<slug>.md) | <resultado, não tarefa> | — | <N>h |
| | **Total** | | **<soma>h** |

## Ordem de execução

```
01 <slug>        (independente — pode ir primeiro)

02 <slug> ─► 03 <slug> ─► 04 <slug>
                  │
                  └─► 05 <slug>
```

<Por que essa ordem: o que cada passo destrava e qual é o caminho crítico.>

Cada spec é uma branch a partir de `<base>` e um PR, em stack quando houver
dependência: a branch da spec N nasce da branch da spec de que ela depende, e o PR
usa essa branch como base.

### Ondas

| Onda | Em paralelo | Condição para começar |
|---|---|---|
| 1 | 01 · 02 | nenhuma |
| 2 | 03 | 02 pronta |

<Specs da mesma onda que mexem nos mesmos arquivos não vão em paralelo: diga quais
e por quê.>

## Versões

<Só se o projeto versiona por changelog. Que specs saem juntas em cada versão e por
quê. Remova a seção se não se aplicar.>

| Versão | Specs | O que fecha |
|---|---|---|
| vX.Y.Z | 01 + 02 | <marco> |

## Regras que valem para todas as specs

1. <Regra de teste, de ordem de operações ou de convenção que toda spec segue.>

## Critério de pronto do conjunto

<Cenários de ponta a ponta que, juntos, provam que o grupo resolveu o problema do
Contexto.>

1. <Cenário.>

## Perguntas em aberto

- <Pergunta, para quem e o que muda no desenho conforme a resposta. Remova a seção
  quando ficar vazia.>
