/*
 * Classes da página do acompanhamento e das abas (antes em Acompanhamento.module.css).
 * Uso: className={estilos.pilha}. Variantes com estado (aba ativa, filtro ativo, etapa do passo,
 * tipo de evento) têm a string inteira em cada estado, sem depender da ordem das classes.
 */

const TEXTO_LONGO = 'whitespace-pre-wrap [word-break:break-word]'

const ABA =
  'inline-flex cursor-pointer items-center gap-[0.4rem] -mb-px border-0 border-b-2 bg-transparent ' +
  'px-[0.9rem] py-[0.65rem] text-[0.92rem] font-semibold whitespace-nowrap hover:text-texto'

const FILTRO =
  'inline-flex cursor-pointer items-center gap-[0.35rem] rounded-full border px-3 py-[0.3rem] ' +
  'text-[0.84rem] font-semibold hover:text-texto'

export const estilos = {
  pilha: 'grid gap-4',
  voltar:
    'inline-flex w-fit items-center gap-[0.3rem] text-[0.88rem] font-semibold text-texto-suave no-underline ' +
    'hover:text-primaria',
  texto: `mt-[0.35rem] ${TEXTO_LONGO}`,
  meta: 'mt-[0.3rem] flex flex-wrap gap-x-[0.9rem] gap-y-[0.2rem] text-[0.84rem] text-texto-suave',
  acoesItem: 'mt-[0.65rem]',
  formularioDestaque: 'rounded-raio-pequeno border border-borda-forte bg-superficie-suave p-[1.1rem]',

  // Cabeçalho
  cabecalho: 'grid gap-[1.1rem] ate-720:[&_h1]:text-[1.3rem]',
  cabecalhoTopo: 'flex flex-wrap items-start justify-between gap-4',
  // Até 720px some o avatar (primeiro filho)
  identificacao: 'flex min-w-0 gap-[0.9rem] ate-720:[&>:first-child]:hidden',
  tituloLinha: 'flex flex-wrap items-center gap-[0.6rem]',
  pessoas:
    'mt-[0.3rem] flex flex-wrap gap-x-[1.1rem] gap-y-[0.2rem] text-[0.88rem] text-texto-suave ' +
    '[&_strong]:font-semibold [&_strong]:text-texto',
  descricao: 'mt-[0.6rem] max-w-[72ch] text-texto-suave',

  // Passo atual: três etapas em linha, ligadas por um traço (ver passos abaixo)
  passoLinha: 'flex flex-wrap items-center gap-[0.9rem] border-t border-borda pt-4',
  rotuloPasso: 'text-[0.8rem] font-semibold tracking-[0.04em] text-texto-suave uppercase',
  passos: 'm-0 flex list-none flex-wrap items-center p-0 ate-720:flex-nowrap',

  // Abas
  abas: 'flex gap-[0.15rem] overflow-x-auto border-b border-borda [scrollbar-width:thin]',
  aba: `${ABA} border-transparent text-texto-suave`,
  abaAtiva: `${ABA} border-b-primaria text-primaria-escura`,
  contador:
    'inline-grid h-[1.3rem] min-w-[1.3rem] place-items-center rounded-full bg-alerta-clara px-[0.3rem] ' +
    'text-[0.74rem] font-bold text-alerta',

  // Filtros em forma de pílula (linha do tempo e documentos)
  filtros: 'flex flex-wrap gap-[0.4rem]',
  filtro: `${FILTRO} border-borda-forte bg-superficie text-texto-suave`,
  filtroAtivo: `${FILTRO} border-primaria bg-primaria-clara text-primaria-escura`,

  // Linha do tempo: o traço vertical fica atrás dos ícones
  linhaDoTempo:
    "relative m-0 list-none p-0 before:absolute before:top-3 before:bottom-3 before:left-[1.05rem] before:w-[2px] before:bg-borda before:content-['']",
  evento: 'relative flex gap-[0.85rem] py-[0.6rem]',
  // O contorno branco "corta" a linha vertical atrás do ícone; a cor vem de iconesEvento
  iconeEvento:
    'relative z-[1] grid size-[2.15rem] shrink-0 place-items-center rounded-full shadow-[0_0_0_4px_var(--cor-superficie)]',
  corpoEvento: 'min-w-0 flex-1 pt-[0.2rem]',
  topoEvento: 'flex flex-wrap items-center gap-2',
  tituloEvento:
    'cursor-pointer border-0 bg-transparent p-0 text-left font-[650] hover:text-primaria hover:underline hover:underline-offset-2',
  dataEvento: 'ml-auto text-[0.82rem] whitespace-nowrap text-texto-suave ate-720:ml-0 ate-720:basis-full',
  textoEvento: `mt-[0.2rem] ${TEXTO_LONGO}`,

  // Consultas
  prescricoes:
    // Borda de um lado só pelo atalho: sem o preflight, border-dashed tracejaria os quatro lados com 3px
    'mt-3 [border-top:1px_dashed_var(--cor-borda)] pt-[0.6rem] [&_h3]:mb-[0.3rem] [&_h3]:text-[0.86rem] ' +
    '[&_ul]:m-0 [&_ul]:grid [&_ul]:gap-[0.35rem] [&_ul]:pl-[1.1rem]',
  grupoPrescricoes:
    'm-0 grid justify-items-start gap-3 rounded-raio-pequeno border border-borda bg-superficie px-[0.9rem] pt-3 pb-[0.9rem] ' +
    '[&_legend]:px-[0.3rem] [&_legend]:py-0 [&_legend]:text-[0.86rem] [&_legend]:font-semibold',
  linhaPrescricao:
    'grid w-full grid-cols-[2fr_1fr_2fr_auto] [align-items:end] gap-[0.6rem] ' +
    'ate-720:grid-cols-[1fr] ate-720:[border-bottom:1px_dashed_var(--cor-borda)] ate-720:pb-3',

  // Documentos
  revisao:
    'mt-[0.7rem] rounded-r-raio-pequeno border-l-3 border-sucesso bg-sucesso-clara px-[0.8rem] py-[0.6rem] text-[0.92rem]',

  // Anamnese do paciente
  anamneseBasicos: 'm-0 grid grid-cols-[repeat(auto-fit,minmax(140px,1fr))] gap-[0.6rem]',
  anamneseTextos: 'm-0 grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-[0.6rem]',
  anamneseItem: 'rounded-raio-pequeno border border-borda bg-superficie-suave px-[0.85rem] py-[0.7rem]',
  anamneseRotulo: 'text-[0.74rem] font-semibold tracking-[0.04em] text-texto-suave uppercase',
  anamneseValor: 'mx-0 mt-[0.15rem] mb-0 font-semibold',
  anamneseValorTexto: `mx-0 mt-[0.15rem] mb-0 font-normal ${TEXTO_LONGO}`,
}

