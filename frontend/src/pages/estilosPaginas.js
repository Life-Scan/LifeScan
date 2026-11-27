/*
 * Classes compartilhadas pelas páginas internas (antes em Paginas.module.css). Uso: className={estilos.pilha}.
 * Peças usadas em vários lugares do app ficam em components/ui.jsx; aqui fica o que é de página.
 */

// Botão de opção (paciente ou parceiro) ao criar um usuário: o input fica escondido dentro do rótulo
const OPCAO =
  'm-0 grid cursor-pointer gap-[0.1rem] rounded-raio-pequeno border px-[0.85rem] py-[0.7rem] ' +
  '[&_input]:pointer-events-none [&_input]:absolute [&_input]:opacity-0 ' +
  'has-[input:focus-visible]:outline-2 has-[input:focus-visible]:outline-offset-2 has-[input:focus-visible]:outline-primaria'

export const estilos = {
  cabecalho: 'mb-5 flex flex-wrap items-end justify-between gap-4',
  subtitulo: 'mt-1 text-texto-suave',
  pilha: 'grid gap-5',
  grade: 'grid grid-cols-[repeat(auto-fit,minmax(280px,1fr))] items-start gap-5',

  // Faixa do Painel: data, saudação, frase com o que pede atenção e os resumos
  faixaTopo: 'flex flex-wrap items-end justify-between gap-3',
  tituloFaixa: 'mt-[0.35rem] text-[2rem] leading-[1.15] tracking-[-0.03em] ate-720:text-[1.6rem]',
  subtituloFaixa: 'mt-[0.35rem] text-menu-texto',
  atualizacaoFaixa: 'text-[0.8rem] text-menu-texto',

  /*
   * Resumos do Painel, dentro da faixa: botões que abrem a gaveta com a lista; cor do ícone em
   * tonsResumo. Uma coluna por resumo (--colunas, inline), numa linha só; até 720px empilham.
   */
  resumos: 'grid grid-cols-[repeat(var(--colunas),minmax(0,1fr))] gap-3 ate-720:grid-cols-1',
  resumo:
    'relative flex w-full cursor-pointer items-center gap-[0.85rem] rounded-raio border border-menu-borda bg-menu-hover ' +
    'px-[1.1rem] py-[0.9rem] text-left text-menu-texto-forte transition-[background,border-color,translate] ' +
    'duration-150 ease-[ease] hover:bg-menu-ativo not-aria-expanded:hover:-translate-y-px ' +
    // Aberto: mesma cor opaca e mesma borda da gaveta, que aponta para ele com a seta (a do cartão gira)
    'aria-expanded:border-menu-destaque/40 aria-expanded:bg-faixa-aberta',
  resumoSeta: 'ml-auto self-start text-menu-texto transition-transform duration-200 ease-out',
  resumoSetaAberta: 'rotate-180',

  /*
   * Gaveta dos resumos (Progressive Disclosure, em forma de dropdown): flutua logo abaixo dos
   * resumos, por cima do conteúdo, sem esticar a faixa. Abre animando a altura de 0fr a 1fr, com
   * fade. Mesma cor do resumo aberto, com uma seta no topo apontando para ele, que desliza quando
   * outro resumo é aberto. A moldura fica; só o conteúdo troca, com fade + 4px, e os itens entram em
   * sequência. prefers-reduced-motion já zera as durações.
   */
  areaResumo: 'relative',
  gaveta:
    'pointer-events-none absolute inset-x-0 top-full z-20 grid grid-rows-[0fr] opacity-0 ' +
    'transition-[grid-template-rows,opacity] duration-300 ease-[cubic-bezier(0.22,1,0.36,1)]',
  gavetaAberta: 'pointer-events-auto grid-rows-[1fr] opacity-100',
  // Margem em volta para a sombra não ser cortada pelo overflow da animação (a moldura mantém a largura do resumo)
  gavetaJanela: 'min-h-0 overflow-hidden -mx-6 px-6 pb-8',
  gavetaMoldura:
    'relative mt-[0.85rem] rounded-raio border border-menu-destaque/40 bg-faixa-aberta shadow-sombra-elevada',
  // Losango girado no centro do topo: só as bordas de cima e da esquerda aparecem, formando a ponta
  gavetaSeta:
    'pointer-events-none absolute -top-[7px] left-1/2 size-3.5 -translate-x-1/2 rotate-45 border-t border-l ' +
    'border-menu-destaque/40 bg-faixa-aberta',
  // Lista longa rola por dentro da gaveta, sem esticar a página
  gavetaConteudo:
    'grid max-h-[min(60vh,520px)] gap-3 overflow-y-auto overscroll-contain p-4 ' +
    'animate-in fade-in slide-in-from-top-1 duration-200',
  gavetaCabecalho: 'flex items-center gap-[0.65rem]',
  gavetaIcone: 'grid size-8 place-items-center rounded-[8px]',
  gavetaTitulo: 'min-w-0 text-[0.98rem] text-menu-texto-forte',
  gavetaQuantidade:
    'inline-grid h-6 min-w-6 place-items-center rounded-full bg-menu-ativo px-[0.45rem] text-[0.8rem] ' +
    'font-semibold text-menu-texto-forte tabular-nums',

  // Lista dentro da gaveta: itens translúcidos sobre o verde, um embaixo do outro
  listaGaveta: 'm-0 grid list-none gap-[0.6rem] p-0',
  itemGaveta:
    'rounded-raio-pequeno border border-menu-borda bg-menu-hover px-4 py-[0.8rem] transition-[background] duration-150 ' +
    'hover:bg-menu-ativo animate-in fade-in slide-in-from-top-1 duration-300 fill-mode-backwards',
  // Vencido: filete vermelho-claro à esquerda (o estado também vem escrito na etiqueta)
  itemGavetaDestaque:
    'rounded-raio-pequeno border border-menu-borda border-l-3 border-l-perigo-borda bg-menu-hover px-4 py-[0.8rem] ' +
    'transition-[background] duration-150 hover:bg-menu-ativo animate-in fade-in slide-in-from-top-1 duration-300 ' +
    'fill-mode-backwards',
  linkGaveta:
    'font-semibold text-menu-texto-forte no-underline hover:underline hover:underline-offset-2',
  textoGaveta: 'mt-[0.35rem] whitespace-pre-wrap text-menu-texto [word-break:break-word]',
  metaGaveta: 'tabular-nums mt-[0.3rem] flex flex-wrap gap-x-[0.9rem] gap-y-[0.2rem] text-[0.84rem] text-menu-texto',
  vazioGaveta:
    'flex items-center gap-[0.6rem] rounded-raio-pequeno border border-dashed border-menu-borda px-4 py-[0.9rem] ' +
    'text-menu-texto [&_a]:text-menu-texto-forte',
  resumoIcone: 'grid size-[2.6rem] place-items-center rounded-[10px]',
  resumoNumero: 'block text-[2rem] leading-[1.1] font-[750] tracking-[-0.03em] tabular-nums',
  resumoRotulo: 'block text-[0.86rem] text-menu-texto',

  meta: 'tabular-nums mt-[0.3rem] flex flex-wrap gap-x-[0.9rem] gap-y-[0.2rem] text-[0.84rem] text-texto-suave',
  textoItem: 'mt-[0.35rem] whitespace-pre-wrap [word-break:break-word]',
  linkItem: 'font-semibold text-texto no-underline hover:text-primaria hover:underline',
  atualizacao: 'text-[0.8rem] text-texto-suave',
  camposEdicao: 'm-0 grid min-w-0 gap-[0.9rem] border-0 p-0',
  opcaoCheck: 'inline-flex cursor-pointer items-center gap-2 text-[0.85rem] [&_input]:accent-primaria',

  // Cabeçalho da lista de contas: abas, busca e botão de recolher. Some a borda quando a lista está recolhida.
  cabecalhoContas:
    'mb-4 flex items-center justify-between gap-2 border-b border-borda pb-[0.65rem] ' +
    'ate-760:flex-wrap ate-760:[&_.abas-pacientes]:flex-1 ' +
    '[&:has(+[hidden])]:mb-0 [&:has(+[hidden])]:border-b-0 [&:has(+[hidden])]:pb-0',
  buscaContas:
    'relative ml-auto min-w-[200px] max-w-[390px] flex-1 [&_input]:w-full [&_input]:pr-[2.75rem] ' +
    'ate-760:order-1 ate-760:basis-full ate-760:min-w-0 ate-760:max-w-none',
  iconeBuscaContas: 'pointer-events-none absolute top-1/2 right-[0.85rem] -translate-y-1/2 text-primaria',
  // abas-pacientes não tem estilo: marca o grupo para o cabecalhoContas encontrá-lo
  abasPacientes: 'abas-pacientes flex min-w-0 flex-wrap gap-2',
  abaPacientes:
    'inline-flex cursor-pointer items-center gap-2 rounded-raio-pequeno border border-transparent bg-transparent ' +
    'px-3 py-[0.55rem] font-semibold text-texto-suave hover:bg-primaria-clara hover:text-primaria ' +
    'aria-selected:border-primaria aria-selected:bg-primaria-clara aria-selected:text-primaria',
  recolherContas:
    'inline-flex size-[2.75rem] shrink-0 cursor-pointer items-center justify-center rounded-raio-pequeno border ' +
    'border-borda bg-superficie text-primaria hover:bg-primaria-clara',
  contagem:
    'ml-1 inline-grid h-6 min-w-6 place-items-center rounded-full border border-borda bg-superficie-suave ' +
    'px-[0.4rem] align-middle text-[0.8rem] font-semibold text-texto-suave tabular-nums',

  escolha:
    'm-0 grid max-w-[780px] grid-cols-[repeat(auto-fit,minmax(180px,1fr))] gap-[0.6rem] border-0 p-0 ' +
    '[&_legend]:mb-[0.3rem] [&_legend]:p-0 [&_legend]:text-[0.9rem] [&_legend]:font-medium',
  // Clicável: sobe 1px com a sombra de hover; a selecionada fica parada
  opcao: `${OPCAO} border-borda transition-[border-color,box-shadow,translate] duration-150 ease-saida hover:-translate-y-px hover:border-primaria hover:shadow-sombra-hover`,
  opcaoSelecionada: `${OPCAO} border-primaria bg-primaria-clara shadow-[0_0_0_1px_var(--cor-primaria)]`,
  opcaoRotulo: 'font-semibold',
  opcaoDescricao: 'text-[0.82rem] font-normal text-texto-suave',

  // Lista da agenda, abaixo das abas
  painelAgenda: 'mt-4',
}

/** Cor do ícone do resumo do Painel: sempre colorido, para identificar o tipo mesmo com zero. */
/** Cor do ícone do resumo pelo tipo (DESIGN.md, item 5). Vencida tem prioridade sobre o tipo. */
export const tonsResumo = {
  consulta: 'bg-consulta-clara text-consulta',
  solicitacao: 'bg-solicitacao-clara text-solicitacao',
  documento: 'bg-documento-clara text-documento',
  vencida: 'bg-perigo-clara text-perigo',
}
