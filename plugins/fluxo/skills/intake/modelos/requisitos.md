---
status: rascunho            # rascunho | validado (o cliente respondeu o que muda o escopo)
origem:                     # cada fonte, com canal e data
  - call 2026-11-20
---

# <Assunto> — requisitos

## Contexto

<O cliente (a empresa), quem pediu, pelo papel ("a gerente financeira"), e o
problema nas palavras do negócio. Sem nome de pessoa, telefone, e-mail, CPF ou
endereço.>

## Objetivo

<Uma ou duas frases: o que muda para o negócio quando a demanda estiver entregue.>

## Requisitos

| # | Requisito | Fonte | No código |
|---|---|---|---|
| R1 | <Um comportamento, do ponto de vista de quem usa.> | <call de 20/11, ou "citação curta" (WhatsApp, 21/11)> | <novo; existe em parte: `caminho`; já existe: `caminho`; — sem código> |

<Os números não mudam entre rodadas. O requisito removido fica na tabela, riscado e
com o motivo: `~~texto~~ removido em 25/11: o cliente desistiu`.>

## Regras de negócio

- <Regra que o sistema precisa respeitar, com a fonte: "pedido cancelado não entra
  no relatório" (call de 20/11).>

## Requisitos não funcionais

- <Só o que foi dito ou é óbvio pelo contexto: prazo, volume, integração, LGPD. Com
  a fonte. Remova a seção se não houver.>

## Fora de escopo

- <O que o cliente disse que não quer ou que fica para depois, com a fonte.>

## Suposições

- S1. <O que foi inferido e precisa de confirmação, e de onde veio a inferência.>

## Perguntas em aberto

- P1. <Pergunta para o cliente.> Muda: <o que muda conforme a resposta: "se sim,
  R3 inclui o envio por WhatsApp".>

## Histórico

- <AAAA-MM-DD — primeira versão, da call de 20/11.>
- <AAAA-MM-DD — respostas por WhatsApp: P1 → R3, P2 → fora de escopo; R5 novo.>
