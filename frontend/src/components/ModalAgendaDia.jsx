/**
 * Agenda de um dia, em janela (DESIGN.md, item 6). Referências: grade de horários do Google Calendar e
 * horários livres clicáveis do Calendly/Cal.com. Padrão do ui-patterns.com mais próximo: Event Calendar
 * (https://ui-patterns.com/patterns/EventCalendar), itens de um período pelo horário de início.
 *
 * - Linhas de 30 minutos: ocupada (consulta), livre (clique agenda nesse horário) ou indisponível
 *   (já passou, ou fica a menos do intervalo mínimo de uma consulta agendada). Horários passados sem
 *   consulta viram uma linha só, para a grade não ter espaço morto.
 * - Clicar numa consulta abre o detalhe com as ações de sempre (renderizarDetalhe = ItemAgendamento).
 * - Cabeçalho com o dia, a contagem e a navegação (anterior, Hoje, próximo).
 *
 * O agendamento não tem duração nem tipo: o bloco mostra o horário de início e a observação.
 */
import { ArrowLeft, Ban, CalendarPlus, ChevronLeft, ChevronRight, Plus, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { cn } from '@/lib/utils'
import { useAgora } from '../hooks/useAgora'
import { chaveDiaLocal, inicioDoDia, somarDias } from '../utils/datas'
import { ROTULOS_STATUS_AGENDAMENTO, formatarDataPorExtenso, formatarHora, paraCampoDataHora } from '../utils/formatacao'
import { agendaEstilos } from './estilosAgenda'
import { BlocoEsqueleto, ErroCarregamento, EstadoVazio, Etiqueta, estilos as ui } from './ui'

// Espelha APPOINTMENT_MIN_GAP_HOURS do backend (padrão 2h). Só orienta a tela: quem valida é o backend.
const HORAS_ENTRE_CONSULTAS = 2
const INTERVALO_MS = HORAS_ENTRE_CONSULTAS * 60 * 60_000
const MINUTOS_POR_LINHA = 30
// Grade padrão das 7h às 20h; estica para caber consultas fora dela
const PRIMEIRA_HORA = 7
const ULTIMA_HORA = 20

// Cor do bloco pelo status; a etiqueta repete o status em texto
const VISUAL_STATUS = {
  agendada: { rotulo: 'Agendada', variante: 'info', bloco: 'border-info-borda border-l-info bg-info-clara' },
  aRegistrar: { rotulo: 'A registrar', variante: 'alerta', bloco: 'border-alerta-borda border-l-alerta bg-alerta-clara' },
  realizada: { rotulo: ROTULOS_STATUS_AGENDAMENTO.realizada, variante: 'sucesso', bloco: 'border-sucesso-borda border-l-sucesso bg-sucesso-clara' },
  faltou: { rotulo: ROTULOS_STATUS_AGENDAMENTO.faltou, variante: 'perigo', bloco: 'border-perigo-borda border-l-perigo bg-perigo-clara' },
  cancelada: { rotulo: ROTULOS_STATUS_AGENDAMENTO.cancelada, variante: 'neutra', bloco: 'border-borda border-l-borda-forte bg-superficie-suave' },
}

function visualStatus(agendamento, agora) {
  if (agendamento.status !== 'agendada') return VISUAL_STATUS[agendamento.status]
  return new Date(agendamento.data_hora) <= agora ? VISUAL_STATUS.aRegistrar : VISUAL_STATUS.agendada
}

const pluralizar = (n, um, varios) => `${n} ${n === 1 ? um : varios}`

/**
 * Linhas da grade do dia. Cada linha: { inicio, tipo, consultas, contemAgora, primeiraDoTipo }, com tipo
 * ocupado | livre | intervalo | passado. Sequências de horários passados sem consulta (fora a linha de
 * agora) viram uma linha { tipo: 'passados', inicio, fim }.
 */
function montarLinhas(dia, ativos, agora) {
  const minutos = ativos.map((a) => {
    const data = new Date(a.data_hora)
    return Math.floor((data.getHours() * 60 + data.getMinutes()) / MINUTOS_POR_LINHA) * MINUTOS_POR_LINHA
  })
  const primeiro = Math.min(PRIMEIRA_HORA * 60, ...minutos)
  const ultimo = Math.min(24 * 60, Math.max(ULTIMA_HORA * 60, ...minutos.map((m) => m + MINUTOS_POR_LINHA)))
  // Só consultas agendadas bloqueiam horários (a mesma regra do backend)
  const bloqueios = ativos.filter((a) => a.status === 'agendada').map((a) => new Date(a.data_hora).getTime())

  const linhas = []
  for (let minuto = primeiro; minuto < ultimo; minuto += MINUTOS_POR_LINHA) {
    const inicio = new Date(dia.getFullYear(), dia.getMonth(), dia.getDate(), 0, minuto)
    const fim = new Date(inicio.getTime() + MINUTOS_POR_LINHA * 60_000)
    const consultas = ativos.filter((a) => {
      const t = new Date(a.data_hora)
      return t >= inicio && t < fim
    })
    const contemAgora = agora >= inicio && agora < fim
    let tipo = 'livre'
    if (consultas.length > 0) tipo = 'ocupado'
    else if (inicio <= agora) tipo = 'passado'
    else if (bloqueios.some((b) => Math.abs(b - inicio.getTime()) < INTERVALO_MS)) tipo = 'intervalo'
    const anterior = linhas.at(-1)
    linhas.push({ inicio, fim, tipo, consultas, contemAgora, primeiraDoTipo: anterior?.tipo !== tipo })
  }

  // Junta as sequências de horários passados vazios (2 ou mais) numa linha só
  const resultado = []
  for (const linha of linhas) {
    const recolhivel = linha.tipo === 'passado' && !linha.contemAgora
    const ultima = resultado.at(-1)
    if (recolhivel && ultima?.tipo === 'passados') ultima.fim = linha.fim
    else if (recolhivel && ultima?.tipo === 'passado' && !ultima.contemAgora) {
      resultado[resultado.length - 1] = { tipo: 'passados', inicio: ultima.inicio, fim: linha.fim }
    } else resultado.push(linha)
  }
  return resultado
}

/**
 * Janela da agenda do dia. `dia` continua preenchido depois de fechar (aberto = false), para a saída
 * animada manter o conteúdo; `abertura` muda a cada abertura e zera a seleção.
 */
export default function ModalAgendaDia({
  dia,
  aberto,
  abertura,
  hoje,
  agendamentos,
  carregando,
  erro,
  aoTentarNovamente,
  aoMudarDia,
  aoFechar,
  aoAgendar,
  renderizarDetalhe,
}) {
  const dialogo = useRef(null)
  const titulo = useRef(null)
  const corpo = useRef(null)
  const quemAbriu = useRef(null)
  const chaveDia = dia ? chaveDiaLocal(dia) : null

  // Abre e fecha o <dialog>; ao fechar, o foco volta para quem abriu (se ainda não foi para outro lugar)
  useEffect(() => {
    const elemento = dialogo.current
    if (!elemento) return
    if (aberto && !elemento.open) {
      quemAbriu.current = document.activeElement
      elemento.showModal()
      titulo.current?.focus()
    } else if (!aberto && elemento.open) {
      elemento.close()
      const foco = document.activeElement
      if (quemAbriu.current?.isConnected && (foco === document.body || elemento.contains(foco))) quemAbriu.current.focus()
    }
  }, [aberto, dia])

  // Ao abrir, ao trocar de dia e ao terminar de carregar: leva a grade para agora, a primeira consulta
  // ou o primeiro horário livre (a um terço do topo da área visível)
  useEffect(() => {
    const area = corpo.current
    if (!aberto || carregando || !area) return
    // Em ordem de prioridade (uma lista de seletores devolveria o primeiro na ordem do documento)
    const alvo = ['[data-agora]', 'li [data-agendamento]', '[data-livre]'].map((s) => area.querySelector(s)).find(Boolean)
    area.scrollTop = alvo ? alvo.getBoundingClientRect().top - area.getBoundingClientRect().top + area.scrollTop - area.clientHeight / 3 : 0
  }, [aberto, chaveDia, carregando])

  if (!dia) return null

  const ehHoje = chaveDia === chaveDiaLocal(hoje)
  const diaPassado = inicioDoDia(dia) < hoje
  const ativos = agendamentos.filter((a) => a.status !== 'cancelada').sort((a, b) => new Date(a.data_hora) - new Date(b.data_hora))
  const canceladas = agendamentos.filter((a) => a.status === 'cancelada')

  const partesResumo = [ativos.length === 0 ? 'Nenhuma consulta' : pluralizar(ativos.length, 'consulta', 'consultas')]
  if (canceladas.length > 0) partesResumo.push(pluralizar(canceladas.length, 'cancelada', 'canceladas'))
  if (diaPassado) partesResumo.push('dia encerrado')

  function agendar(valorCampo) {
    // Fecha já, para o formulário de agendamento (fora da janela) poder receber o foco
    dialogo.current?.close()
    aoAgendar(valorCampo)
  }

  return (
    <dialog
      ref={dialogo}
      className={agendaEstilos.modalDia}
      aria-labelledby="titulo-modal-dia"
      aria-describedby="resumo-modal-dia"
      // closedby="any": o clique fora também fecha. Esc e clique fora disparam "cancel", tratado aqui
      // para o estado do React fechar a janela (onde não há suporte, sobram Esc e "Fechar")
      closedby="any"
      onCancel={(evento) => {
        evento.preventDefault()
        aoFechar()
      }}
    >
      <div className={agendaEstilos.modalConteudo}>
        <header className={agendaEstilos.modalCabecalho}>
          <div className="min-w-0">
            <p className={ui.sobretitulo}>Agenda do dia</p>
            <h2 id="titulo-modal-dia" ref={titulo} tabIndex={-1} className={agendaEstilos.modalTitulo}>
              <span className="first-letter:uppercase">{formatarDataPorExtenso(dia)}</span>
              {ehHoje && <Etiqueta variante="primaria">Hoje</Etiqueta>}
            </h2>
            <p id="resumo-modal-dia" className={agendaEstilos.modalResumo} aria-live="polite">
              {carregando ? 'Carregando…' : partesResumo.join(' · ')}
            </p>
          </div>
          <div className={agendaEstilos.modalNavegacao}>
            <div className="flex items-center gap-1" role="group" aria-label="Trocar de dia">
              <button type="button" className={agendaEstilos.botaoIcone} onClick={() => aoMudarDia(somarDias(dia, -1))} aria-label="Dia anterior">
                <ChevronLeft size={17} aria-hidden="true" />
              </button>
              <button type="button" className={cn(ui.botaoSecundario, ui.botaoPequeno)} onClick={() => aoMudarDia(hoje)} disabled={ehHoje}>
                Hoje
              </button>
              <button type="button" className={agendaEstilos.botaoIcone} onClick={() => aoMudarDia(somarDias(dia, 1))} aria-label="Próximo dia">
                <ChevronRight size={17} aria-hidden="true" />
              </button>
            </div>
            <button type="button" className={agendaEstilos.botaoIcone} onClick={aoFechar} aria-label="Fechar janela">
              <X size={18} aria-hidden="true" />
            </button>
          </div>
        </header>

        <div ref={corpo} className={agendaEstilos.modalCorpo}>
          {erro ? (
            <div className="grid justify-items-start gap-3">
              <ErroCarregamento erro={erro} />
              <button type="button" className={ui.botaoSecundario} onClick={aoTentarNovamente}>
                Tentar novamente
              </button>
            </div>
          ) : carregando ? (
            <GradeCarregando />
          ) : (
            // key: trocar de dia ou reabrir volta para a grade, sem consulta selecionada
            <ConteudoDia
              key={`${abertura}-${chaveDia}`}
              dia={dia}
              ativos={ativos}
              canceladas={canceladas}
              diaPassado={diaPassado}
              aoAgendar={agendar}
              renderizarDetalhe={renderizarDetalhe}
            />
          )}
        </div>

        <footer className={agendaEstilos.modalRodape}>
          <button type="button" className={ui.botaoSecundario} onClick={aoFechar}>
            Fechar
          </button>
          {!diaPassado && (
            <button type="button" className={ui.botao} onClick={() => agendar(null)}>
              <CalendarPlus size={16} aria-hidden="true" />
              Agendar neste dia
            </button>
          )}
        </footer>
      </div>
    </dialog>
  )
}

/** Grade do dia ou, depois de clicar numa consulta, o detalhe dela com as ações. */
function ConteudoDia({ dia, ativos, canceladas, diaPassado, aoAgendar, renderizarDetalhe }) {
  const agora = useAgora()
  const [selecionadoId, setSelecionadoId] = useState(null)
  const area = useRef(null)
  const voltar = useRef(null)
  // Para onde vai o foco depois de trocar entre grade e detalhe
  const focarDepois = useRef(null)

  useEffect(() => {
    const alvo = focarDepois.current
    focarDepois.current = null
    if (alvo === 'voltar') voltar.current?.focus()
    else if (alvo != null) area.current?.querySelector(`[data-agendamento="${alvo}"]`)?.focus()
  }, [selecionadoId])

  function abrirDetalhe(id) {
    focarDepois.current = 'voltar'
    setSelecionadoId(id)
  }

  function voltarParaGrade() {
    focarDepois.current = selecionadoId
    setSelecionadoId(null)
  }

  // A consulta pode sair do dia (remarcada para outro): aí volta para a grade
  const selecionado = [...ativos, ...canceladas].find((a) => a.id === selecionadoId)
  if (selecionado) {
    return (
      <div ref={area}>
        <button ref={voltar} type="button" className={cn(ui.botaoLink, 'mb-3')} onClick={voltarParaGrade}>
          <ArrowLeft size={16} aria-hidden="true" />
          Voltar para a agenda do dia
        </button>
        <ul className={ui.lista}>{renderizarDetalhe(selecionado)}</ul>
      </div>
    )
  }

  if (diaPassado && ativos.length === 0 && canceladas.length === 0) {
    return (
      <EstadoVazio icone={CalendarPlus} titulo="Nenhuma consulta neste dia">
        Este dia já passou. Use as setas para ver outros dias.
      </EstadoVazio>
    )
  }

  const linhas = montarLinhas(dia, ativos, agora)
  const temLivre = linhas.some((l) => l.tipo === 'livre')

  return (
    <div ref={area} className="grid gap-3">
      {canceladas.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 text-[0.82rem]">
          <span className="text-texto-suave">Canceladas:</span>
          {canceladas.map((a) => (
            <button
              key={a.id}
              type="button"
              data-agendamento={a.id}
              className={agendaEstilos.chipCancelada}
              onClick={() => abrirDetalhe(a.id)}
              aria-label={`${formatarHora(a.data_hora)}, ${a.paciente.nome}, cancelada. Ver detalhes`}
            >
              <Ban size={13} aria-hidden="true" />
              <span className="tabular-nums">{formatarHora(a.data_hora)}</span>
              {a.paciente.nome}
            </button>
          ))}
        </div>
      )}

      {!diaPassado && (
        <div className={agendaEstilos.legendaDia} aria-hidden="true">
          <span className={agendaEstilos.legendaItem}>
            <span className="size-3 rounded-[3px] border border-info-borda border-l-[3px] border-l-info bg-info-clara" />
            Ocupado
          </span>
          <span className={agendaEstilos.legendaItem}>
            <span className="size-3 rounded-[3px] border border-borda bg-superficie" />
            Livre
          </span>
          <span className={agendaEstilos.legendaItem}>
            <span className={cn('size-3 rounded-[3px] border border-borda', agendaEstilos.hachura)} />
            Indisponível
          </span>
          {ativos.length === 0 && temLivre && <span className="basis-full text-texto">Nenhuma consulta. Escolha um horário livre para agendar.</span>}
        </div>
      )}

      <ol className="m-0 list-none p-0" aria-label={`Horários de ${formatarDataPorExtenso(dia)}`}>
        {linhas.map((linha) =>
          linha.tipo === 'passados' ? (
            <li key={linha.inicio.getTime()} className={agendaEstilos.linhaGrade}>
              <span className={agendaEstilos.rotuloHora}>{formatarHora(linha.inicio.toISOString())}</span>
              <div className={cn(agendaEstilos.celula, 'border-borda')}>
                <div className={cn(agendaEstilos.faixaCelula, 'h-8 bg-superficie-suave text-texto-suave')}>
                  {formatarHora(linha.inicio.toISOString())}–{formatarHora(linha.fim.toISOString())} · horários passados, sem consultas
                </div>
              </div>
            </li>
          ) : (
            <LinhaHorario
              key={linha.inicio.getTime()}
              linha={linha}
              agora={agora}
              aoAgendar={aoAgendar}
              aoAbrir={abrirDetalhe}
            />
          ),
        )}
      </ol>
    </div>
  )
}

