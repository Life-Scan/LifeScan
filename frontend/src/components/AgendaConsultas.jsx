import {
  Ban,
  Calendar,
  CalendarDays,
  CalendarPlus,
  CalendarX,
  Check,
  ChevronLeft,
  ChevronRight,
  List,
  Pencil,
  Search,
  X,
} from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'

import { mensagemDeErro } from '../api/cliente'
import {
  agendarConsulta,
  alterarStatusAgendamento,
  listarAgendamentos,
  listarPacientesAgendaveis,
  obterPagina,
  remarcarConsulta,
} from '../api/servicos'
import { cn } from '@/lib/utils'
import { useAuth } from '../context/AuthContext'
import { useAgora } from '../hooks/useAgora'
import { useAtualizacaoPeriodica } from '../hooks/useAtualizacaoPeriodica'
import {
  ROTULOS_STATUS_AGENDAMENTO,
  campoDataHoraParaIso,
  formatarData,
  formatarDataHora,
  formatarHora,
  formatarPrazoRelativo,
  paraCampoDataHora,
  primeiroNome,
} from '../utils/formatacao'
import { estilos } from '../pages/estilosPaginas'
import { useConfirmar } from './Confirmacao'
import { agendaEstilos, classesCelulaDia } from './estilosAgenda'
import Paginacao from './Paginacao'
import { Alerta, Avatar, ErroCarregamento, EsqueletoLista, EstadoVazio, Etiqueta, IconeTipo, estilos as ui } from './ui'

const VARIANTES_STATUS = { agendada: 'info', realizada: 'sucesso', faltou: 'perigo', cancelada: 'neutra' }
const DIAS_SEMANA = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']

const formatoMesAno = new Intl.DateTimeFormat('pt-BR', { month: 'long', year: 'numeric' })
const formatoDiaExtenso = new Intl.DateTimeFormat('pt-BR', {
  weekday: 'long',
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
})

function chaveDiaLocal(data) {
  const ano = data.getFullYear()
  const mes = String(data.getMonth() + 1).padStart(2, '0')
  const dia = String(data.getDate()).padStart(2, '0')
  return `${ano}-${mes}-${dia}`
}

function inicioDoDia(data) {
  return new Date(data.getFullYear(), data.getMonth(), data.getDate())
}

function gerarGradeMes(ano, mes) {
  const primeiroDia = new Date(ano, mes, 1)
  const ultimoDia = new Date(ano, mes + 1, 0)
  const inicioGrade = new Date(ano, mes, 1 - primeiroDia.getDay())
  const fimGrade = new Date(ano, mes, ultimoDia.getDate() + (6 - ultimoDia.getDay()))

  const dias = []
  for (let d = new Date(inicioGrade); d <= fimGrade; d.setDate(d.getDate() + 1)) {
    dias.push(new Date(d))
  }
  return dias
}

function sugestaoHorarioParaDia(dia) {
  const agora = new Date()
  const hoje = inicioDoDia(agora)
  if (inicioDoDia(dia).getTime() === hoje.getTime()) {
    const proximo = new Date(agora.getTime() + 60 * 60_000)
    proximo.setMinutes(0, 0, 0)
    if (inicioDoDia(proximo).getTime() === hoje.getTime()) {
      return paraCampoDataHora(proximo)
    }
    return paraCampoDataHora(new Date(agora.getTime() + 15 * 60_000))
  }
  return paraCampoDataHora(new Date(dia.getFullYear(), dia.getMonth(), dia.getDate(), 9, 0))
}

