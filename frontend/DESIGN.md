# LifeScan: sistema visual

Guia para escrever e revisar telas do frontend. Descreve o que **já existe** no código: as
variáveis de `src/index.css`, as peças de `src/components/ui.jsx` e os padrões
das páginas. Quem criar uma tela nova (pessoa ou agente de IA) deve seguir este guia. Antes de
criar um estilo novo, reaproveite um existente. Se o código e este arquivo divergirem, corrija
um dos dois no mesmo PR.

O visual está mudando: a seção [Direção visual](#direção-visual) descreve para onde ele vai, e
as seções seguintes descrevem o que está no código hoje. Telas novas já devem seguir a direção
nova. Ao implantar cada item, atualize a tabela de implantação e as seções de tokens e layout.

## Princípios

- **Identidade da marca em todo o sistema.** O verde-escuro, o gradiente e a linha de batimento
  da tela de login aparecem também nas telas internas (menu, cabeçalhos, destaques), não só na
  entrada. O conteúdo de trabalho continua em superfícies claras, para leitura confortável.
- **Cor com função.** Além do estado (etiquetas, alertas), a cor identifica o tipo de
  informação: consulta, solicitação e documento têm cor própria e sempre a mesma.
- **Densidade de ferramenta de trabalho.** O médico usa o sistema todos os dias: listas
  compactas, informação secundária em texto suave, ações sempre à vista.
- **Estado sempre com texto.** Cor nunca é o único sinal: etiquetas e alertas têm rótulo e,
  quando cabe, ícone.
- **Português em tudo**, inclusive nomes de classes CSS, variáveis e textos da interface.

## Direção visual

O diagnóstico: depois do login, o sistema vira um fundo branco com texto e detalhes verdes. A
marca existe, mas só aparece na tela de entrada. A direção é levar essa identidade para dentro,
sem perder a leitura confortável das listas e formulários.

### 1. Menu lateral escuro

O menu usa o fundo da apresentação do login. O conteúdo continua claro.

| Variável nova | Valor | Uso |
|---|---|---|
| `--cor-menu` | `#0b514d` | Fundo do menu |
| `--gradiente-menu` | `radial-gradient(ellipse at 0% 100%, #218c7b 0, transparent 60%)` | Luz sutil no pé do menu, sobre `--cor-menu` |
| `--cor-menu-texto` | `#c4e0da` | Links e textos do menu |
| `--cor-menu-texto-forte` | `#ffffff` | Marca, link ativo, nome do usuário |
| `--cor-menu-hover` | `rgb(255 255 255 / 8%)` | Fundo do link no hover |
| `--cor-menu-ativo` | `rgb(255 255 255 / 14%)` | Fundo do link ativo, com barra de `3px` em `#a7e3cc` à esquerda |
| `--cor-menu-borda` | `rgb(255 255 255 / 15%)` | Divisória acima do usuário |

Na barra do topo (abaixo de 900px) vale o mesmo fundo escuro.

### 2. Cabeçalho com presença

- **Faixa** (`<Faixa>` de `ui.jsx`): fundo do login (`bg-menu` com a luz de `--cor-menu-luz` no
  canto inferior direito), texto claro e a linha de batimento como detalhe decorativo à direita
  (`aria-hidden`, some abaixo de 720px). Ela **encosta nas bordas da área de conteúdo** (topo, direita e
  menu), sem raio nem borda. O conteúdo de dentro continua alinhado à coluna de 1040px. Para isso, o `<main>` do
  `Layout` é um container (`@container`) e a faixa usa `100cqw` mais o padding do `main`. Ela precisa
  ser o primeiro elemento da página. Para o menu e a faixa não virarem um "L" verde só, o menu tem
  uma divisória fina à direita (`border-menu-borda/60`; embaixo, na barra do topo) e a faixa uma sombra
  interna do lado do menu (`--sombra-faixa`, `--sombra-faixa-topo`): o menu fica por cima.
- **Painel:** padrão [Dashboard](https://ui-patterns.com/patterns/dashboard), com o que pede atenção no
  topo. A faixa traz a data por extenso (sobretítulo), "Olá, <nome>", a frase "N itens pedem sua atenção"
  (pendências e documentos para revisar; consultas agendadas não contam) e os **resumos dentro dela**.
  Cada resumo é um botão (`aria-expanded`) com a sua **gaveta** logo abaixo, mostrando a lista
  correspondente: padrão [Accordion](https://ui-patterns.com/patterns/AccordionMenu) /
  [Progressive Disclosure](https://ui-patterns.com/patterns/ProgressiveDisclosure), um aberto por vez,
  e clicar de novo fecha.
  - **Dropdown:** a gaveta tem a **mesma largura do resumo** e flutua por cima do conteúdo
    (`absolute`, `z-20`, `--sombra-elevada`). A faixa não cresce quando ela abre (por isso a `Faixa`
    não tem `overflow-hidden`). Ela fecha com Esc (o foco volta ao resumo), com um clique fora ou
    clicando de novo no resumo. Lista longa rola por dentro (`max-h: min(60vh, 520px)`).
  - **Ligação com o resumo:** o resumo aberto e a gaveta têm a mesma cor opaca (`--cor-faixa-aberta`,
    `#256561`) e a mesma borda (`--cor-menu-destaque` a 40%). Uma seta no centro do topo da gaveta
    (losango girado) aponta para ele. Os resumos ficam numa linha só (uma coluna por resumo,
    `--colunas`). Até 720px eles empilham, e a gaveta cobre os resumos de baixo.
  - **Conteúdo na paleta da faixa:** ícone do tipo, título e quantidade no topo. Itens translúcidos
    (`bg-menu-hover`) com texto claro, um embaixo do outro. O item vencido tem um filete à esquerda em
    `--cor-perigo-borda`. As etiquetas continuam com as cores de estado.
  - **Movimento:** a gaveta anima `grid-template-rows` (`0fr` → `1fr`) e a opacidade em `300ms` com
    curva de saída. A cada abertura, o conteúdo entra com fade + `4px` e os itens entram em sequência
    (`30ms` entre eles, até o oitavo).
  - Fechada, a gaveta fica `inert`. As listas que antes ficavam no fim do Painel moram só na gaveta. Abaixo
  da faixa ficam o cadastro e a agenda (médico, colaborador) e os dados LGPD (paciente).
- **Acompanhamento:** a identificação (avatar, título, status, pessoas, Encerrar/Reabrir) fica na faixa.
  O sobretítulo é o link de volta para a lista. As etapas ficam num cartão claro logo abaixo.
- **Demais telas:** `sobretitulo` acima do `h1` com a área do menu ("Cadastros" em pacientes, parceiros
  e colaboradores; "Cuidado" na lista de acompanhamentos). Em "Novo acompanhamento" ele é um link para
  a lista (`sobretituloLink`). Sem faixa escura: ela é exclusiva do Painel e do cabeçalho do
  acompanhamento.
- `sobretitulo`: `0.72rem`, peso `700`, caixa alta, `letter-spacing: 0.12em`, cor `--cor-primaria`
  (`--cor-menu-destaque` na faixa: `sobretituloFaixa`, `sobretituloFaixaLink`). É o mesmo padrão do
  login.

### 3. Tipografia

- Fonte **Manrope**, hospedada no projeto via `@fontsource-variable/manrope` (sem depender do
  Google Fonts). `--fonte: 'Manrope Variable', 'Segoe UI', system-ui, sans-serif`.
- Escala com mais contraste:

  | Elemento | Tamanho | Peso | `letter-spacing` |
  |---|---|---|---|
  | Título da faixa do Painel | `2rem` | `700` | `-0.03em` |
  | `h1` | `1.85rem` (`1.45rem` abaixo de 720px) | `700` | `-0.025em` |
  | `h2` | `1.15rem` | `700` | `-0.015em` |
  | `h3` | `1rem` | `650` | `-0.01em` |
  | Número de resumo | `2rem` | `750` | `-0.03em` |

- Números que se comparam (resumos, horários, datas em lista, contadores) usam
  `font-variant-numeric: tabular-nums`.

### 4. Fundo e profundidade

| Variável | Valor anterior | Valor |
|---|---|---|
| `--cor-fundo` | `#f3f5f7` | `#edf3f1` (o mesmo tom esverdeado do fundo do login) |
| `--cor-borda` | `#e2e7eb` | `#dfe8e4` |
| `--sombra` | `0 1px 2px rgb(16 24 40 / 5%)` | `0 1px 2px rgb(11 81 77 / 6%), 0 4px 12px rgb(11 81 77 / 4%)` |
| `--sombra-hover` (nova) | — | `0 2px 4px rgb(11 81 77 / 8%), 0 12px 28px rgb(11 81 77 / 10%)` |
| `--raio-grande` (nova) | — | `20px` |

Cartões clicáveis (resumos, itens com link) sobem `1px` e trocam para `--sombra-hover` no
hover. Cartões estáticos não se movem.

### 5. Cor por tipo de informação

| Variável nova | Aponta para | Tipo |
|---|---|---|
| `--cor-consulta` / `--cor-consulta-clara` | `--cor-primaria` / `--cor-primaria-clara` | Consultas e agenda |
| `--cor-solicitacao` / `--cor-solicitacao-clara` | `--cor-alerta` / `--cor-alerta-clara` | Solicitações |
| `--cor-documento` / `--cor-documento-clara` | `--cor-info` / `--cor-info-clara` | Documentos |

Onde aplicar: ícone da linha do tempo (já é assim), ícone dos resumos do Painel (sempre
colorido, não só quando há itens), faixa lateral de `3px` nos itens de lista e ícone ao lado
do título dos cartões. O estado (vencida, cancelada…) continua nas etiquetas: a cor do tipo não
substitui a do estado.

### 6. Agenda visual

As consultas do dia aparecem numa faixa de horários (coluna de horas à esquerda, blocos de
consulta coloridos pelo status), com a hora atual marcada por uma linha em `--cor-perigo`. A
lista atual continua para os outros dias e no celular.

### 7. Acabamento

- **Carregamento:** esqueleto (blocos cinza com brilho passando) com o formato do conteúdo, no
  lugar do spinner nas listas e cartões. O spinner fica para ações em botões.
- **Estados vazios:** ícone dentro de um círculo em `--cor-primaria-clara`, título curto e uma
  frase explicando o que vai aparecer ali; quando houver, botão para a ação que preenche a lista.
- **Transições:** `150ms` para hover e cor; `200ms` com `ease-out` para troca de aba e
  entrada de conteúdo (opacidade + `4px` de deslocamento). Tudo respeita
  `prefers-reduced-motion`.

### Implantação

| Item | Situação |
|---|---|
| 1. Menu lateral escuro | Implantado |
| 2. Cabeçalho com presença | Implantado (faixa de ponta a ponta, sem raio) |
| 3. Tipografia | Implantado (o título da faixa do Painel entra com o item 2) |
| 4. Fundo e profundidade | Implantado (as variáveis dos itens 1 e 5 já existem em `index.css`) |
| 5. Cor por tipo de informação | Planejado (já existe só na linha do tempo) |
| 6. Agenda visual | Planejado |
| 7. Acabamento | Planejado |

Ordem sugerida: 1 a 4 primeiro (mudam o sistema inteiro quase só com `index.css` e
`Layout`), depois 5 a 7, tela por tela.

## Tailwind e shadcn/ui

O frontend usa Tailwind v4 + shadcn/ui. Não há mais CSS Modules: não crie `.module.css` novo.
As classes compartilhadas ficam em objetos `estilos` (strings de classes), um por área:
`components/ui.jsx` (peças do app inteiro), `pages/estilosPaginas.js` (páginas internas),
`pages/acompanhamento/estilosAcompanhamento.js` (página do acompanhamento e abas) e
`components/estilosAgenda.js` (calendário e modal da agenda).

- **Tokens:** as variáveis de `:root` continuam sendo a fonte da verdade. O `@theme inline` de
  `index.css` gera classes com o nome delas (`bg-primaria`, `text-texto-suave`, `border-borda`,
  `rounded-raio`, `shadow-sombra`) e aponta as variáveis do shadcn (`--primary`, `--border`,
  `--muted-foreground`...) para elas. Não use a paleta padrão do Tailwind (`bg-teal-700`).
- **Componentes do shadcn:** `npx shadcn@latest add <nome>`. Vão para `src/components/ui/`
  (pasta) e não se confundem com `src/components/ui.jsx` (arquivo, componentes próprios), mas
  importe sempre pelo caminho completo: `@/components/ui/button`.
- **Estilos globais em `@layer base`:** as classes do Tailwind vencem as regras de `index.css`
  (`button`, `input`, `label`, `h1`...). A ordem das camadas está declarada no topo de `index.css`.
- **Pontos de quebra:** use `ate-900:`, `ate-860:`, `ate-760:`, `ate-720:` e `ate-680:` (definidos em
  `index.css`, com `width <= N`, iguais ao `max-width` dos antigos módulos). O `max-[900px]:` do Tailwind usa `width < 900px`
  e muda o layout com 1px de diferença.
- **Sem preflight:** o reset do Tailwind não está ligado. As telas foram migradas pixel a pixel
  sobre os padrões do navegador (`dl`, `fieldset`, listas, `dialog`), e ligar o reset muda o visual:
  é uma mudança à parte, com revisão de tela por tela. Enquanto isso:
  - **Borda de um lado só, tracejada ou pontilhada:** use o atalho (`[border-top:1px_dashed_var(--cor-borda)]`),
    não `border-t border-dashed`. Sem o reset, `border-dashed` vale para os quatro lados, e os lados
    sem largura definida ficam com a largura padrão do navegador (3px).
  - As regras globais de formulário e foco de `index.css` deixam de fora os elementos com
    `data-slot` (todos os componentes do shadcn têm), e a base do shadcn vale só para eles.
- Classes condicionais com `cn()` (`@/lib/utils`).

## Tokens

Valores **atuais** do código. Os novos estão em [Direção visual](#direção-visual) e substituem
estes à medida que forem implantados.

Todos ficam em `:root`, em `src/index.css`. **Não use cores em hexadecimal nos módulos**. Use as
variáveis. Se faltar uma, crie a variável em `index.css` primeiro.

### Cores

| Variável | Valor | Uso |
|---|---|---|
| `--cor-fundo` | `#edf3f1` | Fundo da página |
| `--cor-superficie` | `#ffffff` | Cartões, menu, campos, diálogos |
| `--cor-superficie-suave` | `#f7f9fa` | Hover de itens neutros, estado vazio, campos desabilitados |
| `--cor-borda` | `#dfe8e4` | Bordas de cartões, listas, divisórias |
| `--cor-borda-forte` | `#cfd6dc` | Bordas de campos e botões secundários |
| `--cor-texto` | `#17212b` | Texto principal |
| `--cor-texto-suave` | `#5d6b78` | Metadados, ajuda, rótulos secundários |
| `--cor-texto-apagado` | `#94a0ab` | Placeholder dos campos |
| `--cor-icone-apagado` | `#9aa7b3` | Ícone do estado vazio |
| `--cor-veu` | `rgb(15 23 32 / 45%)` | Fundo atrás dos diálogos (`backdrop:bg-veu`) |
| `--cor-primaria` | `#0f766e` | Marca, botão principal, links, foco |
| `--cor-primaria-escura` | `#0b5d57` | Hover do primário, texto sobre `--cor-primaria-clara` |
| `--cor-primaria-clara` | `#e2f3f0` | Item de menu ativo, seleção, anel de foco dos campos |
| `--cor-primaria-suave` | `#f4fbf9` | Dia com compromissos no calendário |
| `--cor-primaria-borda` | `#b7dfd7` | Borda do dia com compromissos |
| `--cor-primaria-anel` | `rgb(15 118 110 / 12%)` | Anel do dia de hoje no calendário |

Cores de estado: cada uma tem o tom forte (texto e ícone) e o `-clara` (fundo).

| Estado | Forte | Clara | Significado |
|---|---|---|---|
| `perigo` | `#b42318` | `#fdecea` | Erro, vencido, falta, ação destrutiva |
| `alerta` | `#93610a` | `#fff3d4` | Pendente, aguardando revisão, vence em breve |
| `sucesso` | `#1a7340` | `#e3f4e9` | Atendida, realizada, revisado, ativo |
| `info` | `#1d5fa8` | `#e5effb` | Agendada, categoria, informação neutra relevante |

Use sempre o par: texto `--cor-x` sobre fundo `--cor-x-clara`. O contraste já foi pensado para
essa combinação. O contorno dos alertas usa `--cor-x-borda` (`#f5c2bc`, `#f0d68f`, `#b9e2c5`,
`#bcd5f2`). O perigo tem ainda `--cor-perigo-escura` (`#8f1c13`, hover do botão sólido),
`--cor-perigo-suave` (`#fff8f7`) e `--cor-perigo-borda-suave` (`#f3c0ba`), do `itemListaDestaque`.

As variáveis do menu escuro (`--cor-menu`, `--gradiente-menu`, `--cor-menu-*`) e da cor por tipo
(`--cor-consulta`, `--cor-solicitacao`, `--cor-documento` e os `-clara`) já existem, com os valores
da [Direção visual](#direção-visual). A barra do link ativo usa `--cor-menu-destaque` (`#a7e3cc`).

### Tipografia

- Fonte: `--fonte` (Manrope Variable, importada em `main.jsx` de `@fontsource-variable/manrope`).
  Ela vem do próprio bundle, sem Google Fonts nem outro serviço externo. O navegador só baixa o
  subconjunto de caracteres usado (latino, cerca de 25 KB).
- Corpo: `15px`, `line-height: 1.5`.
- Títulos:
  - `h1` `1.85rem` (`1.45rem` abaixo de 720px), peso `700`, `-0.025em`. Título da página, um por tela.
  - `h2` `1.15rem`, peso `700`, `-0.015em`. Título de cartão ou seção.
  - `h3` `1rem`, peso `650`, `-0.01em`. Subtítulo dentro de cartão.
- Número de resumo do Painel: `2rem`, peso `750`, `-0.03em`.
- Números que se comparam usam `tabular-nums`: resumos, contadores (`contagem`, `contador`,
  `contagemEventos`), `meta` das listas, data da linha do tempo, dia e hora do calendário.
- Escala de texto menor, em `rem`: `0.92` (botões, alertas), `0.86` (rótulos, ajuda),
  `0.84` (metadados), `0.76` (etiquetas).
- Pesos usados: `400`, `600` (rótulos, botões, nomes), `650` (`h3`, destaques), `700` (`h1`,
  `h2`, avatar), `750` (número de resumo).

### Espaçamento

Em `rem`. Use os passos que já existem, sem valores soltos:

| Passo | Onde |
|---|---|
| `0.25`–`0.35` | Entre título e subtítulo, ícone e texto pequeno |
| `0.5` | Entre botões (`.acoes`), entre itens pequenos |
| `0.6` | Entre itens de lista (`.lista`) |
| `0.9` | Entre campos de formulário (`.formulario`, `.linhaCampos`) |
| `1` | Abaixo do cabeçalho do cartão |
| `1.25` | Padding de cartão; entre cartões e seções (`.pilha`, `.grade`) |
| `2` | Padding do conteúdo da página (telas largas) |

### Raios e sombras

| Variável | Valor | Uso |
|---|---|---|
| `--raio-grande` | `20px` | Faixa de destaque do Painel e do acompanhamento |
| `--raio` | `12px` | Cartões, resumos, diálogos |
| `--raio-pequeno` | `8px` | Botões, campos, itens de lista, alertas |
| `999px` | — | Pílulas: etiquetas, filtros, contadores |
| `--sombra` | sutil, com o tom do verde | Cartões e resumos |
| `--sombra-hover` | média | Hover de cartão clicável (sobe `1px`); cartão estático não se move |
| `--sombra-elevada` | forte | Só para o que flutua (diálogos) |

## Layout

- `Layout.jsx`: menu lateral escuro (`bg-menu` + `--gradiente-menu`), fixo, de `--largura-menu`
  (248px). **Até 900px** (`ate-900:`) vira barra no topo, também escura, com a navegação rolando na
  horizontal. As classes dos links ficam nas constantes `LINK_ATIVO` / `LINK_INATIVO` (o ativo não
  muda no hover). O ativo tem a barra de `3px` em `--cor-menu-destaque` à esquerda (embaixo, na barra
  do topo). Dentro do menu, o foco do teclado usa `--cor-menu-destaque`, porque o contorno primário
  some no fundo escuro. O logo e o avatar ganham contorno em `--cor-menu-borda`. As variáveis
  `--sidebar*` do shadcn apontam para as do menu.
- O conteúdo fica centralizado com `max-width: 1040px` (o `div` dentro do `main` do `Layout.jsx`).
- Estrutura de página (`estilos` de `pages/estilosPaginas.js`):
  - `cabecalho`: `h1` + `subtitulo` à esquerda, ação principal à direita.
  - `pilha`: cartões empilhados com `1.25rem` entre eles.
  - `grade`: cartões lado a lado, com no mínimo 280px cada.
  - `resumos` / `resumo`: números do Painel, dentro da faixa (cartões translúcidos sobre o escuro).
    O ícone é sempre colorido pelo tom (`tonsResumo`: `perigo`, `alerta`, `info`), mesmo com zero.
  - `faixaTopo`, `tituloFaixa`, `subtituloFaixa`, `atualizacaoFaixa`: o topo da faixa do Painel.
  - `gaveta`, `gavetaAberta`, `gavetaJanela`, `gavetaConteudo`, `gavetaCabecalho`: a gaveta dos resumos.
    `listaGaveta`, `itemGaveta`, `itemGavetaDestaque`, `linkGaveta`, `metaGaveta`, `textoGaveta`,
    `vazioGaveta`: as listas dentro dela, na paleta da faixa.
- Breakpoints usados: `900px` (menu), `860px` (linha com ações empilha), `720px` (tamanho do
  `h1`), `760px` (busca da lista de contas em linha própria), `680px` (login em uma coluna). Prefira `auto-fit`/`minmax` a criar breakpoints novos.

## Componentes

Importe de `src/components/ui.jsx` (`estilos` também é exportado de lá: são strings de classes do
Tailwind, usadas como `className={ui.cartao}`). Não recrie essas peças em módulos de página.

| Peça | Como usar | Observações |
|---|---|---|
| Cartão | `estilos.cartao` + `estilos.cartaoCabecalho` | Container padrão de qualquer seção |
| Botão primário | `estilos.botao` | Uma ação principal por área |
| Botão secundário | `estilos.botaoSecundario` | Cancelar, voltar, ações neutras |
| Botão de perigo | `estilos.botaoPerigo` (contorno) / `botaoPerigoSolido` | O sólido só aparece no diálogo de confirmação |
| Botão pequeno | `cn(estilos.botaoSecundario, estilos.botaoPequeno)` | Ações dentro de itens de lista. Use `cn()` (`@/lib/utils`), não template string: ele resolve o conflito de padding e fonte |
| Botão-link | `estilos.botaoLink` | Ações discretas no meio do texto (visualizar, baixar, remover) |
| Grupo de ações | `estilos.acoes` | Botões lado a lado com quebra |
| Formulário | `estilos.formulario`, `estilos.linhaCampos` | Campos já têm o estilo global; não estilize `input` no módulo |
| Texto de ajuda | `estilos.ajuda`, `estilos.suave` | |
| Lista | `estilos.lista` + `estilos.itemLista` | `itemListaDestaque` para item vencido/urgente |
| Linha com ações | `estilos.linhaComAcoes` | Ações à direita; empilha abaixo de 860px |
| `<Etiqueta variante>` | `neutra`, `perigo`, `alerta`, `sucesso`, `info`, `primaria` | Status e categorias |
| `<Alerta tipo>` | `erro`, `sucesso`, `info`, `alerta` | Mensagens de retorno; `erro` usa `role="alert"` |
| `<Avatar tipo>` | `paciente`, `parceiro`, `colaborador`, `medico` | `grande` no cabeçalho do acompanhamento |
| `<Carregando>` | | Spinner com texto |
| `<EstadoVazio icone>` | | Lista sem itens: sempre explique o que aparece ali |
| `<ErroCarregamento erro>` | | Falha do polling, com a mensagem do backend |
| `<CampoArquivo>` / `<Anexo>` | | Upload com validação (RNF01) e anexo com miniatura |
| `useConfirmar()` | `await confirmar({ titulo, mensagem, rotuloConfirmar, perigo })` | **Nunca** use `window.confirm` |
| `<Paginacao>` | | Listas paginadas no servidor (20 por página) |
| `<Faixa como>` | `section` (padrão) ou `header` | Faixa escura do topo; só no Painel e no acompanhamento, como primeiro elemento |
| Sobretítulo | `estilos.sobretitulo` / `sobretituloLink` / `sobretituloFaixa` / `sobretituloFaixaLink` | Área acima do `h1` |
| Botão na faixa | `cn(estilos.botaoFaixa, estilos.botaoPequeno)` | Contorno claro, sem fundo |

Padrões do acompanhamento (`pages/acompanhamento/estilosAcompanhamento.js`):

- **Abas** (`aba`, `abaAtiva`): sublinhado primário; `contador` em tom de alerta para pendências.
  A aba ativa fica na URL (`?aba=`).
- **Filtros** (`filtro`, `filtroAtivo`): pílulas; a ativa usa `--cor-primaria-clara`.
- **Linha do tempo**: ícone redondo por tipo (`iconesEvento`): consulta → primária,
  solicitação → alerta, documento → info.
- **Passo atual** (`passo`): cada etapa tem um estado (`pendente`, `concluido`, `atual`) que define
  as cores do botão e do número; o traço antes da etapa fica verde quando a anterior foi concluída.

### Status → variante

Mantenha o mesmo significado de cor em todas as telas:

| Domínio | Status | Variante |
|---|---|---|
| Solicitação | pendente / atendida / cancelada | `alerta` / `sucesso` / `neutra` |
| Agendamento | agendada / realizada / faltou / cancelada | `info` / `sucesso` / `perigo` / `neutra` |
| Documento | aguardando revisão / revisado | `alerta` / `sucesso` |
| Documento | categoria | `info` |
| Conta | ativa / aguardando primeiro acesso / desativada | `sucesso` / `alerta` / `neutra` |
| Acompanhamento | ativo / encerrado | `sucesso` / `neutra` |
| Solicitação | vencida (sobrepõe o status) | `perigo`, com `itemListaDestaque` no item |

Um status novo deve seguir a mesma lógica: **finalizado com sucesso → `sucesso`; aguardando
alguém → `alerta`; problema → `perigo`; futuro/informativo → `info`; encerrado sem efeito →
`neutra`**.

## Ícones

- Só `lucide-react`. Não misture outras bibliotecas nem SVGs soltos (o logo é a exceção).
- Tamanhos: `14` em botões pequenos e links, `16`–`18` em botões, títulos e menu, `17` em
  alertas, `20` nos resumos do painel, `26` em estado vazio (`strokeWidth={1.5}`).
- Ícone decorativo leva `aria-hidden="true"`. Botão só com ícone precisa de `aria-label` ou
  `title`.

## Acessibilidade

- Foco visível global (`:focus-visible` com contorno primário). Não remova `outline` sem
  colocar algo equivalente.
- Todo campo tem `<label htmlFor>`. Para texto só de leitores de tela, use `.visualmente-oculto`.
- Abas e opções selecionáveis usam `aria-selected` / `aria-current`, e o estilo pode depender
  desses atributos.
- Diálogos usam `<dialog>` com `showModal()`. Em ações destrutivas, o foco inicial fica em
  "Cancelar".
- Animações respeitam `prefers-reduced-motion` (já tratado globalmente).
- Mensagens de carregamento e sucesso usam `role="status"`; as de erro, `role="alert"`.

## Textos da interface

- Português do Brasil, frases curtas, sem ponto de exclamação.
- Botões com verbo no infinitivo: "Salvar", "Enviar documento", "Reenviar acesso".
- Confirmações dizem a consequência: "A conta não poderá entrar no sistema até ser reativada."
- Estados vazios explicam o que vai aparecer ali, não só "Nada encontrado".
- Datas e horas sempre pelos formatadores de `utils/formatacao.js` (`formatarData`,
  `formatarDataHora`, `formatarPrazoRelativo`). Rótulos de enums vêm das constantes `ROTULOS_*`
  de lá, nunca escritos direto no JSX.

## Ao criar ou alterar uma tela

1. Comece por `ui.jsx` e `pages/estilosPaginas.js`. Só crie classe nova quando o padrão não existir.
2. Uma peça usada em duas ou mais páginas deve ir para o `estilos` de `ui.jsx` (e, se tiver lógica,
   virar componente lá).
3. Cores, raios e sombras só por variável. Espaçamento pelos passos da tabela.
4. Confira em tela larga e abaixo de 900px. Veja a tela de verdade, não só o `npm run build`.

## Exceções conhecidas

- **Login** (`Login.jsx`) tem visual próprio de "porta de entrada": painel de apresentação
  verde-escuro com gradiente, caixa de `28px` de raio, campos de `52px` e valores em `px`/hex
  direto (classes arbitrárias do Tailwind). É intencional. O fundo do painel verde usa as variáveis
  do menu (`bg-menu` e `--cor-menu-luz`, com o gradiente vindo do canto oposto ao do menu); o verde
  principal já usa `primaria`. As outras telas de acesso (esqueci a senha, definir senha)
  usam a moldura `TelaAcesso.jsx`, só com tokens.
- Não há tema escuro (`color-scheme: light`). Se for criado, ele deve sair só da troca das
  variáveis de `:root`.
