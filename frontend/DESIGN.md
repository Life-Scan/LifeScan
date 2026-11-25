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

- **Painel:** faixa de destaque no topo, com o gradiente do login
  (`radial-gradient(ellipse at 100% 100%, #218c7b 0, transparent 65%), #0b514d`), texto claro,
  saudação, data de hoje e o resumo do dia ("3 consultas hoje · 2 solicitações vencidas"). A
  linha de batimento do login entra como detalhe decorativo à direita, com `aria-hidden`. Raio
  `--raio-grande` (`20px`).
- **Demais telas:** `.sobretitulo` acima do `h1` (o nome da área: "Pacientes", "Agenda"),
  `h1` maior e subtítulo em texto suave. Sem faixa escura: ela é exclusiva do Painel e do
  cabeçalho do acompanhamento.
- `.sobretitulo`: `0.72rem`, peso `700`, caixa alta, `letter-spacing: 0.12em`,
  cor `--cor-primaria`. É o mesmo padrão já usado no login.

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

| Variável | Valor atual | Valor novo |
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
| 1. Menu lateral escuro | Planejado |
| 2. Cabeçalho com presença | Planejado |
| 3. Tipografia | Planejado |
| 4. Fundo e profundidade | Planejado |
| 5. Cor por tipo de informação | Planejado (já existe só na linha do tempo) |
| 6. Agenda visual | Planejado |
| 7. Acabamento | Planejado |

Ordem sugerida: 1 a 4 primeiro (mudam o sistema inteiro quase só com `index.css` e
`Layout`), depois 5 a 7, tela por tela.

## Tailwind e shadcn/ui

O projeto está migrando de CSS Modules para Tailwind v4 + shadcn/ui, componente por componente. Os
dois convivem: ao migrar um componente, apague o `.module.css` dele.

- **Tokens:** as variáveis de `:root` continuam sendo a fonte da verdade. O `@theme inline` de
  `index.css` gera classes com o nome delas (`bg-primaria`, `text-texto-suave`, `border-borda`,
  `rounded-raio`, `shadow-sombra`) e aponta as variáveis do shadcn (`--primary`, `--border`,
  `--muted-foreground`...) para elas. Não use a paleta padrão do Tailwind (`bg-teal-700`).
- **Componentes do shadcn:** `npx shadcn@latest add <nome>`. Vão para `src/components/ui/`
  (pasta) e não se confundem com `src/components/ui.jsx` (arquivo, componentes próprios), mas
  importe sempre pelo caminho completo: `@/components/ui/button`.
- **Estilos globais em `@layer base`:** as classes do Tailwind vencem as regras de `index.css`
  (`button`, `input`, `label`, `h1`...), e os `.module.css`, fora de camada, vencem tudo. A ordem
  das camadas está declarada no topo de `index.css`.
- **Migrados:** `ui.jsx` (o antigo `ui.module.css`), `Confirmacao.jsx`, as telas de acesso
  (`TelaAcesso.jsx`, no lugar do antigo `Auth.module.css`) e o `Login.jsx`.
- **Pontos de quebra:** use `ate-900:`, `ate-860:` e `ate-680:` (definidos em `index.css`, com
  `width <= N`, iguais ao `max-width` dos módulos). O `max-[900px]:` do Tailwind usa `width < 900px`
  e muda o layout com 1px de diferença.
- **Sem preflight por enquanto:** o reset do Tailwind não está ligado, porque as telas em CSS
  Modules dependem dos padrões do navegador (`dl`, `fieldset`, listas, `dialog`). As regras
  globais de formulário e foco de `index.css` deixam de fora os elementos com `data-slot` (todos
  os componentes do shadcn têm), e a base do shadcn vale só para eles. Quando a migração terminar,
  ligue o preflight.
- Classes condicionais com `cn()` (`@/lib/utils`).

## Tokens