// Cada aba é um filtro da mesma rota; o "agora" é calculado a cada busca
const ABAS = [
  {
    id: 'proximas',
    titulo: 'Próximas',
    parametros: () => ({ status: 'agendada', inicio: new Date().toISOString() }),
    vazio: { titulo: 'Nenhuma consulta agendada', frase: 'Use o formulário acima para agendar.' },
  },
  {
    id: 'a-registrar',
    titulo: 'A registrar',
    parametros: () => ({ status: 'agendada', fim: new Date().toISOString() }),
    vazio: {
      titulo: 'Nada para registrar',
      frase: 'Depois do horário, as consultas aparecem aqui para você marcar se foram realizadas ou se o paciente faltou.',
    },
  },
  {
    id: 'realizadas',
    titulo: 'Realizadas',
    parametros: () => ({ status: 'realizada', ordem: 'desc' }),
    vazio: { titulo: 'Nenhuma consulta realizada', frase: 'As consultas marcadas como realizadas aparecem aqui.' },
  },
  {
    id: 'faltas',
    titulo: 'Faltas',
    parametros: () => ({ status: 'faltou', ordem: 'desc' }),
    vazio: { titulo: 'Nenhuma falta registrada', frase: 'As consultas em que o paciente faltou aparecem aqui.' },
  },
  {
    id: 'canceladas',
    titulo: 'Canceladas',
    parametros: () => ({ status: 'cancelada', ordem: 'desc' }),
    vazio: { titulo: 'Nenhuma consulta cancelada', frase: 'As consultas canceladas aparecem aqui.' },
  },
]

/**
 * Agenda do médico, mostrada no painel do médico (abaixo do cadastro de usuários) e do colaborador:
 * os dois agendam, remarcam, cancelam e registram as consultas.
 */
