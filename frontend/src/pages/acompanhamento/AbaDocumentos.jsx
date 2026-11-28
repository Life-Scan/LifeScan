import { FileText, Pencil, Trash2, Upload } from 'lucide-react'
import { useState } from 'react'

import { mensagemDeErro } from '../../api/cliente'
import { editarDocumento, enviarDocumento, excluirDocumento, revisarDocumento } from '../../api/servicos'
import { useConfirmar } from '../../components/Confirmacao'
import { Alerta, Anexo, CampoArquivo, EstadoVazio, Etiqueta, IconeTipo, estilos as ui } from '../../components/ui'
import { cn } from '@/lib/utils'
import {
  ROTULOS_CATEGORIA,
  ROTULOS_STATUS_DOCUMENTO,
  ROTULOS_TIPO_SOLICITACAO,
  formatarData,
  formatarDataHora,
} from '../../utils/formatacao'
import { estilos } from './estilosAcompanhamento'

const TIPOS_COM_ENVIO = ['exame', 'orientacao_profissional']

// Categoria sugerida ao atender uma solicitação
const CATEGORIA_POR_TIPO = { exame: 'exame', orientacao_profissional: 'orientacao' }

export default function AbaDocumentos({
  documentos,
  solicitacoes,
  solicitacaoInicial,
  acompanhamento,
  usuario,
  ehMedico,
  ehParceiro,
  editavel,
  atualizar,
  filtro,
  setFiltro,
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
  const visiveis = documentos

  return (
    <div className={estilos.pilha}>
      <div className={ui.cartaoCabecalho} style={{ marginBottom: 0 }}>
        <h2 className={ui.tituloComIcone}>
          <IconeTipo tipo="documento">
            <FileText size={16} />
          </IconeTipo>
          {ehParceiro ? 'Meus envios' : 'Documentos'}
        </h2>
        {editavel && !formularioAberto && (
          <button type="button" className={ui.botao} onClick={() => setFormularioAberto(true)}>
            <Upload size={16} aria-hidden="true" />
            Enviar documento
          </button>
        )}
      </div>

      {formularioAberto && (
        <FormularioDocumento
          acompanhamentoId={acompanhamento.id}
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

      {(
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
        filtro ? (
          <EstadoVazio icone={FileText} titulo="Nenhum documento nesta categoria">
            Escolha &quot;Todos&quot; para ver os documentos das outras categorias.
          </EstadoVazio>
        ) : (
          <EstadoVazio icone={FileText} titulo={ehParceiro ? 'Nenhum envio ainda' : 'Nenhum documento enviado'}>
            {ehParceiro
              ? 'Os documentos que você enviar para este paciente aparecem aqui.'
              : 'Exames, laudos e outros arquivos enviados aparecem aqui para revisão.'}
          </EstadoVazio>
        )
      ) : (
        <ul className={ui.lista}>
          {visiveis.map((documento) => (
            <ItemDocumento
              key={documento.id}
              documento={documento}
              solicitacao={solicitacoes.find((s) => s.id === documento.solicitacao_id)}
              podeRevisar={ehMedico && editavel}
              // Espelha o backend (que é quem garante): o médico altera qualquer um; o parceiro, os próprios
              podeAlterar={editavel && (ehMedico || (ehParceiro && documento.enviado_por.id === usuario.id))}
              atualizar={atualizar}
            />
          ))}
        </ul>
      )}
    </div>
  )
}

function ItemDocumento({ documento, solicitacao, podeRevisar, podeAlterar, atualizar }) {
  const confirmar = useConfirmar()
  const [revisando, setRevisando] = useState(false)
  const [editando, setEditando] = useState(false)
  const [observacao, setObservacao] = useState(documento.observacao_revisao || '')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)
  const revisado = documento.status === 'revisado'

  async function excluir() {
    const confirmado = await confirmar({
      titulo: 'Excluir este documento?',
      // A lista de solicitações desta aba só traz as pendentes, então o vínculo vem do próprio documento
      mensagem: documento.solicitacao_id
        ? `"${documento.titulo}" e o arquivo serão apagados, e a solicitação que ele atendia volta a ficar pendente.`
        : `"${documento.titulo}" e o arquivo serão apagados. Não dá para desfazer.`,
      rotuloConfirmar: 'Excluir documento',
      perigo: true,
    })
    if (!confirmado) return
    setErro('')
    setEnviando(true)
    try {
      await excluirDocumento(documento.id)
      await atualizar()
    } catch (erroExclusao) {
      setErro(mensagemDeErro(erroExclusao))
      setEnviando(false)
    }
  }

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
    <li className={ui.itemListaDocumento}>
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

      {(podeRevisar || podeAlterar) && !revisando && !editando && (
        <div className={cn(estilos.acoesItem, ui.acoes)}>
          {podeRevisar && (
            <button type="button" className={cn(ui.botaoSecundario, ui.botaoPequeno)} onClick={() => setRevisando(true)}>
              <Pencil size={14} aria-hidden="true" />
              {revisado ? 'Editar revisão' : 'Revisar documento'}
            </button>
          )}
          {podeAlterar && (
            <>
              <button
                type="button"
                className={cn(ui.botaoSecundario, ui.botaoPequeno)}
                onClick={() => setEditando(true)}
                disabled={enviando}
              >
                <Pencil size={14} aria-hidden="true" />
                Editar
              </button>
              <button
                type="button"
                className={cn(ui.botaoPerigo, ui.botaoPequeno)}
                onClick={excluir}
                disabled={enviando}
              >
                <Trash2 size={14} aria-hidden="true" />
                {enviando ? 'Excluindo…' : 'Excluir'}
              </button>
            </>
          )}
        </div>
      )}

      {!editando && !revisando && <Alerta tipo="erro">{erro}</Alerta>}

      {editando && (
        <FormularioEdicao
          documento={documento}
          aoConcluir={async () => {
            setEditando(false)
            await atualizar()
          }}
          aoCancelar={() => setEditando(false)}
        />
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
            <button type="submit" className={cn(ui.botao, ui.botaoPequeno)} disabled={enviando}>
              {enviando ? 'Salvando…' : 'Marcar como revisado'}
            </button>
            <button
              type="button"
              className={cn(ui.botaoSecundario, ui.botaoPequeno)}
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

/** Edição básica no próprio item: título e categoria. O arquivo não muda (para trocar, exclua e envie). */
function FormularioEdicao({ documento, aoConcluir, aoCancelar }) {
  const [titulo, setTitulo] = useState(documento.titulo)
  const [categoria, setCategoria] = useState(documento.categoria)
  const [erro, setErro] = useState('')
  const [salvando, setSalvando] = useState(false)

  async function salvar(evento) {
    evento.preventDefault()
    setErro('')
    setSalvando(true)
    try {
      await editarDocumento(documento.id, { titulo, categoria })
      await aoConcluir()
    } catch (erroEdicao) {
      setErro(mensagemDeErro(erroEdicao))
      setSalvando(false)
    }
  }

  return (
    <form className={`${ui.formulario} ${estilos.acoesItem}`} onSubmit={salvar}>
      <div className={ui.linhaCampos}>
        <div>
          <label htmlFor={`edicao-titulo-${documento.id}`}>Título</label>
          <input
            id={`edicao-titulo-${documento.id}`}
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            required
            minLength={3}
            maxLength={150}
          />
        </div>
        <div>
          <label htmlFor={`edicao-categoria-${documento.id}`}>Categoria</label>
          <select
            id={`edicao-categoria-${documento.id}`}
            value={categoria}
            onChange={(e) => setCategoria(e.target.value)}
          >
            {Object.entries(ROTULOS_CATEGORIA).map(([valor, rotulo]) => (
              <option key={valor} value={valor}>
                {rotulo}
              </option>
            ))}
          </select>
        </div>
      </div>
      <p className={ui.ajuda}>Para trocar o arquivo, exclua este documento e envie o novo.</p>
      <Alerta tipo="erro">{erro}</Alerta>
      <div className={ui.acoes}>
        <button type="submit" className={cn(ui.botao, ui.botaoPequeno)} disabled={salvando}>
          {salvando ? 'Salvando…' : 'Salvar'}
        </button>
        <button type="button" className={cn(ui.botaoSecundario, ui.botaoPequeno)} onClick={aoCancelar} disabled={salvando}>
          Cancelar
        </button>
      </div>
    </form>
  )
}

function FormularioDocumento({
  acompanhamentoId,
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
      await enviarDocumento(acompanhamentoId, { titulo, categoria, arquivo, solicitacaoId })
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
