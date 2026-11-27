/*
 * Classes da agenda de consultas: calendário mensal, alternador calendário/lista e modal de
 * compromissos do dia (antes em AgendaConsultas.module.css). Uso: className={agendaEstilos.gradeDias}.
 */

const BOTAO_MODO =
  'inline-flex cursor-pointer items-center gap-[0.35rem] rounded-[6px] border-0 px-[0.65rem] py-[0.32rem] ' +
  'text-[0.84rem] font-semibold transition-[background,color] duration-150 ease-[ease] hover:text-texto'

const CHIP_EVENTO = {
  agendada: 'bg-info-clara text-info',
  atrasada: 'bg-alerta-clara text-alerta',
  realizada: 'bg-sucesso-clara text-sucesso',
  faltou: 'bg-perigo-clara text-perigo',
  cancelada: 'bg-superficie-suave text-texto-suave line-through',
}

export const agendaEstilos = {
  // Controles no cabeçalho da agenda
  cabecalhoControles: 'flex flex-wrap items-center gap-2',
  alternadorModo: 'inline-flex gap-[0.15rem] rounded-raio-pequeno border border-borda bg-superficie-suave p-[0.2rem]',
  // O hover muda a cor do texto também no botão ativo (como no CSS original)
  botaoModo: `${BOTAO_MODO} bg-transparent text-texto-suave`,
  botaoModoAtivo: `${BOTAO_MODO} bg-superficie text-primaria-escura shadow-sombra`,

  // Barra de navegação do calendário
  calendarioTopo: 'mb-[0.9rem] flex flex-wrap items-center justify-between gap-3',
  mesTitulo: 'text-[1.05rem] font-[650] text-texto capitalize',
  navegacaoMes: 'flex items-center gap-[0.35rem]',

  // Grade mensal (as células usam classesCelulaDia)
  gradeSemana: 'mb-[0.35rem] grid grid-cols-[repeat(7,minmax(0,1fr))] gap-[0.35rem]',
  diaSemana: 'py-1 text-center text-[0.78rem] font-[650] tracking-[0.03em] text-texto-suave uppercase',
  gradeDias: 'grid grid-cols-[repeat(7,minmax(0,1fr))] gap-[0.35rem]',
  cabecalhoDia: 'flex items-center justify-between gap-1',
  numeroDia: 'text-[0.84rem] leading-[1.2] font-[650] tabular-nums',
  numeroDiaHoje:
    'inline-flex h-[1.45rem] min-w-[1.45rem] items-center justify-center rounded-full bg-primaria px-1 text-white',
  contagemEventos:
    'rounded-full bg-primaria-clara px-[0.38rem] py-[0.05rem] text-[0.7rem] font-bold text-primaria-escura tabular-nums',
  listaEventosDia: 'flex min-w-0 flex-col gap-[0.2rem]',
  eventoChip:
    'flex items-center gap-1 overflow-hidden rounded-[5px] px-[0.35rem] py-[0.12rem] text-[0.72rem] leading-[1.25] ' +
    'font-semibold text-ellipsis whitespace-nowrap',
  // Cor do evento por status; "atrasada" é a agendada cujo horário já passou
  evento_agendada: CHIP_EVENTO.agendada,
  evento_atrasada: CHIP_EVENTO.atrasada,
  evento_realizada: CHIP_EVENTO.realizada,
  evento_faltou: CHIP_EVENTO.faltou,
  evento_cancelada: CHIP_EVENTO.cancelada,
  eventoHora: 'shrink-0 tabular-nums',
  // Até 720px a célula mostra só o horário
  eventoNome: 'overflow-hidden text-ellipsis ate-720:hidden',
  maisEventos: 'pl-[0.2rem] text-[0.7rem] font-semibold text-primaria-escura',

  legenda:
    'mt-[0.85rem] flex flex-wrap gap-3 border-t border-borda pt-3 text-[0.78rem] text-texto-suave',
  legendaItem: 'inline-flex items-center gap-[0.35rem]',
  legendaCor: 'size-[10px] rounded-[3px]',

  // Janela da agenda do dia (ModalAgendaDia). dvh: no celular, a barra do navegador não corta o rodapé.
  modalDia:
    'max-h-[calc(100dvh-2rem)] w-[min(760px,calc(100vw-2rem))] rounded-raio border-0 bg-superficie p-0 text-texto ' +
    'shadow-sombra-elevada dialogo-animado',
  modalConteudo: 'flex max-h-[calc(100dvh-2rem)] flex-col',
  modalCabecalho:
    'flex flex-wrap items-start justify-between gap-x-4 gap-y-3 border-b border-borda px-[1.35rem] pt-[1.1rem] pb-4 ' +
    'ate-720:px-4',
  modalTitulo: 'flex flex-wrap items-center gap-2 text-[1.25rem] leading-tight outline-none',
  modalResumo: 'mt-1 text-[0.88rem] text-texto-suave tabular-nums',
  modalNavegacao: 'flex items-center gap-2 ate-720:w-full ate-720:justify-between',
  // Botão só com ícone (anterior, próximo, fechar): 36px, com o nome em aria-label
  botaoIcone:
    'inline-flex size-9 shrink-0 cursor-pointer items-center justify-center rounded-raio-pequeno border border-borda ' +
    'bg-superficie text-texto-suave transition-[background,color,scale] duration-150 ease-saida ' +
    'hover:bg-superficie-suave hover:text-texto active:scale-[0.97] focus-visible:outline-2 focus-visible:outline-offset-2 ' +
    'focus-visible:outline-primaria',
  modalCorpo: 'min-h-[12rem] overflow-y-auto overscroll-contain px-[1.35rem] py-4 ate-720:px-4',
  modalRodape:
    'flex flex-wrap justify-end gap-2 border-t border-borda bg-superficie-suave px-[1.35rem] py-[0.9rem] ' +
    'ate-720:px-4 ate-720:[&>button]:flex-1',

  // Grade do dia: hora à esquerda (4rem) e a célula com o conteúdo da meia hora
  linhaGrade: 'grid grid-cols-[4rem_minmax(0,1fr)] ate-720:grid-cols-[3.4rem_minmax(0,1fr)]',
  rotuloHora: 'pt-1 pr-3 text-right text-[0.75rem] leading-none tabular-nums',
  // border-0 antes do border-t: sem o preflight, um border-dashed daria borda nos quatro lados
  celula: 'min-h-10 border-0 border-t',
  faixaCelula: 'flex items-center rounded-[6px] px-3 text-[0.8rem]',
  // Indisponível: listras diagonais discretas (horário bloqueado pelo intervalo entre consultas)
  hachura:
    'bg-[repeating-linear-gradient(135deg,var(--cor-superficie-suave)_0_6px,var(--cor-borda)_6px_7px)]',
  horarioLivre:
    'group flex h-10 w-full cursor-pointer items-center rounded-[6px] border-0 bg-transparent px-3 text-left ' +
    'text-[0.84rem] font-semibold text-primaria transition-[background-color] duration-150 hover:bg-primaria-suave ' +
    'focus-visible:bg-primaria-suave focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-primaria',
  blocoConsulta:
    'flex w-full cursor-pointer items-center gap-3 rounded-raio-pequeno border border-l-4 px-3 py-2 text-left ' +
    'transition-[box-shadow,translate] duration-150 ease-saida hover:-translate-y-px hover:shadow-sombra-hover ' +
    'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primaria',
  chipCancelada:
    'inline-flex cursor-pointer items-center gap-1.5 rounded-full border border-borda bg-superficie-suave px-2.5 py-1 ' +
    'text-texto-suave transition-[background,color] duration-150 hover:bg-superficie hover:text-texto ' +
    'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primaria',
  legendaDia: 'flex flex-wrap items-center gap-x-4 gap-y-1 text-[0.78rem] text-texto-suave',

  // Hora atual: rótulo "Agora" na coluna das horas e a linha vermelha sobre a célula
  agora: 'pointer-events-none absolute inset-x-0 z-10 flex -translate-y-1/2 items-center',
  // Fundo branco: cobre o número da hora quando os dois coincidem
  agoraRotulo:
    'mr-1.5 w-[calc(4rem-0.375rem)] bg-superficie text-right text-[0.68rem] leading-4 font-bold uppercase ' +
    'tracking-[0.04em] text-perigo ate-720:w-[calc(3.4rem-0.375rem)]',
}

const CELULA =
  'flex min-h-[92px] cursor-pointer flex-col items-stretch gap-[0.28rem] rounded-raio-pequeno p-[0.45rem] text-left ' +
  'transition-[border-color,background,box-shadow,translate] duration-150 ease-saida hover:-translate-y-px hover:border-primaria ' +
  'ate-720:min-h-[64px] ate-720:p-[0.3rem]'

/**
 * Classes de uma célula do calendário. Os estados se combinam como no CSS original: "com eventos"
 * vence o fundo de "fora do mês"; "hoje" troca a borda por uma de 2px; o hover muda borda e fundo.
 */
export function classesCelulaDia({ foraMes, temEventos, ehHoje }) {
  const borda = ehHoje
    ? 'border-2 border-primaria shadow-[0_0_0_2px_var(--cor-primaria-anel)]'
    : `border ${temEventos ? 'border-primaria-borda' : 'border-borda'}`
  const fundo = temEventos
    ? 'bg-primaria-suave hover:bg-primaria-clara'
    : `${foraMes ? 'bg-superficie-suave' : 'bg-superficie'} hover:bg-superficie-suave`
  return `${CELULA} ${borda} ${fundo} ${foraMes ? 'text-texto-suave opacity-65' : ''}`
}
