import { useState } from 'react'

import { mensagemDeErro } from '../../api/cliente'
import { enviarExame, revisarExame } from '../../api/servicos'
import { Alerta, Anexo, CampoArquivo, EstadoVazio, Etiqueta, estilos as ui } from '../../components/ui'
import { ROTULOS_STATUS_EXAME, ROTULOS_TIPO_SOLICITACAO, formatarData, formatarDataHora } from '../../utils/formatacao'
import estilos from './Jornada.module.css'

const TIPOS_COM_ENVIO = ['exame', 'orientacao_profissional']

export default function AbaExames({ exames, solicitacoes, solicitacaoInicial, jornada, ehMedico, editavel, atualizar }) {
  const abertas = solicitacoes.filter((s) => s.status === 'pendente' && TIPOS_COM_ENVIO.includes(s.tipo))
  const [formularioAberto, setFormularioAberto] = useState(Boolean(solicitacaoInicial) && editavel)

  return (
    <div className={estilos.pilha}>
      <div className={ui.cartaoCabecalho} style={{ marginBottom: 0 }}>
        <h2>Exames e documentos</h2>
        {editavel && !formularioAberto && (
          <button type="button" className={ui.botao} onClick={() => setFormularioAberto(true)}>
            Enviar arquivo
          </button>
        )}
      </div>

      {formularioAberto && (
        <FormularioExame
          jornadaId={jornada.id}
          solicitacoes={abertas}
          solicitacaoInicial={solicitacaoInicial}
          aoConcluir={async () => {
            setFormularioAberto(false)
            await atualizar()
          }}
          aoCancelar={() => setFormularioAberto(false)}
        />
      )}

      {exames.length === 0 ? (
        <EstadoVazio>Nenhum exame ou documento enviado.</EstadoVazio>
      ) : (
        <ul className={ui.lista}>
          {exames.map((exame) => (
            <ItemExame
              key={exame.id}
              exame={exame}
              solicitacao={solicitacoes.find((s) => s.id === exame.solicitacao_id)}
              podeRevisar={ehMedico && editavel}
              atualizar={atualizar}
            />
          ))}
        </ul>
      )}
    </div>
  )
}

function ItemExame({ exame, solicitacao, podeRevisar, atualizar }) {
  const [revisando, setRevisando] = useState(false)
  const [observacao, setObservacao] = useState(exame.observacao_revisao || '')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)
  const revisado = exame.status === 'revisado'

  async function salvarRevisao(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      await revisarExame(exame.id, observacao.trim() || null)
      setRevisando(false)
      await atualizar()
    } catch (erroRevisao) {
      setErro(mensagemDeErro(erroRevisao))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <li className={ui.itemLista}>
      <div className={ui.cabecalhoItem}>
        <strong>{exame.titulo}</strong>
        <Etiqueta variante={revisado ? 'sucesso' : 'alerta'}>{ROTULOS_STATUS_EXAME[exame.status]}</Etiqueta>
      </div>
      <div className={estilos.meta}>
        <span>Enviado por {exame.enviado_por.nome}</span>
        <span>{formatarDataHora(exame.criado_em)}</span>
        {solicitacao && <span>Atende: {ROTULOS_TIPO_SOLICITACAO[solicitacao.tipo].toLowerCase()}</span>}
      </div>
      <div className={estilos.acoesItem}>
        <Anexo arquivo={exame.arquivo} />
      </div>

      {revisado && !revisando && (
        <div className={estilos.revisao}>
          <strong>Revisão do médico</strong> <span className={ui.suave}>({formatarData(exame.revisado_em)})</span>
          <p className={estilos.texto}>{exame.observacao_revisao || 'Revisado sem observações.'}</p>
        </div>
      )}

      {podeRevisar && !revisando && (
        <div className={estilos.acoesItem}>
          <button type="button" className={`${ui.botaoSecundario} ${ui.botaoPequeno}`} onClick={() => setRevisando(true)}>
            {revisado ? 'Editar revisão' : 'Revisar exame'}
          </button>
        </div>
      )}

      {revisando && (
        <form className={`${ui.formulario} ${estilos.acoesItem}`} onSubmit={salvarRevisao}>
          <div>
            <label htmlFor={`revisao-${exame.id}`}>Observação da revisão</label>
            <textarea
              id={`revisao-${exame.id}`}
              value={observacao}
              onChange={(e) => setObservacao(e.target.value)}
              placeholder="Ex.: Valores dentro da normalidade."
            />
          </div>
          <Alerta tipo="erro">{erro}</Alerta>
          <div className={ui.acoes}>
            <button type="submit" className={`${ui.botao} ${ui.botaoPequeno}`} disabled={enviando}>
              {enviando ? 'Salvando…' : 'Marcar como revisado'}
            </button>
            <button
              type="button"
              className={`${ui.botaoSecundario} ${ui.botaoPequeno}`}
              onClick={() => setRevisando(false)}
              disabled={enviando}
            >
              Cancelar
            </button>
          </div>
        </form>
      )}
    </li>
  )
}

