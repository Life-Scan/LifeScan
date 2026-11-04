import { Ban, CalendarDays, CalendarPlus, CalendarX, Check, Pencil, Search } from 'lucide-react'
import { useEffect, useState } from 'react'

import { mensagemDeErro } from '../api/cliente'
import {
  agendarConsulta,
  alterarStatusAgendamento,
  listarPacientesAgendaveis,
  obterPagina,
  remarcarConsulta,
} from '../api/servicos'
import { useConfirmar } from './Confirmacao'
import Paginacao from './Paginacao'
import { Alerta, Avatar, Carregando, ErroCarregamento, EstadoVazio, Etiqueta, estilos as ui } from './ui'
import { useAtualizacaoPeriodica } from '../hooks/useAtualizacaoPeriodica'
import {
  ROTULOS_STATUS_AGENDAMENTO,
  campoDataHoraParaIso,
  formatarDataHora,
  formatarPrazoRelativo,
  paraCampoDataHora,
} from '../utils/formatacao'
import estilos from '../pages/Paginas.module.css'

const VARIANTES_STATUS = { agendada: 'info', realizada: 'sucesso', faltou: 'perigo', cancelada: 'neutra' }

// Cada aba é um filtro da mesma rota; o "agora" é calculado a cada busca
const ABAS = [
  {
    id: 'proximas',
    titulo: 'Próximas',
    parametros: () => ({ status: 'agendada', inicio: new Date().toISOString() }),
    vazio: 'Nenhuma consulta agendada. Use o formulário acima para agendar.',
  },
  {
    id: 'a-registrar',
    titulo: 'A registrar',
    parametros: () => ({ status: 'agendada', fim: new Date().toISOString() }),
    vazio: 'Nenhuma consulta esperando registro. Depois do horário, marque aqui se a consulta foi realizada ou se o paciente faltou.',
  },
  { id: 'realizadas', titulo: 'Realizadas', parametros: () => ({ status: 'realizada', ordem: 'desc' }), vazio: 'Nenhuma consulta realizada.' },
  { id: 'faltas', titulo: 'Faltas', parametros: () => ({ status: 'faltou', ordem: 'desc' }), vazio: 'Nenhuma falta registrada.' },
  { id: 'canceladas', titulo: 'Canceladas', parametros: () => ({ status: 'cancelada', ordem: 'desc' }), vazio: 'Nenhuma consulta cancelada.' },
]

/**
 * Agenda do médico, mostrada no painel do médico (abaixo do cadastro de usuários) e do colaborador:
 * os dois agendam, remarcam, cancelam e registram as consultas.
 */
export default function AgendaConsultas() {
  const [aba, setAba] = useState('proximas')
  const [pagina, setPagina] = useState(1)
  const selecionada = ABAS.find((item) => item.id === aba)
  const { dados, erro, carregando, atualizar } = useAtualizacaoPeriodica(
    () => obterPagina('/appointments', { ...selecionada.parametros(), pagina }),
    undefined,
    [aba, pagina],
  )

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
      <FormularioAgendamento aoAgendar={() => (aba === 'proximas' ? atualizar() : mudarAba('proximas'))} />

      <section id="agenda" className={ui.cartao} aria-labelledby="titulo-agenda">
        <div className={ui.cartaoCabecalho}>
          <h2 id="titulo-agenda">Agenda de consultas</h2>
        </div>
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
              {aba === item.id && dados && <span className={estilos.contagem}>{dados.total}</span>}
            </button>
          ))}
        </div>
        <div role="tabpanel" id="painel-agenda" aria-labelledby={`aba-agenda-${aba}`} tabIndex={0} className={estilos.painelAgenda}>
          <ErroCarregamento erro={erro} />
          {carregando && !dados && <Carregando />}
          {dados && (dados.itens.length === 0 ? (
            <EstadoVazio icone={CalendarDays}>{selecionada.vazio}</EstadoVazio>
          ) : (
            <ul className={ui.lista}>
              {dados.itens.map((agendamento) => (
                <ItemAgendamento key={agendamento.id} agendamento={agendamento} aoAlterar={atualizar} />
              ))}
            </ul>
          ))}
          <Paginacao dados={dados} aoMudar={setPagina} carregando={carregando} />
        </div>
      </section>
    </>
  )
}

function FormularioAgendamento({ aoAgendar }) {
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
    return () => { ativo = false }
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
              min={paraCampoDataHora(new Date())}
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
  const confirmar = useConfirmar()
  const [editando, setEditando] = useState(false)
  const [erro, setErro] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const { paciente } = agendamento
  const agendada = agendamento.status === 'agendada'
  const passou = new Date(agendamento.data_hora) <= new Date()

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
          aoSalvar={async () => { setEditando(false); await aoAlterar() }}
          aoCancelar={() => setEditando(false)}
        />
      </li>
    )
  }

  return (
    <li className={ui.itemLista}>
      <div className={ui.linhaComAcoes}>
        <div className={ui.pessoa}>
          <Avatar nome={paciente.nome} tipo="paciente" />
          <div>
            <div className={ui.pessoaNome}>
              {formatarDataHora(agendamento.data_hora)} · {paciente.nome}{' '}
              {agendada && !passou && <Etiqueta variante="info">{formatarPrazoRelativo(agendamento.data_hora)}</Etiqueta>}
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
                <button type="button" className={`${ui.botao} ${ui.botaoPequeno}`} onClick={() => mudarStatus('realizada')} disabled={ocupado}>
                  <Check size={14} aria-hidden="true" />
                  Realizada
                </button>
                <button type="button" className={`${ui.botaoSecundario} ${ui.botaoPequeno}`} onClick={() => mudarStatus('faltou')} disabled={ocupado}>
                  <CalendarX size={14} aria-hidden="true" />
                  Faltou
                </button>
              </>
            )}
            {!passou && (
              <button type="button" className={`${ui.botaoSecundario} ${ui.botaoPequeno}`} onClick={() => setEditando(true)} disabled={ocupado}>
                <Pencil size={14} aria-hidden="true" />
                Remarcar
              </button>
            )}
            <button type="button" className={`${ui.botaoPerigo} ${ui.botaoPequeno}`} onClick={cancelar} disabled={ocupado}>
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
              min={paraCampoDataHora(new Date())}
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
