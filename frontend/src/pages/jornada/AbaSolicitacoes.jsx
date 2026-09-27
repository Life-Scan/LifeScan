import { useState } from 'react'

import { mensagemDeErro } from '../../api/cliente'
import { cancelarSolicitacao, concluirSolicitacao, criarSolicitacao } from '../../api/servicos'
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

// Solicitações que o paciente atende enviando um documento
const TIPOS_COM_ENVIO = ['exame', 'orientacao_profissional']

const ORDEM_STATUS = { pendente: 0, atendida: 1, cancelada: 2 }

export function EtiquetaSolicitacao({ solicitacao }) {
  if (solicitacao.vencida) return <Etiqueta variante="perigo">Vencida</Etiqueta>
  const variantes = { pendente: 'alerta', atendida: 'sucesso', cancelada: 'neutra' }
  return <Etiqueta variante={variantes[solicitacao.status]}>{ROTULOS_STATUS_SOLICITACAO[solicitacao.status]}</Etiqueta>
}

export default function AbaSolicitacoes({ solicitacoes, jornada, ehMedico, editavel, atualizar, irParaAba }) {
  const [formularioAberto, setFormularioAberto] = useState(false)
  const [erro, setErro] = useState('')

  // Pendentes primeiro (por prazo); depois as resolvidas
  const ordenadas = [...solicitacoes].sort(
    (a, b) => ORDEM_STATUS[a.status] - ORDEM_STATUS[b.status] || new Date(a.prazo) - new Date(b.prazo),
  )

  async function executar(acao, confirmacao) {
    if (confirmacao && !window.confirm(confirmacao)) return
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
        <h2>Solicitações</h2>
        {ehMedico && editavel && !formularioAberto && (
          <button type="button" className={ui.botao} onClick={() => setFormularioAberto(true)}>
            Nova solicitação
          </button>
        )}
      </div>

      {formularioAberto && (
        <FormularioSolicitacao
          jornadaId={jornada.id}
          aoConcluir={async () => {
            setFormularioAberto(false)
            await atualizar()
          }}
          aoCancelar={() => setFormularioAberto(false)}
        />
      )}

      <Alerta tipo="erro">{erro}</Alerta>

      {ordenadas.length === 0 ? (
        <EstadoVazio>Nenhuma solicitação nesta jornada.</EstadoVazio>
      ) : (
        <ul className={ui.lista}>
          {ordenadas.map((solicitacao) => {
            const pendente = solicitacao.status === 'pendente'
            return (
              <li key={solicitacao.id} className={solicitacao.vencida ? ui.itemListaDestaque : ui.itemLista}>
                <div className={ui.cabecalhoItem}>
                  <strong>{ROTULOS_TIPO_SOLICITACAO[solicitacao.tipo]}</strong>
                  <EtiquetaSolicitacao solicitacao={solicitacao} />
                </div>
                <p className={estilos.texto}>{solicitacao.descricao}</p>
                <div className={estilos.meta}>
                  <span>
                    {solicitacao.tipo === 'consulta_extra' ? 'Marcada para' : 'Prazo'}:{' '}
                    {formatarDataHora(solicitacao.prazo)}
                    {pendente && ` (${formatarPrazoRelativo(solicitacao.prazo)})`}
                  </span>
                  {solicitacao.atendida_em && <span>Atendida em {formatarDataHora(solicitacao.atendida_em)}</span>}
                </div>

                {pendente && editavel && (
                  <div className={`${ui.acoes} ${estilos.acoesItem}`}>
                    {!ehMedico && TIPOS_COM_ENVIO.includes(solicitacao.tipo) && (
                      <button
                        type="button"
                        className={`${ui.botao} ${ui.botaoPequeno}`}
                        onClick={() => irParaAba('exames', { solicitacao: String(solicitacao.id) })}
                      >
                        Enviar documento
                      </button>
                    )}
                    {!ehMedico && solicitacao.tipo === 'consulta_extra' && (
                      <span className={ui.ajuda}>Lembrete do seu médico: compareça na data marcada.</span>
                    )}
                    {ehMedico && (
                      <>
                        <button
                          type="button"
                          className={`${ui.botaoSecundario} ${ui.botaoPequeno}`}
                          onClick={() => executar(() => concluirSolicitacao(solicitacao.id))}
                        >
                          Marcar como atendida
                        </button>
                        <button
                          type="button"
                          className={`${ui.botaoPerigo} ${ui.botaoPequeno}`}
                          onClick={() =>
                            executar(() => cancelarSolicitacao(solicitacao.id), 'Cancelar esta solicitação?')
                          }
                        >
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

function FormularioSolicitacao({ jornadaId, aoConcluir, aoCancelar }) {
  const [tipo, setTipo] = useState('exame')
  const [descricao, setDescricao] = useState('')
  const [prazo, setPrazo] = useState(() => paraCampoDataHora(new Date(Date.now() + 7 * 86_400_000)))
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      await criarSolicitacao(jornadaId, { tipo, descricao, prazo: campoDataHoraParaIso(prazo) })
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
          <select id="solicitacao-tipo" value={tipo} onChange={(e) => setTipo(e.target.value)}>
            {Object.entries(ROTULOS_TIPO_SOLICITACAO).map(([valor, rotulo]) => (
              <option key={valor} value={valor}>
                {rotulo}
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
              ? 'Ex.: Enviar o plano alimentar da nutricionista'
              : 'Ex.: Hemograma completo e perfil lipídico'
          }
        />
      </div>
      {tipo === 'consulta_extra' && (
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
