# LifeScan

## Design, UX/UI e frontend — qual ferramenta

Uma de cada vez, nesta ordem de escolha. Misturar skills de UI na mesma tela gera direções que brigam.

- **Padrão de UX/UI:** `ui-ux-pro-max` (plugin). Estilo, paleta, tipografia, guias de UX e componentes — sempre sobre o shadcn e os tokens do projeto, nunca um visual novo por cima do design system que já existe.
- **Movimento e animação:** skills `emilkowalski` (`animation-vocabulary`, `improve-animations`, `review-animations`, `apple-design`...).
- **Landing e conversão:** `revenue-centric-design` (+ `ogilvy-copywriting` no texto).
- **Mockup HTML (Artifact):** `artifact-design`.
- **Pesquisa de padrão antes de construir interface:** antes do mockup de tela ou componente novo, consultar <https://ui-patterns.com> (WebFetch na categoria que o problema pede: navegação, formulário, dados, onboarding, feedback, persuasão) e escolher o padrão que resolve o problema do usuário. Uma consulta por tela, não por componente; o resultado vai para o mockup, não para o chat.
- **Padrão de interação:** nomear no mockup o padrão escolhido e o motivo, com o link da página dele no ui-patterns.com, ex.: "Pagination, não Continuous Scrolling: lista de trabalho".
  - **Usar:** Breadcrumbs (2+ níveis), Navigation Tabs (seção = rota), Module Tabs (visão do mesmo dado), Pagination (lista de trabalho), Progressive Disclosure (form/detalhe longo), Cards, Accordion na sidebar.
  - **Evitar no painel:** Carousel, Tag Cloud, Continuous Scrolling em tabela, Fat Footer.

## Frontend — React + Vite (SPA)

O risco é o que chega ao navegador. Antes de usar API nova de React, React Router, Vite ou outra lib,
conferir a versão instalada (`frontend/package.json` / `node_modules/<lib>/package.json`) e a documentação
dessa versão: ela pode divergir do treino.

- **Tudo no frontend é público.** Regra de negócio, autorização e validação de verdade ficam no backend
  (FastAPI); o controle por tipo de usuário no front (`RotaProtegida`, `ehMedico`…) é só experiência, nunca
  segurança. Lib pesada ou usada em poucas telas (`pdfjs-dist`, `mammoth`) entra com `import()` dinâmico /
  `React.lazy`; o tamanho do bundle inicial só desce.
- **Nada de segredo no cliente:** toda variável `VITE_*` (e `import.meta.env.MODE`/`DEV`/`PROD`) vai embutida
  no JavaScript entregue ao navegador. Segredo fica no `backend/.env`, nunca em `VITE_*`.
- **Render puro:** nunca ler a hora no render (`Date.now()`/`new Date()` sem argumento) — o resultado muda a
  cada render e quebra a pureza que o React exige (StrictMode, memoização). Ler em efeito, handler ou num
  hook de "agora" atualizado por intervalo.
- **`<img>` sempre com `width`, `height` e `alt`** (`alt=""` só para imagem decorativa); `loading="lazy"`
  para o que fica abaixo da dobra.
- **Semântica antes de div:** `<button>` para ação, `<a>`/`<Link>` para navegação, `htmlFor` no `<label>`.
  Nada de `onClick` em `div`/`span`.
- **Dívida de lint/a11y fica congelada em baseline;** reprova o aumento. A baseline é
  `frontend/eslint-suppressions.json`: `npm run lint` falha em qualquer violação nova. Ao corrigir uma antiga,
  rode `npm run lint:baseline` para encolher o arquivo. Nunca use `--suppress-all` para esconder violação nova.
- **Não confiar em HMR para concluir que algo funciona:** recarregar a página inteira e rodar `npm run build`.