export default function AgendaConsultas() {
  const { ehMedico } = useAuth()
  const [modo, setModo] = useState('calendario')
  const [aba, setAba] = useState('proximas')
  const [pagina, setPagina] = useState(1)

  // "Hoje" vem do relógio do useAgora (atualizado fora do render) e só muda quando vira o dia
  const agora = useAgora()
  const chaveHoje = chaveDiaLocal(agora)
  const hoje = useMemo(() => {
    const [ano, mes, dia] = chaveHoje.split('-').map(Number)
    return new Date(ano, mes - 1, dia)
  }, [chaveHoje])
  const [mesReferencia, setMesReferencia] = useState(() => ({ ano: hoje.getFullYear(), mes: hoje.getMonth() }))
  // O dia fica guardado depois de fechar, para a janela sair animada com o mesmo conteúdo
  const [diaModal, setDiaModal] = useState(null)
  const [modalAberto, setModalAberto] = useState(false)
  const [dataPredefinida, setDataPredefinida] = useState(null)
  const modalInicialAberto = useRef(false)

  const diasGrade = useMemo(() => gerarGradeMes(mesReferencia.ano, mesReferencia.mes), [mesReferencia])

  const {
    dados: dadosCalendario,
    erro: erroCalendario,
    carregando: carregandoCalendario,
    atualizar: atualizarCalendario,
  } = useAtualizacaoPeriodica(
    () => {
      const inicio = diasGrade[0]
      const ultimo = diasGrade[diasGrade.length - 1]
      const fimExclusivo = new Date(ultimo.getFullYear(), ultimo.getMonth(), ultimo.getDate() + 1)
      return listarAgendamentos({
        inicio: inicio.toISOString(),
        fim: fimExclusivo.toISOString(),
      })
    },
    undefined,
    [mesReferencia.ano, mesReferencia.mes],
  )

  const selecionada = ABAS.find((item) => item.id === aba)
  const {
    dados: dadosLista,
    erro: erroLista,
    carregando: carregandoLista,
    atualizar: atualizarLista,
  } = useAtualizacaoPeriodica(
    () => obterPagina('/appointments', { ...selecionada.parametros(), pagina }),
    undefined,
    [aba, pagina],
  )

  // Quando o médico acessa o painel pela primeira vez, abre automaticamente o modal com os compromissos de hoje
  useEffect(() => {
    if (ehMedico && !modalInicialAberto.current && dadosCalendario !== null) {
      modalInicialAberto.current = true
      setDiaModal(hoje)
      setModalAberto(true)
    }
  }, [ehMedico, dadosCalendario, hoje])

  const agendamentosPorDia = useMemo(() => {
    const mapa = new Map()
    for (const agendamento of dadosCalendario || []) {
      const chave = chaveDiaLocal(new Date(agendamento.data_hora))
      if (!mapa.has(chave)) mapa.set(chave, [])
      mapa.get(chave).push(agendamento)
    }
    return mapa
  }, [dadosCalendario])

  const compromissosHoje = agendamentosPorDia.get(chaveDiaLocal(hoje)) || []
  const compromissosDiaModal = diaModal ? agendamentosPorDia.get(chaveDiaLocal(diaModal)) || [] : []

  async function atualizarTudo() {
    await Promise.all([atualizarCalendario(), atualizarLista()])
  }

  function irParaMes(deslocamento) {
    setMesReferencia((atual) => {
      const novo = new Date(atual.ano, atual.mes + deslocamento, 1)
      return { ano: novo.getFullYear(), mes: novo.getMonth() }
    })
  }

  function irParaHoje() {
    setMesReferencia({ ano: hoje.getFullYear(), mes: hoje.getMonth() })
  }

  function abrirModalDia(dia) {
    setDiaModal(dia)
    setModalAberto(true)
  }

  function abrirCompromissosDeHoje() {
    irParaHoje()
    abrirModalDia(hoje)
  }

  function mudarAba(id) {
    setAba(id)
    setPagina(1)
  }

  function navegarAbas(evento, indice) {
    const destinos = { ArrowRight: indice + 1, ArrowLeft: indice - 1, Home: 0, End: ABAS.length - 1 }
    if (!(evento.key in destinos)) return
    evento.preventDefault()
    const destino = (destinos[evento.key] + ABAS.length) % ABAS.length
    mudarAba(ABAS[destino].id)
    document.getElementById(`aba-agenda-${ABAS[destino].id}`).focus()
  }

  return (
    <>
      <FormularioAgendamento
        dataPredefinida={dataPredefinida}
        aoAgendar={() => {
          atualizarTudo()
          if (modo === 'lista' && aba !== 'proximas') mudarAba('proximas')
        }}
      />

      <section id="agenda" className={ui.cartao} aria-labelledby="titulo-agenda">
        <div className={ui.cartaoCabecalho}>
          <h2 id="titulo-agenda" className={ui.tituloComIcone}>
            <IconeTipo tipo="consulta">
              <CalendarDays size={16} />
            </IconeTipo>
            Agenda de consultas
          </h2>
          <div className={agendaEstilos.cabecalhoControles}>
            <button type="button" className={cn(ui.botaoSecundario, ui.botaoPequeno)} onClick={abrirCompromissosDeHoje}>
              <CalendarDays size={15} aria-hidden="true" />
              Compromissos de hoje
              {compromissosHoje.length > 0 && <span className={estilos.contagem}>{compromissosHoje.length}</span>}
            </button>

            <div className={agendaEstilos.alternadorModo} role="group" aria-label="Visualização da agenda">
              <button
                type="button"
                className={modo === 'calendario' ? agendaEstilos.botaoModoAtivo : agendaEstilos.botaoModo}
                onClick={() => setModo('calendario')}
                aria-pressed={modo === 'calendario'}
              >
                <Calendar size={14} aria-hidden="true" />
                Calendário
              </button>
              <button
                type="button"
                className={modo === 'lista' ? agendaEstilos.botaoModoAtivo : agendaEstilos.botaoModo}
                onClick={() => setModo('lista')}
                aria-pressed={modo === 'lista'}
              >
                <List size={14} aria-hidden="true" />
                Lista
              </button>
            </div>
          </div>
        </div>

        {modo === 'calendario' ? (
          <div>
            <div className={agendaEstilos.calendarioTopo}>
              <span className={agendaEstilos.mesTitulo}>
                {formatoMesAno.format(new Date(mesReferencia.ano, mesReferencia.mes, 1))}
              </span>
              <div className={agendaEstilos.navegacaoMes}>
                <button
                  type="button"
                  className={cn(ui.botaoSecundario, ui.botaoPequeno)}
                  onClick={() => irParaMes(-1)}
                  aria-label="Mês anterior"
                >
                  <ChevronLeft size={16} aria-hidden="true" />
                </button>
                <button type="button" className={cn(ui.botaoSecundario, ui.botaoPequeno)} onClick={irParaHoje}>
                  Hoje
                </button>
                <button
                  type="button"
                  className={cn(ui.botaoSecundario, ui.botaoPequeno)}
                  onClick={() => irParaMes(1)}
                  aria-label="Próximo mês"
                >
                  <ChevronRight size={16} aria-hidden="true" />
                </button>
              </div>
            </div>

            <ErroCarregamento erro={erroCalendario} />
            {/* Carregando o mês: a própria grade é o esqueleto, com o brilho passando por cima */}
            {carregandoCalendario && !dadosCalendario && (
              <span role="status" className="visualmente-oculto">
                Carregando as consultas do mês…
              </span>
            )}

            <div className={agendaEstilos.gradeSemana} aria-hidden="true">
              {DIAS_SEMANA.map((dia) => (
                <div key={dia} className={agendaEstilos.diaSemana}>
                  {dia}
                </div>
              ))}
            </div>

            {/* key: ao trocar de mês a grade remonta e entra com fade + 4px */}
            <div
              key={`${mesReferencia.ano}-${mesReferencia.mes}`}
              className={cn(
                agendaEstilos.gradeDias,
                'animate-entrar',
                carregandoCalendario && !dadosCalendario && 'esqueleto-brilho rounded-raio-pequeno',
              )}
              role="grid"
              aria-label="Calendário mensal de consultas"
            >
              {diasGrade.map((dia) => {
                const chave = chaveDiaLocal(dia)
                const eventos = agendamentosPorDia.get(chave) || []
                const foraMes = dia.getMonth() !== mesReferencia.mes
                const ehHoje = chave === chaveDiaLocal(hoje)
                const temEventos = eventos.length > 0

                return (
                  <button
                    key={chave}
                    type="button"
                    className={classesCelulaDia({ foraMes, temEventos, ehHoje })}
                    onClick={() => abrirModalDia(dia)}
                    aria-label={`${formatarData(dia.toISOString())}: ${eventos.length} ${eventos.length === 1 ? 'compromisso' : 'compromissos'}`}
                  >
                    <div className={agendaEstilos.cabecalhoDia}>
                      <span className={`${agendaEstilos.numeroDia} ${ehHoje ? agendaEstilos.numeroDiaHoje : ''}`}>
                        {dia.getDate()}
                      </span>
                      {temEventos && <span className={agendaEstilos.contagemEventos}>{eventos.length}</span>}
                    </div>

                    {temEventos && (
                      <div className={agendaEstilos.listaEventosDia}>
                        {eventos.slice(0, 2).map((evento) => {
                          const passou = new Date(evento.data_hora) <= agora
                          const classeStatus =
                            evento.status === 'agendada'
                              ? passou
                                ? agendaEstilos.evento_atrasada
                                : agendaEstilos.evento_agendada
                              : agendaEstilos[`evento_${evento.status}`]

                          return (
                            <span key={evento.id} className={`${agendaEstilos.eventoChip} ${classeStatus}`}>
                              <span className={agendaEstilos.eventoHora}>{formatarHora(evento.data_hora)}</span>
                              <span className={agendaEstilos.eventoNome}>{primeiroNome(evento.paciente.nome)}</span>
                            </span>
                          )
                        })}
                        {eventos.length > 2 && (
                          <span className={agendaEstilos.maisEventos}>+{eventos.length - 2} mais</span>
                        )}
                      </div>
                    )}
                  </button>
                )
              })}
            </div>

            <div className={agendaEstilos.legenda} aria-hidden="true">
              <span className={agendaEstilos.legendaItem}>
                <span className={`${agendaEstilos.legendaCor} ${agendaEstilos.evento_agendada}`} />
                Agendada
              </span>
              <span className={agendaEstilos.legendaItem}>
                <span className={`${agendaEstilos.legendaCor} ${agendaEstilos.evento_atrasada}`} />
                A registrar
              </span>
              <span className={agendaEstilos.legendaItem}>
                <span className={`${agendaEstilos.legendaCor} ${agendaEstilos.evento_realizada}`} />
                Realizada
              </span>
              <span className={agendaEstilos.legendaItem}>
                <span className={`${agendaEstilos.legendaCor} ${agendaEstilos.evento_faltou}`} />
                Faltou
              </span>
              <span className={agendaEstilos.legendaItem}>
                <span className={`${agendaEstilos.legendaCor} ${agendaEstilos.evento_cancelada}`} />
                Cancelada
              </span>
            </div>
          </div>
        ) : (
          <>
            <div className={estilos.abasPacientes} role="tablist" aria-label="Situação das consultas">
              {ABAS.map((item, indice) => (
                <button
                  key={item.id}
                  type="button"
                  role="tab"
                  id={`aba-agenda-${item.id}`}
                  aria-controls="painel-agenda"
                  aria-selected={aba === item.id}
                  tabIndex={aba === item.id ? 0 : -1}
                  className={estilos.abaPacientes}
                  onClick={() => mudarAba(item.id)}
                  onKeyDown={(evento) => navegarAbas(evento, indice)}
                >
                  {item.titulo}
                  {aba === item.id && dadosLista && <span className={estilos.contagem}>{dadosLista.total}</span>}
                </button>
              ))}
            </div>
            <div role="tabpanel" id="painel-agenda" aria-labelledby={`aba-agenda-${aba}`} tabIndex={0} className={estilos.painelAgenda}>
              <ErroCarregamento erro={erroLista} />
              {carregandoLista && !dadosLista && <EsqueletoLista avatar texto="Carregando consultas…" />}
              {/* Aba e página zeram os dados: a lista remonta e entra com fade + 4px. O polling não. */}
              {dadosLista && (
                <div className="animate-entrar">
                  {dadosLista.itens.length === 0 ? (
                    <EstadoVazio icone={CalendarDays} titulo={selecionada.vazio.titulo}>
                      {selecionada.vazio.frase}
                    </EstadoVazio>
                  ) : (
                    <ul className={ui.lista}>
                      {dadosLista.itens.map((agendamento) => (
                        <ItemAgendamento key={agendamento.id} agendamento={agendamento} aoAlterar={atualizarTudo} />
                      ))}
                    </ul>
                  )}
                </div>
              )}
              <Paginacao dados={dadosLista} aoMudar={setPagina} carregando={carregandoLista} />
            </div>
          </>
        )}
      </section>

      <ModalCompromissosDia
        dia={diaModal}
        aberto={modalAberto}
        hoje={hoje}
        agendamentos={compromissosDiaModal}
        aoFechar={() => setModalAberto(false)}
        aoAlterar={atualizarTudo}
        aoAgendarNoDia={(dia) => {
          setModalAberto(false)
          setDataPredefinida({ valor: sugestaoHorarioParaDia(dia), token: Date.now() })
        }}
      />
    </>
  )
}