Valores **atuais** do código. Os novos estão em [Direção visual](#direção-visual) e substituem
estes à medida que forem implantados.

Todos ficam em `:root`, em `src/index.css`. **Não use cores em hexadecimal nos módulos**. Use as
variáveis. Se faltar uma, crie a variável em `index.css` primeiro.

### Cores

| Variável | Valor | Uso |
|---|---|---|
| `--cor-fundo` | `#f3f5f7` | Fundo da página |
| `--cor-superficie` | `#ffffff` | Cartões, menu, campos, diálogos |
| `--cor-superficie-suave` | `#f7f9fa` | Hover de itens neutros, estado vazio, campos desabilitados |
| `--cor-borda` | `#e2e7eb` | Bordas de cartões, listas, divisórias |
| `--cor-borda-forte` | `#cfd6dc` | Bordas de campos e botões secundários |
| `--cor-texto` | `#17212b` | Texto principal |
| `--cor-texto-suave` | `#5d6b78` | Metadados, ajuda, rótulos secundários |
| `--cor-primaria` | `#0f766e` | Marca, botão principal, links, foco |
| `--cor-primaria-escura` | `#0b5d57` | Hover do primário, texto sobre `--cor-primaria-clara` |
| `--cor-primaria-clara` | `#e2f3f0` | Item de menu ativo, seleção, anel de foco dos campos |

Cores de estado: cada uma tem o tom forte (texto e ícone) e o `-clara` (fundo).

| Estado | Forte | Clara | Significado |
|---|---|---|---|
| `perigo` | `#b42318` | `#fdecea` | Erro, vencido, falta, ação destrutiva |
| `alerta` | `#93610a` | `#fff3d4` | Pendente, aguardando revisão, vence em breve |
| `sucesso` | `#1a7340` | `#e3f4e9` | Atendida, realizada, revisado, ativo |
| `info` | `#1d5fa8` | `#e5effb` | Agendada, categoria, informação neutra relevante |

Use sempre o par: texto `--cor-x` sobre fundo `--cor-x-clara`. O contraste já foi pensado para
essa combinação.

### Tipografia

- Fonte: `--fonte` (Segoe UI Variable / system-ui). Não carregamos fontes externas.
- Corpo: `15px`, `line-height: 1.5`.
- Títulos com peso `650` e `letter-spacing: -0.01em`:
  - `h1` `1.6rem` (`1.35rem` abaixo de 720px), título da página. Um por tela.
  - `h2` `1.1rem`, título de cartão ou seção.
  - `h3` `0.98rem`, subtítulo dentro de cartão.
- Escala de texto menor, em `rem`: `0.92` (botões, alertas), `0.86` (rótulos, ajuda),
  `0.84` (metadados), `0.76` (etiquetas).
- Pesos usados: `400`, `600` (rótulos, botões, nomes), `650` (títulos), `700` (números de
  resumo, avatar).

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
| `--raio` | `12px` | Cartões, resumos, diálogos |
| `--raio-pequeno` | `8px` | Botões, campos, itens de lista, alertas |
| `999px` | — | Pílulas: etiquetas, filtros, contadores |
| `--sombra` | sutil | Cartões e resumos |
| `--sombra-elevada` | forte | Só para o que flutua (diálogos) |

## Layout

- `Layout.jsx`: menu lateral fixo de `--largura-menu` (248px). **Abaixo de 900px** vira barra no
  topo, com a navegação rolando na horizontal.
- O conteúdo fica centralizado com `max-width: 1040px` (`.miolo`).
- Estrutura de página (`Paginas.module.css`):
  - `.cabecalho`: `h1` + `.subtitulo` à esquerda, ação principal à direita.
  - `.pilha`: cartões empilhados com `1.25rem` entre eles.
  - `.grade`: cartões lado a lado, com no mínimo 280px cada.
  - `.resumos` / `.resumo`: números do painel. O tom (`resumo_perigo`, `_alerta`, `_info`) só é
    aplicado quando o número é maior que zero.
- Breakpoints usados: `900px` (menu), `860px` (linha com ações empilha), `720px` (tamanho do
  `h1`), `680px` (login em uma coluna). Prefira `auto-fit`/`minmax` a criar breakpoints novos.

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

Padrões do acompanhamento (`Acompanhamento.module.css`):

- **Abas** (`.aba`, `.abaAtiva`): sublinhado primário; `.contador` em tom de alerta para pendências.
  A aba ativa fica na URL (`?aba=`).
- **Filtros** (`.filtro`, `.filtroAtivo`): pílulas; a ativa usa `--cor-primaria-clara`.
- **Linha do tempo**: ícone redondo por tipo: consulta → primária, solicitação → alerta,
  documento → info.

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

1. Comece por `ui.jsx` e `Paginas.module.css`. Só crie classe nova em módulo
   da página quando o padrão não existir.
2. Uma peça usada em duas ou mais páginas deve ir para o `estilos` de `ui.jsx` (e, se tiver lógica,
   virar componente lá).
3. Cores, raios e sombras só por variável. Espaçamento pelos passos da tabela.
4. Confira em tela larga e abaixo de 900px. Veja a tela de verdade, não só o `npm run build`.

## Exceções conhecidas

- **Login** (`Login.jsx`) tem visual próprio de "porta de entrada": painel de apresentação
  verde-escuro com gradiente, caixa de `28px` de raio, campos de `52px` e valores em `px`/hex
  direto (classes arbitrárias do Tailwind). É intencional. Os hex do painel verde (`#0b514d`,
  `#218c7b`) viram variáveis com o item 1 da Direção visual (`--cor-menu`, `--gradiente-menu`); o
  verde principal já usa `primaria`. As outras telas de acesso (esqueci a senha, definir senha)
  usam a moldura `TelaAcesso.jsx`, só com tokens.
- Alguns tons derivados estão em hex dentro de `ui.jsx` (bordas dos alertas, hover do
  `botaoPerigoSolido`, fundo e borda do `itemListaDestaque`, ícone do estado vazio) e no
  placeholder de `index.css` (`#94a0ab`). São candidatos a
  virar variáveis.
- Não há tema escuro (`color-scheme: light`). Se for criado, ele deve sair só da troca das
  variáveis de `:root`.