function LinhaHorario({ linha, agora, aoAgendar, aoAbrir }) {
  const hora = formatarHora(linha.inicio.toISOString())
  const cheia = linha.inicio.getMinutes() === 0
  return (
    <li className={cn(agendaEstilos.linhaGrade, 'relative')}>
      <span className={cn(agendaEstilos.rotuloHora, cheia ? 'font-semibold text-texto' : 'text-texto-apagado')}>{hora}</span>
      <div className={cn(agendaEstilos.celula, cheia ? 'border-borda' : 'border-dashed border-borda')}>
        {linha.tipo === 'ocupado' && (
          // grid-cols-1 (minmax(0,1fr)): com a coluna "auto", o nome sem quebra alargava o bloco no celular
          <div className="grid grid-cols-1 gap-1.5 py-1.5">
            {linha.consultas.map((agendamento) => (
              <BlocoConsulta key={agendamento.id} agendamento={agendamento} agora={agora} aoAbrir={aoAbrir} />
            ))}
          </div>
        )}
        {linha.tipo === 'livre' && (
          <button type="button" data-livre="" className={agendaEstilos.horarioLivre} onClick={() => aoAgendar(paraCampoDataHora(linha.inicio))} aria-label={`Agendar consulta às ${hora}`}>
            <span className="font-normal text-texto-apagado group-hover:hidden group-focus-visible:hidden">Livre</span>
            <span className="hidden items-center gap-1 group-hover:inline-flex group-focus-visible:inline-flex">
              <Plus size={15} aria-hidden="true" />
              Agendar às {hora}
            </span>
          </button>
        )}
        {linha.tipo === 'intervalo' && (
          <div className={cn(agendaEstilos.faixaCelula, 'h-10', agendaEstilos.hachura)}>
            {linha.primeiraDoTipo && (
              <span className="rounded bg-superficie px-1.5 text-texto-suave">Indisponível · intervalo mínimo de {HORAS_ENTRE_CONSULTAS}h entre consultas</span>
            )}
          </div>
        )}
        {linha.tipo === 'passado' && (
          <div className={cn(agendaEstilos.faixaCelula, 'h-10 bg-superficie-suave text-texto-apagado')}>{linha.primeiraDoTipo && 'Horário passado'}</div>
        )}
      </div>
      {linha.contemAgora && <LinhaAgora linha={linha} agora={agora} />}
    </li>
  )
}

