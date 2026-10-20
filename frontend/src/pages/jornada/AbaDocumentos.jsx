import { FileText, Pencil, Upload } from 'lucide-react'
import { useState } from 'react'

import { mensagemDeErro } from '../../api/cliente'
import { enviarDocumento, revisarDocumento } from '../../api/servicos'
import { Alerta, Anexo, CampoArquivo, EstadoVazio, Etiqueta, estilos as ui } from '../../components/ui'
import {
  ROTULOS_CATEGORIA,
  ROTULOS_STATUS_DOCUMENTO,
  ROTULOS_TIPO_SOLICITACAO,
  formatarData,
  formatarDataHora,
} from '../../utils/formatacao'
import estilos from './Jornada.module.css'

const TIPOS_COM_ENVIO = ['exame', 'orientacao_profissional']

// Categoria sugerida ao atender uma solicitação
const CATEGORIA_POR_TIPO = { exame: 'exame', orientacao_profissional: 'orientacao' }

export default function AbaDocumentos({
  documentos,
  solicitacoes,
  solicitacaoInicial,
  jornada,
  usuario,
  ehMedico,
  ehParceiro,
  editavel,
  atualizar,
}) {
  // Solicitações que este usuário pode atender com um envio: o médico, qualquer uma;
  // paciente e parceiro, só as destinadas a eles
  const atendiveis = solicitacoes.filter(
    (s) =>
      s.status === 'pendente' &&
      TIPOS_COM_ENVIO.includes(s.tipo) &&
      (ehMedico || s.destinatario.id === usuario.id),
  )
  const [formularioAberto, setFormularioAberto] = useState(Boolean(solicitacaoInicial) && editavel)
  const [filtro, setFiltro] = useState('')

  const categoriasPresentes = [...new Set(documentos.map((d) => d.categoria))]
  const visiveis = filtro ? documentos.filter((d) => d.categoria === filtro) : documentos

  return (
    <div className={estilos.pilha}>
      <div className={ui.cartaoCabecalho} style={{ marginBottom: 0 }}>
        <h2>{ehParceiro ? 'Meus envios' : 'Documentos'}</h2>
        {editavel && !formularioAberto && (
          <button type="button" className={ui.botao} onClick={() => setFormularioAberto(true)}>
            <Upload size={16} aria-hidden="true" />
            Enviar documento
          </button>
        )}
      </div>

      {formularioAberto && (
        <FormularioDocumento
          jornadaId={jornada.id}
          solicitacoes={atendiveis}
          solicitacaoInicial={solicitacaoInicial}
          mostrarDestinatario={ehMedico}
          categoriaPadrao={ehParceiro ? 'orientacao' : 'exame'}
          aoConcluir={async () => {
            setFormularioAberto(false)
            await atualizar()
          }}
          aoCancelar={() => setFormularioAberto(false)}
        />
      )}

      {categoriasPresentes.length > 1 && (
        <div className={estilos.filtros} role="group" aria-label="Filtrar por categoria">
          <button
            type="button"
            className={filtro === '' ? estilos.filtroAtivo : estilos.filtro}
            onClick={() => setFiltro('')}
            aria-pressed={filtro === ''}
          >
            Todos
          </button>
          {Object.keys(ROTULOS_CATEGORIA)
            .filter((categoria) => categoriasPresentes.includes(categoria))
            .map((categoria) => (
              <button
                key={categoria}
                type="button"
                className={filtro === categoria ? estilos.filtroAtivo : estilos.filtro}
                onClick={() => setFiltro(categoria)}
                aria-pressed={filtro === categoria}
              >
                {ROTULOS_CATEGORIA[categoria]}
              </button>
            ))}
        </div>
      )}

      {visiveis.length === 0 ? (
        <EstadoVazio icone={FileText}>
          {ehParceiro ? 'Você ainda não enviou documentos para este paciente.' : 'Nenhum documento enviado.'}
        </EstadoVazio>
      ) : (
        <ul className={ui.lista}>
          {visiveis.map((documento) => (
            <ItemDocumento
              key={documento.id}
              documento={documento}
              solicitacao={solicitacoes.find((s) => s.id === documento.solicitacao_id)}
              podeRevisar={ehMedico && editavel}
              atualizar={atualizar}
            />
          ))}
        </ul>
      )}
    </div>
  )
}

