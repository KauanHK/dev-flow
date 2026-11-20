---
camada: frontend
descricao: SPA em React, TypeScript, Vite e TanStack Query — features, acesso à API, rotas e estilo.
paths:
  - "**/frontend/src/**"
  - "**/frontend/index.html"
  - "**/frontend/package.json"
---

# Frontend

SPA em React + TypeScript + Vite, com TanStack Query para os dados do servidor e
react-router para as rotas. CSS puro com design tokens; sem Tailwind e sem
biblioteca de componentes.

```bash
npm run lint
npm run build      # tsc -b && vite build: o type-check roda aqui
```

## Estrutura de `src/`

- **`api/http.ts`**: o client HTTP central. Injeta a base URL e o `Authorization`,
  faz o refresh em `401` e lança `ApiError`. **Todo acesso à API passa por ele**;
  nada de `fetch` direto.
- **`features/<dominio>/`**: o trio
  - `types.ts`: tipos do domínio, espelhando o `*Read` do backend; campo que pode
    vir nulo é `| null`;
  - `api.ts`: funções que chamam `api/http.ts`;
  - `hooks.ts`: `useQuery`/`useMutation`. **Toda mutação invalida a query key da
    lista** correspondente.
  Lógica de exibição que não é chamada à API (formatação, agrupamento, cálculo)
  vai num arquivo próprio da feature (`format.ts`, `grouping.ts`), puro e sem
  React.
- **`pages/<dominio>/`**: as páginas, registradas em `router.tsx` dentro de
  `RequireAuth`, com o item de navegação no `AppLayout`.
- **`components/`**: o que é compartilhado entre features; as primitivas de UI em
  `primitives.tsx`.
- **`styles/`**: `tokens.css` (cores, espaçamentos, fontes) e `base.css`. Cor e
  medida novas viram token, não valor solto.

Feature nova replica o trio e a página da feature mais completa do projeto.

## Regras

- **Textos de UI em português**, e a opção diz o que faz: um select de códigos
  ("1", "2", "3") vira rótulos que explicam o efeito.
- Decisão de erro pelo `code` do `ApiError`, não pelo texto. A mensagem do backend
  já vem em português e pode ser mostrada.
- Validação que existe no backend é espelhada no formulário, com o mesmo limite,
  mas o backend continua sendo quem decide.
- Enquanto um dado necessário carrega, o padrão é **não oferecer a ação**: botão
  que responderia erro fica desabilitado, com o motivo no tooltip.
- Painel e diálogo fecham no Esc e no clique fora, e devolvem o foco ao gatilho.
  Diálogo com requisição em andamento não fecha.
- Data de negócio no fuso do negócio, igual ao backend; a data trafega em
  `AAAA-MM-DD`.
- Comentários em português.