/** Consulta na grade: horário, paciente, observação e status. Abre o detalhe com as ações. */
function BlocoConsulta({ agendamento, agora, aoAbrir }) {
  const visual = visualStatus(agendamento, agora)
  const hora = formatarHora(agendamento.data_hora)
  return (
    <button
      type="button"
      data-agendamento={agendamento.id}
      className={cn(agendaEstilos.blocoConsulta, visual.bloco)}
      onClick={() => aoAbrir(agendamento.id)}
      aria-label={`${hora}, ${agendamento.paciente.nome}, ${visual.rotulo}. Ver detalhes e ações`}
    >
      <span className="text-[0.92rem] font-bold tabular-nums">{hora}</span>
      <span className="min-w-0 flex-1">
        <span className="block truncate font-semibold">{agendamento.paciente.nome}</span>
        {agendamento.observacao && <span className="block truncate text-[0.8rem] text-texto-suave">{agendamento.observacao}</span>}
      </span>
      <Etiqueta variante={visual.variante}>{visual.rotulo}</Etiqueta>
      <ChevronRight size={16} aria-hidden="true" className="shrink-0 text-texto-suave" />
    </button>
  )
}

/** Linha vermelha da hora atual, na altura proporcional dentro da linha de 30 minutos. */
function LinhaAgora({ linha, agora }) {
  const fracao = (agora - linha.inicio) / (linha.fim - linha.inicio)
  return (
    <div data-agora="" aria-hidden="true" className={agendaEstilos.agora} style={{ top: `${fracao * 100}%` }}>
      <span className={agendaEstilos.agoraRotulo}>Agora</span>
      <span className="relative h-0.5 flex-1 bg-perigo">
        <span className="absolute -top-[3px] -left-1 size-2 rounded-full bg-perigo" />
      </span>
    </div>
  )
}

/** Carregando o dia: linhas da grade em esqueleto. */
function GradeCarregando() {
  return (
    <div role="status">
      <span className="visualmente-oculto">Carregando a agenda do dia…</span>
      <div className="grid gap-2" aria-hidden="true">
        {Array.from({ length: 7 }, (_, indice) => (
          <div key={indice} className={agendaEstilos.linhaGrade}>
            <BlocoEsqueleto className="mt-1 ml-auto mr-3 h-3 w-9" />
            <BlocoEsqueleto className={cn('h-10 w-full rounded-raio-pequeno', indice % 3 === 1 && 'h-12')} />
          </div>
        ))}
      </div>
    </div>
  )
}
