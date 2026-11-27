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

  // Modal de compromissos do dia
  modalDia:
    'max-h-[calc(100vh-2rem)] w-[min(680px,calc(100vw-2rem))] rounded-raio border-0 bg-superficie p-0 text-texto ' +
    'shadow-sombra-elevada dialogo-animado',
  modalConteudo: 'flex max-h-[calc(100vh-2rem)] flex-col',
  modalCabecalho: 'flex items-start justify-between gap-4 border-b border-borda px-[1.35rem] py-[1.15rem]',
  modalSubtitulo: 'mt-[0.2rem] text-[0.88rem] text-texto-suave capitalize',
  botaoFechar:
    'inline-flex size-8 cursor-pointer items-center justify-center rounded-raio-pequeno border border-borda ' +
    'bg-superficie text-texto-suave hover:bg-superficie-suave hover:text-texto',
  modalCorpo: 'overflow-y-auto px-[1.35rem] py-[1.15rem]',
  modalRodape:
    'flex flex-wrap justify-end gap-2 border-t border-borda bg-superficie-suave px-[1.35rem] py-[0.9rem]',
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