function FormularioExame({ jornadaId, solicitacoes, solicitacaoInicial, aoConcluir, aoCancelar }) {
  const inicialValida = solicitacoes.some((s) => String(s.id) === solicitacaoInicial) ? solicitacaoInicial : ''
  const [titulo, setTitulo] = useState(() => {
    const inicial = solicitacoes.find((s) => String(s.id) === inicialValida)
    return inicial ? inicial.descricao.slice(0, 150) : ''
  })
  const [solicitacaoId, setSolicitacaoId] = useState(inicialValida)
  const [arquivo, setArquivo] = useState(null)
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function aoEnviar(evento) {
    evento.preventDefault()
    if (!arquivo) {
      setErro('Escolha um arquivo para enviar.')
      return
    }
    setErro('')
    setEnviando(true)
    try {
      await enviarExame(jornadaId, { titulo, arquivo, solicitacaoId })
      await aoConcluir()
    } catch (erroEnvio) {
      setErro(mensagemDeErro(erroEnvio))
      setEnviando(false)
    }
  }

  return (
    <form className={`${ui.formulario} ${estilos.formularioDestaque}`} onSubmit={aoEnviar}>
      <h3>Enviar exame ou documento</h3>
      <Alerta tipo="erro">{erro}</Alerta>
      <div>
        <label htmlFor="exame-titulo">Título</label>
        <input
          id="exame-titulo"
          value={titulo}
          onChange={(e) => setTitulo(e.target.value)}
          required
          minLength={3}
          maxLength={150}
          placeholder="Ex.: Hemograma completo"
        />
      </div>
      {solicitacoes.length > 0 && (
        <div>
          <label htmlFor="exame-solicitacao">Atende a qual solicitação? (opcional)</label>
          <select id="exame-solicitacao" value={solicitacaoId} onChange={(e) => setSolicitacaoId(e.target.value)}>
            <option value="">Nenhuma</option>
            {solicitacoes.map((s) => (
              <option key={s.id} value={s.id}>
                {ROTULOS_TIPO_SOLICITACAO[s.tipo]}: {s.descricao.slice(0, 60)}
              </option>
            ))}
          </select>
          <p className={ui.ajuda}>A solicitação escolhida será marcada como atendida.</p>
        </div>
      )}
      <CampoArquivo id="exame-arquivo" arquivo={arquivo} onChange={setArquivo} obrigatorio />
      <div className={ui.acoes}>
        <button type="submit" className={ui.botao} disabled={enviando || !arquivo}>
          {enviando ? 'Enviando…' : 'Enviar'}
        </button>
        <button type="button" className={ui.botaoSecundario} onClick={aoCancelar} disabled={enviando}>
          Cancelar
        </button>
      </div>
    </form>
  )
}