/** `dia` continua preenchido depois de fechar (aberto = false), para a saída animada manter o conteúdo. */
function ModalCompromissosDia({ dia, aberto, hoje, agendamentos, aoFechar, aoAlterar, aoAgendarNoDia }) {
  const dialogo = useRef(null)

  useEffect(() => {
    if (aberto && !dialogo.current?.open) dialogo.current?.showModal()
    else if (!aberto && dialogo.current?.open) dialogo.current?.close()
  }, [aberto, dia])

  if (!dia) return null

  const ehHoje = chaveDiaLocal(dia) === chaveDiaLocal(hoje)
  const podeAgendar = inicioDoDia(dia).getTime() >= hoje.getTime()

  return (
    <dialog
      ref={dialogo}
      className={agendaEstilos.modalDia}
      aria-labelledby="titulo-modal-dia"
      // closedby="any": o clique fora da janela também fecha. Esc e clique fora disparam "cancel",
      // tratado aqui para o estado do React fechar o modal (onde não há suporte, sobram Esc e "Fechar")
      closedby="any"
      onCancel={(evento) => {
        evento.preventDefault()
        aoFechar()
      }}
    >
      <div className={agendaEstilos.modalConteudo}>
        <div className={agendaEstilos.modalCabecalho}>
          <div>
            <h2 id="titulo-modal-dia">
              {ehHoje ? 'Compromissos de hoje' : `Compromissos de ${formatarData(dia.toISOString())}`}
            </h2>
            <p className={agendaEstilos.modalSubtitulo}>{formatoDiaExtenso.format(dia)}</p>
          </div>
          <button type="button" className={agendaEstilos.botaoFechar} onClick={aoFechar} aria-label="Fechar janela">
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        <div className={agendaEstilos.modalCorpo}>
          {agendamentos.length === 0 ? (
            <EstadoVazio icone={CalendarDays} titulo={ehHoje ? 'Nenhum compromisso hoje' : 'Nenhum compromisso neste dia'}>
              {podeAgendar && 'Use "Agendar neste dia" para marcar uma consulta.'}
            </EstadoVazio>
          ) : (
            <ul className={ui.lista}>
              {agendamentos.map((agendamento) => (
                <ItemAgendamento key={agendamento.id} agendamento={agendamento} aoAlterar={aoAlterar} />
              ))}
            </ul>
          )}
        </div>

        <div className={agendaEstilos.modalRodape}>
          {podeAgendar && (
            <button type="button" className={ui.botaoSecundario} onClick={() => aoAgendarNoDia(dia)}>
              <CalendarPlus size={16} aria-hidden="true" />
              Agendar neste dia
            </button>
          )}
          <button type="button" className={ui.botao} onClick={aoFechar}>
            Fechar
          </button>
        </div>
      </div>
    </dialog>
  )
}

