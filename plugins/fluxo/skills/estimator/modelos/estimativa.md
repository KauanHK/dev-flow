---
status: rascunho            # rascunho | enviada | aprovada | recusada: só humano troca
total_h: 0                  # base_h + contingencia_h: as horas do orçamento
quebra_h: 0                 # soma da quebra, na escala das specs
base_h: 0                   # quebra_h × calibracao, arredondada para cima
contingencia_h: 0           # soma das horas da tabela de riscos
calibracao:                 # razão real/estimado aplicada (1.20); vazio sem calibração
---

# <Assunto> — estimativa

## Contexto

<Requisitos de origem (`requisitos.md`, status e data da última rodada) e a data
desta estimativa. O que foi conferido no código: módulos lidos, o que já existe, o
que não deu para conferir. Calibração: de quantos grupos, a razão histórica e a
usada; ou "sem histórico de horas no projeto".>

## Quebra preliminar

| # | Entrega | Requisitos | Horas | Confiança |
|---|---|---|---|---|
| E1 | <resultado, não tarefa> | R1, R2 | 4 | alta |
| E2 | <resultado> | R3 | 6 | baixa: <por quê> |
| | **Soma** | | **<N>** | |

<Não é spec: sem critério de aceite nem desenho. O `/fluxo:specs` refina a quebra
depois da aprovação.>

## Premissas

- <O que, se mudar, muda o número. Inclui a resposta assumida para cada pergunta em
  aberto que pesa nas horas: "P2: o envio é só por e-mail".>

## Riscos

| Risco | Horas se acontecer | Por quê |
|---|---|---|
| <O que pode dar errado.> | <N> | <De onde vem o risco: entrega, premissa, código.> |

## Fora do escopo

- <O que não entra nestas horas e o motivo: o cliente adiou, fica para outro
  orçamento.>

## Total

Base <base_h> h (quebra de <quebra_h> h × <calibracao>) + contingência
<contingencia_h> h = <total_h> h.

## Texto para o orçamento

<Para o cliente, em linguagem de negócio: o que está incluso, as horas totais, as
premissas que ele precisa saber e o que não está incluso. Sem nome de arquivo, sem
jargão e sem valor em dinheiro.>

## Histórico

- <AAAA-MM-DD — primeira versão: <total_h> h.>
- <AAAA-MM-DD — <total anterior> h → <novo> h: <o que mudou nos requisitos>.>