function ItemDocumento({ documento, solicitacao, podeRevisar, atualizar }) {
  const [revisando, setRevisando] = useState(false)
  const [observacao, setObservacao] = useState(documento.observacao_revisao || '')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)
  const revisado = documento.status === 'revisado'

  async function salvarRevisao(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      await revisarDocumento(documento.id, observacao.trim() || null)
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
        <div className={ui.acoes}>
          <strong>{documento.titulo}</strong>
          <Etiqueta variante="info">{ROTULOS_CATEGORIA[documento.categoria]}</Etiqueta>
        </div>
        <Etiqueta variante={revisado ? 'sucesso' : 'alerta'}>{ROTULOS_STATUS_DOCUMENTO[documento.status]}</Etiqueta>
      </div>
      <div className={estilos.meta}>
        <span>Enviado por {documento.enviado_por.nome}</span>
        <span>{formatarDataHora(documento.criado_em)}</span>
        {solicitacao && <span>Atende: {ROTULOS_TIPO_SOLICITACAO[solicitacao.tipo].toLowerCase()}</span>}
      </div>
      <div className={estilos.acoesItem}>
        <Anexo arquivo={documento.arquivo} />
      </div>

      {revisado && !revisando && (
        <div className={estilos.revisao}>
          <strong>Revisão do médico</strong> <span className={ui.suave}>({formatarData(documento.revisado_em)})</span>
          <p className={estilos.texto}>{documento.observacao_revisao || 'Revisado sem observações.'}</p>
        </div>
      )}

      {podeRevisar && !revisando && (
        <div className={estilos.acoesItem}>
          <button type="button" className={`${ui.botaoSecundario} ${ui.botaoPequeno}`} onClick={() => setRevisando(true)}>
            <Pencil size={14} aria-hidden="true" />
            {revisado ? 'Editar revisão' : 'Revisar documento'}
          </button>
        </div>
      )}

      {revisando && (
        <form className={`${ui.formulario} ${estilos.acoesItem}`} onSubmit={salvarRevisao}>
          <div>
            <label htmlFor={`revisao-${documento.id}`}>Observação da revisão</label>
            <textarea
              id={`revisao-${documento.id}`}
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

function FormularioDocumento({
  jornadaId,
  solicitacoes,
  solicitacaoInicial,
  mostrarDestinatario,
  categoriaPadrao,
  aoConcluir,
  aoCancelar,
}) {
  const inicial = solicitacoes.find((s) => String(s.id) === solicitacaoInicial)
  const [titulo, setTitulo] = useState(inicial ? inicial.descricao.slice(0, 150) : '')
  const [categoria, setCategoria] = useState(inicial ? CATEGORIA_POR_TIPO[inicial.tipo] : categoriaPadrao)
  const [solicitacaoId, setSolicitacaoId] = useState(inicial ? String(inicial.id) : '')
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
      await enviarDocumento(jornadaId, { titulo, categoria, arquivo, solicitacaoId })
      await aoConcluir()
    } catch (erroEnvio) {
      setErro(mensagemDeErro(erroEnvio))
      setEnviando(false)
    }
  }

  return (
    <form className={`${ui.formulario} ${estilos.formularioDestaque}`} onSubmit={aoEnviar}>
      <h3>Enviar documento</h3>
      <Alerta tipo="erro">{erro}</Alerta>
      <div className={ui.linhaCampos}>
        <div>
          <label htmlFor="documento-titulo">Título</label>
          <input
            id="documento-titulo"
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            required
            minLength={3}
            maxLength={150}
            placeholder="Ex.: Hemograma completo"
          />
        </div>
        <div>
          <label htmlFor="documento-categoria">Categoria</label>
          <select id="documento-categoria" value={categoria} onChange={(e) => setCategoria(e.target.value)}>
            {Object.entries(ROTULOS_CATEGORIA).map(([valor, rotulo]) => (
              <option key={valor} value={valor}>
                {rotulo}
              </option>
            ))}
          </select>
        </div>
      </div>
      {solicitacoes.length > 0 && (
        <div>
          <label htmlFor="documento-solicitacao">Atende a qual solicitação? (opcional)</label>
          <select
            id="documento-solicitacao"
            value={solicitacaoId}
            onChange={(e) => setSolicitacaoId(e.target.value)}
          >
            <option value="">Nenhuma</option>
            {solicitacoes.map((s) => (
              <option key={s.id} value={s.id}>
                {ROTULOS_TIPO_SOLICITACAO[s.tipo]}: {s.descricao.slice(0, 60)}
                {mostrarDestinatario ? ` (para ${s.destinatario.nome})` : ''}
              </option>
            ))}
          </select>
          <p className={ui.ajuda}>A solicitação escolhida será marcada como atendida.</p>
        </div>
      )}
      <CampoArquivo id="documento-arquivo" arquivo={arquivo} onChange={setArquivo} obrigatorio />
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
