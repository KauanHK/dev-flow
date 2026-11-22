---
id: <sigla>-NN              # identifica a spec em branch, commit, card e dependências
tipo: feat                  # feat | fix | refactor: tipo da branch e dos commits
depende_de: []              # ids de outras specs, deste ou de outro grupo: [conta-01]
estimativa_h: 4             # 1, 2, 4, 6 ou 8
status: rascunho            # rascunho | aprovada | cancelada: só aprovada vai ao Jira
jira:                       # chave do card, preenchida pelo /fluxo:jira
---

# Spec NN — <Título que diz o resultado>

<Se a spec muda comportamento, uma frase ou uma lista do que muda para quem usa.
Refactor puro: "Não muda comportamento.". Se depende de outra spec, diga o que ela
entrega e esta usa. Se o grupo tem `requisitos.md`, diga os requisitos que ela
atende ou prepara: "Atende R2 e R5.".>

## O problema

<O que está errado ou falta hoje, com referência ao código
(`caminho/arquivo.py:123`). Fatos conferidos no código; o que for suposição, diga
que é.>

## Objetivo

<Uma ou duas frases: como fica o sistema quando a spec estiver pronta.>

## Desenho

<Decisões de implementação, cada uma com o porquê. Nomes de classes, rotas,
tabelas e arquivos. Subseções por lado (Backend, Frontend) ou por peça. Código só
quando a forma importa: assinatura, SQL, protocolo.>

## Fora de escopo

- <O que fica de fora e onde vai ser tratado: outra spec, issue, orçamento futuro.>

## Critérios de aceite

- [ ] <Um comportamento por item, verificável por teste ou por um passo manual
      descrito.>
