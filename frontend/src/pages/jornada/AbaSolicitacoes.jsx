import { Ban, Check, ClipboardList, Plus, Upload } from 'lucide-react'
import { useState } from 'react'

import { mensagemDeErro } from '../../api/cliente'
import { cancelarSolicitacao, concluirSolicitacao, criarSolicitacao } from '../../api/servicos'
import { useConfirmar } from '../../components/Confirmacao'
import { Alerta, EstadoVazio, Etiqueta, estilos as ui } from '../../components/ui'
import {
  ROTULOS_STATUS_SOLICITACAO,
  ROTULOS_TIPO_SOLICITACAO,
  campoDataHoraParaIso,
  formatarDataHora,
  formatarPrazoRelativo,
  paraCampoDataHora,
} from '../../utils/formatacao'
import estilos from './Jornada.module.css'

// Solicitações que o destinatário atende enviando um documento
const TIPOS_COM_ENVIO = ['exame', 'orientacao_profissional']

const ORDEM_STATUS = { pendente: 0, atendida: 1, cancelada: 2 }

export function EtiquetaSolicitacao({ solicitacao }) {
  if (solicitacao.vencida) return <Etiqueta variante="perigo">Vencida</Etiqueta>
  const variantes = { pendente: 'alerta', atendida: 'sucesso', cancelada: 'neutra' }
  return <Etiqueta variante={variantes[solicitacao.status]}>{ROTULOS_STATUS_SOLICITACAO[solicitacao.status]}</Etiqueta>
}

/** "Carlos Lima" para o paciente; "Marina Costa (Nutricionista)" para um parceiro. */
export function nomeDoDestinatario({ nome, tipo_usuario: tipo, profissao }) {
  return tipo === 'parceiro' && profissao ? `${nome} (${profissao})` : nome
}