/** Cor do ícone de cada tipo de evento da linha do tempo. */
export const iconesEvento = {
  consulta: 'bg-primaria-clara text-primaria-escura',
  solicitacao: 'bg-alerta-clara text-alerta',
  documento: 'bg-info-clara text-info',
}

/*
 * Etapas do passo atual. Cada etapa tem um estado (pendente, concluido, atual) que define as cores do
 * botão e do número. O traço antes da etapa fica verde quando a anterior já foi concluída.
 */
const BOTAO_PASSO =
  'inline-flex items-center gap-[0.45rem] rounded-full border py-[0.3rem] pr-[0.8rem] pl-[0.35rem] text-[0.88rem] font-semibold ' +
  'ate-720:gap-[0.3rem] ate-720:py-[0.25rem] ate-720:pr-[0.6rem] ate-720:pl-[0.3rem] ate-720:text-[0.8rem]'
const NUMERO_PASSO =
  'inline-grid size-[1.4rem] shrink-0 place-items-center rounded-full border text-[0.74rem] ate-720:size-[1.25rem]'
// Só quando a etapa é um botão (quem pode mudar o passo)
const BOTAO_PASSO_CLICAVEL = 'cursor-pointer transition-[border-color,background] duration-150 ease-[ease]'
const HOVER_PASSO = 'hover:not-disabled:border-primaria hover:not-disabled:text-primaria-escura'

export const passo = {
  item: 'flex items-center',
  traco: "before:h-[2px] before:w-[1.75rem] before:content-[''] ate-720:before:w-3",
  tracoCor: { feito: 'before:bg-primaria', pendente: 'before:bg-borda-forte' },
  botao: {
    pendente: `${BOTAO_PASSO} border-borda-forte bg-superficie text-texto-suave`,
    concluido: `${BOTAO_PASSO} border-primaria bg-superficie text-primaria-escura`,
    atual: `${BOTAO_PASSO} border-primaria bg-primaria text-white`,
  },
  clicavel: { pendente: `${BOTAO_PASSO_CLICAVEL} ${HOVER_PASSO}`, concluido: `${BOTAO_PASSO_CLICAVEL} ${HOVER_PASSO}`, atual: BOTAO_PASSO_CLICAVEL },
  numero: {
    pendente: `${NUMERO_PASSO} border-borda-forte bg-superficie-suave`,
    concluido: `${NUMERO_PASSO} border-transparent bg-primaria-clara text-primaria-escura`,
    atual: `${NUMERO_PASSO} border-white bg-white text-primaria-escura`,
  },
}
