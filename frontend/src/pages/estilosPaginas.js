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

  // Resumos do Painel; as cores do ícone e do número vêm de tonsResumo
  resumos: 'grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-3',
  resumo:
    'flex items-center gap-[0.85rem] rounded-raio border border-borda bg-superficie px-[1.1rem] py-4 text-inherit ' +
    'no-underline shadow-sombra transition-[border-color,box-shadow,translate] duration-150 ease-[ease] ' +
    // Cartão clicável: sobe 1px e ganha a sombra de hover (cartões estáticos não se movem)
    'hover:-translate-y-px hover:border-borda-forte hover:shadow-sombra-hover',
  resumoIcone: 'grid size-[2.6rem] place-items-center rounded-[10px]',
  resumoNumero: 'block text-[2rem] leading-[1.1] font-[750] tracking-[-0.03em] tabular-nums',
  resumoRotulo: 'block text-[0.86rem] text-texto-suave',

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
  opcao: `${OPCAO} border-borda hover:border-primaria`,
  opcaoSelecionada: `${OPCAO} border-primaria bg-primaria-clara shadow-[0_0_0_1px_var(--cor-primaria)]`,
  opcaoRotulo: 'font-semibold',
  opcaoDescricao: 'text-[0.82rem] font-normal text-texto-suave',

  // Lista da agenda, abaixo das abas
  painelAgenda: 'mt-4',
}

/** Cores do resumo do Painel. O tom só vale quando há itens: zero fica neutro. */
export const tonsResumo = {
  neutro: { icone: 'bg-superficie-suave text-texto-suave', numero: '' },
  perigo: { icone: 'bg-perigo-clara text-perigo', numero: 'text-perigo' },
  alerta: { icone: 'bg-alerta-clara text-alerta', numero: '' },
  info: { icone: 'bg-info-clara text-info', numero: '' },
}