function FormularioAgendamento({ aoAgendar, dataPredefinida }) {
  const agora = useAgora()
  const [textoBusca, setTextoBusca] = useState('')
  const [busca, setBusca] = useState('')
  const [pacientes, setPacientes] = useState(null)
  const [erroPacientes, setErroPacientes] = useState('')
  const [pacienteId, setPacienteId] = useState('')
  const [dataHora, setDataHora] = useState('')
  const [observacao, setObservacao] = useState('')
  const [erro, setErro] = useState('')
  const [sucesso, setSucesso] = useState('')
  const [enviando, setEnviando] = useState(false)

  // "Agendar neste dia" no modal preenche a data: ajusta o estado no render quando chega um pedido novo
  // (token diferente), em vez de copiar num efeito
  const [tokenAplicado, setTokenAplicado] = useState(null)
  if (dataPredefinida?.valor && dataPredefinida.token !== tokenAplicado) {
    setTokenAplicado(dataPredefinida.token)
    setDataHora(dataPredefinida.valor)
  }

  useEffect(() => {
    if (dataPredefinida?.valor) document.getElementById('agenda-busca')?.focus()
  }, [dataPredefinida])

  useEffect(() => {
    const temporizador = setTimeout(() => setBusca(textoBusca.trim()), 250)
    return () => clearTimeout(temporizador)
  }, [textoBusca])

  useEffect(() => {
    let ativo = true
    listarPacientesAgendaveis({ busca, pagina: 1, tamanho: 50 })
      .then((resultado) => {
        if (!ativo) return
        setPacientes(resultado)
        setErroPacientes('')
        // Se a busca for única, já deixa o paciente escolhido
        if (resultado.itens.length === 1) setPacienteId(String(resultado.itens[0].id))
        else if (!resultado.itens.some((p) => String(p.id) === pacienteId)) setPacienteId('')
      })
      .catch((erroBusca) => ativo && setErroPacientes(mensagemDeErro(erroBusca)))
    return () => {
      ativo = false
    }
    // pacienteId fica de fora de propósito: só a busca dispara a consulta
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busca])

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    setSucesso('')
    setEnviando(true)
    try {
      const agendamento = await agendarConsulta({
        paciente_id: Number(pacienteId),
        data_hora: campoDataHoraParaIso(dataHora),
        observacao: observacao.trim() || null,
      })
      setSucesso(`Consulta de ${agendamento.paciente.nome} agendada para ${formatarDataHora(agendamento.data_hora)}.`)
      setDataHora('')
      setObservacao('')
      aoAgendar()
    } catch (erroEnvio) {
      setErro(mensagemDeErro(erroEnvio))
    } finally {
      setEnviando(false)
    }
  }

  const semPacientes = pacientes && pacientes.total === 0 && !busca

  return (
    <section className={ui.cartao}>
      <div className={ui.cartaoCabecalho}>
        <h2>Agendar consulta</h2>
      </div>
      <form className={ui.formulario} onSubmit={aoEnviar}>
        <div className={ui.linhaCampos}>
          <div>
            <label htmlFor="agenda-busca">Buscar paciente</label>
            <div className={estilos.buscaContas}>
              <input
                id="agenda-busca"
                type="text"
                role="searchbox"
                placeholder="Nome ou e-mail"
                value={textoBusca}
                onChange={(evento) => setTextoBusca(evento.target.value)}
                maxLength={255}
              />
              <Search className={estilos.iconeBuscaContas} size={18} aria-hidden="true" />
            </div>
          </div>
          <div>
            <label htmlFor="agenda-paciente">Paciente</label>
            <select id="agenda-paciente" value={pacienteId} onChange={(evento) => setPacienteId(evento.target.value)} required>
              <option value="">
                {pacientes === null ? 'Carregando…' : pacientes.itens.length === 0 ? 'Nenhum paciente encontrado' : 'Escolha o paciente'}
              </option>
              {pacientes?.itens.map((paciente) => (
                <option key={paciente.id} value={paciente.id}>
                  {paciente.nome} ({paciente.email})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="agenda-data">Data e hora</label>
            <input
              id="agenda-data"
              type="datetime-local"
              value={dataHora}
              min={paraCampoDataHora(agora)}
              onChange={(evento) => setDataHora(evento.target.value)}
              required
            />
          </div>
        </div>
        <div>
          <label htmlFor="agenda-observacao">Observação (opcional)</label>
          <input
            id="agenda-observacao"
            value={observacao}
            onChange={(evento) => setObservacao(evento.target.value)}
            maxLength={255}
            placeholder="Ex.: Retorno para mostrar os exames"
          />
        </div>
        {semPacientes && (
          <p className={ui.ajuda}>
            Ainda não há pacientes para agendar. Só podem ser agendados pacientes que já passaram pela primeira consulta
            com o médico (com a consulta registrada no acompanhamento).
          </p>
        )}
        <Alerta tipo="erro">{erroPacientes || erro}</Alerta>
        <Alerta tipo="sucesso">{sucesso}</Alerta>
        <div className={ui.acoes}>
          <button type="submit" className={ui.botao} disabled={enviando || !pacienteId}>
            <CalendarPlus size={16} aria-hidden="true" />
            {enviando ? 'Agendando…' : 'Agendar consulta'}
          </button>
          <span className={ui.ajuda}>
            Só aparecem pacientes que já passaram pela primeira consulta. Duas consultas precisam ficar a pelo menos 2 horas
            uma da outra.
          </span>
        </div>
      </form>
    </section>
  )
}

function ItemAgendamento({ agendamento, aoAlterar }) {
  const agora = useAgora()
  const confirmar = useConfirmar()
  const [editando, setEditando] = useState(false)
  const [erro, setErro] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const { paciente } = agendamento
  const agendada = agendamento.status === 'agendada'
  const passou = new Date(agendamento.data_hora) <= agora

  async function mudarStatus(status) {
    setErro('')
    setOcupado(true)
    try {
      await alterarStatusAgendamento(agendamento.id, status)
      await aoAlterar()
    } catch (erroAcao) {
      setErro(mensagemDeErro(erroAcao))
    } finally {
      setOcupado(false)
    }
  }

  async function cancelar() {
    const confirmado = await confirmar({
      titulo: `Cancelar a consulta de ${paciente.nome}?`,
      mensagem: `A consulta de ${formatarDataHora(agendamento.data_hora)} será cancelada e o horário ficará livre. Essa ação não pode ser desfeita.`,
      rotuloConfirmar: 'Cancelar consulta',
      rotuloCancelar: 'Manter',
      perigo: true,
    })
    if (confirmado) mudarStatus('cancelada')
  }

  if (editando) {
    return (
      <li className={ui.itemLista}>
        <FormularioRemarcacao
          agendamento={agendamento}
          aoSalvar={async () => {
            setEditando(false)
            await aoAlterar()
          }}
          aoCancelar={() => setEditando(false)}
        />
      </li>
    )
  }

  return (
    <li className={ui.itemListaConsulta}>
      <div className={ui.linhaComAcoes}>
        <div className={ui.pessoa}>
          <Avatar nome={paciente.nome} tipo="paciente" />
          <div>
            <div className={ui.pessoaNome}>
              {formatarDataHora(agendamento.data_hora)} · {paciente.nome}{' '}
              {agendada && !passou && <Etiqueta variante="info">{formatarPrazoRelativo(agendamento.data_hora, agora)}</Etiqueta>}
              {agendada && passou && <Etiqueta variante="alerta">A registrar</Etiqueta>}
              {!agendada && (
                <Etiqueta variante={VARIANTES_STATUS[agendamento.status]}>{ROTULOS_STATUS_AGENDAMENTO[agendamento.status]}</Etiqueta>
              )}
            </div>
            <div className={estilos.meta}>
              <span>{paciente.email}</span>
              {agendamento.observacao && <span>{agendamento.observacao}</span>}
              <span>Agendada por {agendamento.criado_por.nome}</span>
            </div>
          </div>
        </div>
        {agendada && (
          <div className={ui.acoes}>
            {passou && (
              <>
                <button type="button" className={cn(ui.botao, ui.botaoPequeno)} onClick={() => mudarStatus('realizada')} disabled={ocupado}>
                  <Check size={14} aria-hidden="true" />
                  Realizada
                </button>
                <button type="button" className={cn(ui.botaoSecundario, ui.botaoPequeno)} onClick={() => mudarStatus('faltou')} disabled={ocupado}>
                  <CalendarX size={14} aria-hidden="true" />
                  Faltou
                </button>
              </>
            )}
            {!passou && (
              <button type="button" className={cn(ui.botaoSecundario, ui.botaoPequeno)} onClick={() => setEditando(true)} disabled={ocupado}>
                <Pencil size={14} aria-hidden="true" />
                Remarcar
              </button>
            )}
            <button type="button" className={cn(ui.botaoPerigo, ui.botaoPequeno)} onClick={cancelar} disabled={ocupado}>
              <Ban size={14} aria-hidden="true" />
              Cancelar
            </button>
          </div>
        )}
      </div>
      <Alerta tipo="erro">{erro}</Alerta>
    </li>
  )
}

function FormularioRemarcacao({ agendamento, aoSalvar, aoCancelar }) {
  const agora = useAgora()
  const [dataHora, setDataHora] = useState(paraCampoDataHora(new Date(agendamento.data_hora)))
  const [observacao, setObservacao] = useState(agendamento.observacao || '')
  const [erro, setErro] = useState('')
  const [salvando, setSalvando] = useState(false)

  async function enviar(evento) {
    evento.preventDefault()
    setErro('')
    setSalvando(true)
    try {
      await remarcarConsulta(agendamento.id, { data_hora: campoDataHoraParaIso(dataHora), observacao: observacao.trim() || null })
      await aoSalvar()
    } catch (erroEdicao) {
      setErro(mensagemDeErro(erroEdicao))
      setSalvando(false)
    }
  }

  return (
    <form className={ui.formulario} onSubmit={enviar} aria-label={`Remarcar a consulta de ${agendamento.paciente.nome}`}>
      <h3>Remarcar a consulta de {agendamento.paciente.nome}</h3>
      <fieldset className={estilos.camposEdicao} disabled={salvando}>
        <legend className="visualmente-oculto">Nova data e observação</legend>
        <div className={ui.linhaCampos}>
          <div>
            <label htmlFor={`remarcar-data-${agendamento.id}`}>Nova data e hora</label>
            <input
              id={`remarcar-data-${agendamento.id}`}
              type="datetime-local"
              value={dataHora}
              min={paraCampoDataHora(agora)}
              onChange={(evento) => setDataHora(evento.target.value)}
              required
              autoFocus
            />
          </div>
          <div>
            <label htmlFor={`remarcar-observacao-${agendamento.id}`}>Observação</label>
            <input
              id={`remarcar-observacao-${agendamento.id}`}
              value={observacao}
              onChange={(evento) => setObservacao(evento.target.value)}
              maxLength={255}
            />
          </div>
        </div>
        <Alerta tipo="erro">{erro}</Alerta>
        <div className={ui.acoes}>
          <button type="submit" className={ui.botao}>{salvando ? 'Salvando…' : 'Salvar'}</button>
          <button type="button" className={ui.botaoSecundario} onClick={aoCancelar}>Voltar</button>
        </div>
      </fieldset>
    </form>
  )
}
