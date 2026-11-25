# LifeScan: sistema visual

Guia para escrever e revisar telas do frontend. Descreve o que **já existe** no código: as
variáveis de `src/index.css`, as peças de `src/components/ui.module.css` e `ui.jsx` e os padrões
das páginas. Quem criar uma tela nova (pessoa ou agente de IA) deve seguir este guia. Antes de
criar um estilo novo, reaproveite um existente. Se o código e este arquivo divergirem, corrija
um dos dois no mesmo PR.

## Princípios

- **Clínico e calmo.** Fundo cinza bem claro, superfícies brancas, uma única cor de marca
  (verde-azulado). A cor serve para informar estado, não para decorar.
- **Densidade de ferramenta de trabalho.** O médico usa o sistema todos os dias: listas
  compactas, informação secundária em texto suave, ações sempre à vista.
- **Estado sempre com texto.** Cor nunca é o único sinal: etiquetas e alertas têm rótulo e,
  quando cabe, ícone.
- **Português em tudo**, inclusive nomes de classes CSS, variáveis e textos da interface.

## Tokens

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
  `h1`). Prefira `auto-fit`/`minmax` a criar breakpoints novos.

## Componentes

Importe de `src/components/ui.jsx` (`estilos` também é exportado de lá). Não recrie essas peças
em módulos de página.

| Peça | Como usar | Observações |
|---|---|---|
| Cartão | `estilos.cartao` + `estilos.cartaoCabecalho` | Container padrão de qualquer seção |
| Botão primário | `estilos.botao` | Uma ação principal por área |
| Botão secundário | `estilos.botaoSecundario` | Cancelar, voltar, ações neutras |
| Botão de perigo | `estilos.botaoPerigo` (contorno) / `botaoPerigoSolido` | O sólido só aparece no diálogo de confirmação |
| Botão pequeno | some `estilos.botaoPequeno` a qualquer botão | Ações dentro de itens de lista |
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

1. Comece por `ui.jsx` / `ui.module.css` e `Paginas.module.css`. Só crie classe nova em módulo
   da página quando o padrão não existir.
2. Uma peça usada em duas ou mais páginas deve ir para `ui.module.css` (e, se tiver lógica, para
   `ui.jsx`).
3. Cores, raios e sombras só por variável. Espaçamento pelos passos da tabela.
4. Confira em tela larga e abaixo de 900px. Veja a tela de verdade, não só o `npm run build`.

## Exceções conhecidas

- **Login e telas de acesso** (`Login.module.css`, `Auth.module.css`) têm visual próprio de
  "porta de entrada": painel de apresentação verde-escuro com gradiente, caixa de `28px` de
  raio, campos de `52px` e valores em `px`/hex direto. É intencional, mas os hex repetem tons da
  marca (`#0f766e`, `#0b5d57`); ao mexer nesses arquivos, troque-os pelas variáveis.
- `.miniaturaTexto` usa `var(--fonte-mono, monospace)`, mas `--fonte-mono` não está definida.
  Hoje cai no `monospace` do navegador.
- Alguns tons derivados estão em hex dentro de `ui.module.css` (bordas dos alertas, hover do
  `botaoPerigoSolido`, fundo do `itemListaDestaque`, placeholder `#94a0ab`). São candidatos a
  virar variáveis.
- Não há tema escuro (`color-scheme: light`). Se for criado, ele deve sair só da troca das
  variáveis de `:root`.
