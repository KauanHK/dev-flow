---
estimado_h: 40              # soma do estimado das specs da tabela
real_h: 46.5                # soma do real das mesmas specs, pelo worklog do Jira
razao: 1.16                 # real_h / estimado_h, com duas casas
fechado_em: 2026-11-22      # AAAA-MM-DD do fechamento; vazio = parcial, não calibra
---

# Horas — <Assunto da visão geral>

Épico <ÉPICO>. Real pelo worklog do Jira, lido em <AAAA-MM-DD>; estimado pelo
`estimativa_h` das specs. <Só no parcial: "Parcial: o grupo ainda não foi
entregue.">

Entram na tabela as specs com card concluído e horas lançadas. As outras vão para
"Fora da conta".

| Spec | Tipo | Estimado | Real | Desvio |
|---|---|---|---|---|
| [<sigla>-01](01-<slug>.md) | feat | 4h | 5,5h | +1,5h (+38%) |
| **Total** | | **40h** | **46,5h** | **+6,5h (+16%)** |

## Por tipo

| Tipo | Specs | Estimado | Real | Razão |
|---|---|---|---|---|
| feat | 5 | 30h | 33h | 1,10 |

## Orçamento

<Só com `estimativa.md` aprovada; senão, remova a seção.>

| | Horas |
|---|---|
| Orçamento: `total_h` da estimativa + aditivos das CRs | <N>h |
| Real total do grupo, com as horas fora da conta | <N>h |

## Fora da conta

<Remova a seção quando vazia.>

- Horas fora de spec: <card — título — Nh>, lançadas no épico, em cards sem spec ou
  em specs canceladas.
- Horas não lançadas: <spec — card>, concluída sem worklog.
- Em aberto (só no parcial): <spec — card — real até agora>.