export default function AbaSolicitacoes({
  solicitacoes,
  parceiros,
  jornada,
  usuario,
  ehMedico,
  ehParceiro,
  editavel,
  atualizar,
  irParaAba,
}) {
  const confirmar = useConfirmar()
  const [formularioAberto, setFormularioAberto] = useState(false)
  const [erro, setErro] = useState('')

  // Pendentes primeiro (por prazo); depois as resolvidas
  const ordenadas = [...solicitacoes].sort(
    (a, b) => ORDEM_STATUS[a.status] - ORDEM_STATUS[b.status] || new Date(a.prazo) - new Date(b.prazo),
  )

  async function executar(acao, confirmacao) {
    if (confirmacao && !(await confirmar(confirmacao))) return
    setErro('')
    try {
      await acao()
      await atualizar()
    } catch (erroAcao) {
      setErro(mensagemDeErro(erroAcao))
    }
  }

  return (
    <div className={estilos.pilha}>
      <div className={ui.cartaoCabecalho} style={{ marginBottom: 0 }}>
        <h2>{ehParceiro ? 'Solicitações para você' : 'Solicitações'}</h2>
        {ehMedico && editavel && !formularioAberto && (
          <button type="button" className={ui.botao} onClick={() => setFormularioAberto(true)}>
            <Plus size={16} aria-hidden="true" />
            Nova solicitação
          </button>
        )}
      </div>

      {formularioAberto && (
        <FormularioSolicitacao
          jornada={jornada}
          parceiros={parceiros}
          aoConcluir={async () => {
            setFormularioAberto(false)
            await atualizar()
          }}
          aoCancelar={() => setFormularioAberto(false)}
        />
      )}

      <Alerta tipo="erro">{erro}</Alerta>

      {ordenadas.length === 0 ? (
        <EstadoVazio icone={ClipboardList}>
          {ehParceiro ? 'O médico ainda não fez solicitações para você.' : 'Nenhuma solicitação nesta jornada.'}
        </EstadoVazio>
      ) : (
        <ul className={ui.lista}>
          {ordenadas.map((solicitacao) => {
            const pendente = solicitacao.status === 'pendente'
            const paraMim = solicitacao.destinatario.id === usuario.id
            const paraParceiro = solicitacao.destinatario.tipo_usuario === 'parceiro'
            return (
              <li key={solicitacao.id} className={solicitacao.vencida ? ui.itemListaDestaque : ui.itemLista}>
                <div className={ui.cabecalhoItem}>
                  <strong>{ROTULOS_TIPO_SOLICITACAO[solicitacao.tipo]}</strong>
                  <EtiquetaSolicitacao solicitacao={solicitacao} />
                </div>
                <p className={estilos.texto}>{solicitacao.descricao}</p>
                <div className={estilos.meta}>
                  {/* Para o parceiro todas são dele; para os demais, só destaca as que vão a um parceiro */}
                  {!ehParceiro && (ehMedico || paraParceiro) && (
                    <span>Para: {nomeDoDestinatario(solicitacao.destinatario)}</span>
                  )}
                  <span>
                    {solicitacao.tipo === 'consulta_extra' ? 'Marcada para' : 'Prazo'}:{' '}
                    {formatarDataHora(solicitacao.prazo)}
                    {pendente && ` (${formatarPrazoRelativo(solicitacao.prazo)})`}
                  </span>
                  {solicitacao.atendida_em && <span>Atendida em {formatarDataHora(solicitacao.atendida_em)}</span>}
                </div>

                {pendente && editavel && (
                  <div className={`${ui.acoes} ${estilos.acoesItem}`}>
                    {!ehMedico && paraMim && TIPOS_COM_ENVIO.includes(solicitacao.tipo) && (
                      <button
                        type="button"
                        className={`${ui.botao} ${ui.botaoPequeno}`}
                        onClick={() => irParaAba('documentos', { solicitacao: String(solicitacao.id) })}
                      >
                        <Upload size={14} aria-hidden="true" />
                        Enviar documento
                      </button>
                    )}
                    {!ehMedico && paraMim && solicitacao.tipo === 'consulta_extra' && (
                      <span className={ui.ajuda}>Lembrete do seu médico: compareça na data marcada.</span>
                    )}
                    {!ehMedico && !paraMim && (
                      <span className={ui.ajuda}>
                        Esta solicitação é para {solicitacao.destinatario.nome}; você não precisa fazer nada.
                      </span>
                    )}
                    {ehMedico && (
                      <>
                        <button
                          type="button"
                          className={`${ui.botaoSecundario} ${ui.botaoPequeno}`}
                          onClick={() => executar(() => concluirSolicitacao(solicitacao.id))}
                        >
                          <Check size={14} aria-hidden="true" />
                          Marcar como atendida
                        </button>
                        <button
                          type="button"
                          className={`${ui.botaoPerigo} ${ui.botaoPequeno}`}
                          onClick={() =>
                            executar(() => cancelarSolicitacao(solicitacao.id), {
                              titulo: 'Cancelar esta solicitação?',
                              mensagem: 'Ela deixa de aparecer como pendência. Esta ação não pode ser desfeita.',
                              rotuloConfirmar: 'Cancelar solicitação',
                              rotuloCancelar: 'Voltar',
                              perigo: true,
                            })
                          }
                        >
                          <Ban size={14} aria-hidden="true" />
                          Cancelar
                        </button>
                      </>
                    )}
                  </div>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}

function FormularioSolicitacao({ jornada, parceiros, aoConcluir, aoCancelar }) {
  const [tipo, setTipo] = useState('exame')
  const [destinatarioId, setDestinatarioId] = useState(String(jornada.paciente.id))
  const [descricao, setDescricao] = useState('')
  const [prazo, setPrazo] = useState(() => paraCampoDataHora(new Date(Date.now() + 7 * 86_400_000)))
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  // A consulta extra é um lembrete para o paciente e não pode ir para um parceiro
  const soPaciente = tipo === 'consulta_extra'

  function aoMudarTipo(novoTipo) {
    setTipo(novoTipo)
    if (novoTipo === 'consulta_extra') setDestinatarioId(String(jornada.paciente.id))
  }

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      await criarSolicitacao(jornada.id, {
        tipo,
        descricao,
        prazo: campoDataHoraParaIso(prazo),
        destinatario_id: Number(destinatarioId),
      })
      await aoConcluir()
    } catch (erroEnvio) {
      setErro(mensagemDeErro(erroEnvio))
      setEnviando(false)
    }
  }

  return (
    <form className={`${ui.formulario} ${estilos.formularioDestaque}`} onSubmit={aoEnviar}>
      <h3>Nova solicitação</h3>
      <Alerta tipo="erro">{erro}</Alerta>
      <div className={ui.linhaCampos}>
        <div>
          <label htmlFor="solicitacao-tipo">Tipo</label>
          <select id="solicitacao-tipo" value={tipo} onChange={(e) => aoMudarTipo(e.target.value)}>
            {Object.entries(ROTULOS_TIPO_SOLICITACAO).map(([valor, rotulo]) => (
              <option key={valor} value={valor}>
                {rotulo}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="solicitacao-destinatario">Para quem</label>
          <select
            id="solicitacao-destinatario"
            value={destinatarioId}
            onChange={(e) => setDestinatarioId(e.target.value)}
            disabled={soPaciente}
          >
            <option value={jornada.paciente.id}>{jornada.paciente.nome} (paciente)</option>
            {parceiros.map(({ parceiro }) => (
              <option key={parceiro.id} value={parceiro.id}>
                {parceiro.nome} ({parceiro.profissao})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="solicitacao-prazo">{tipo === 'consulta_extra' ? 'Data da consulta' : 'Prazo'}</label>
          <input
            id="solicitacao-prazo"
            type="datetime-local"
            value={prazo}
            min={paraCampoDataHora(new Date())}
            onChange={(e) => setPrazo(e.target.value)}
            required
          />
        </div>
      </div>
      {parceiros.length === 0 && !soPaciente && (
        <p className={ui.ajuda}>
          Para pedir algo a um parceiro (ex.: plano alimentar), atribua-o a esta jornada na aba Parceiros.
        </p>
      )}
      <div>
        <label htmlFor="solicitacao-descricao">Descrição</label>
        <textarea
          id="solicitacao-descricao"
          value={descricao}
          onChange={(e) => setDescricao(e.target.value)}
          required
          minLength={3}
          placeholder={
            tipo === 'orientacao_profissional'
              ? 'Ex.: Montar e enviar o plano alimentar'
              : 'Ex.: Hemograma completo e perfil lipídico'
          }
        />
      </div>
      {soPaciente && (
        <p className={ui.ajuda}>O paciente verá esta consulta como um lembrete. Você a marca como atendida depois.</p>
      )}
      <div className={ui.acoes}>
        <button type="submit" className={ui.botao} disabled={enviando}>
          {enviando ? 'Salvando…' : 'Criar solicitação'}
        </button>
        <button type="button" className={ui.botaoSecundario} onClick={aoCancelar} disabled={enviando}>
          Cancelar
        </button>
      </div>
    </form>
  )
}
