/** Componentes pequenos de interface usados em várias páginas. */
import { CircleAlert, CircleCheck, Download, Eye, Inbox, Info, Paperclip, TriangleAlert } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { textoDeDocx, urlDaPrimeiraPaginaDePdf } from '../utils/previaDocumentos'
import { mensagemDeErro } from '../api/cliente'
import { obterArquivo } from '../api/servicos'
import {
  ACCEPT_ARQUIVOS,
  EXTENSOES_PERMITIDAS,
  TAMANHO_MAXIMO_MB,
  baixarArquivo,
  podeVisualizar,
  validarArquivo,
  visualizarArquivo,
} from '../utils/arquivos'
import { formatarTamanho, iniciais } from '../utils/formatacao'
import estilos from './ui.module.css'

export { estilos }

/** variante: neutra | perigo | alerta | sucesso | info | primaria */
export function Etiqueta({ variante = 'neutra', children }) {
  const classe = variante === 'neutra' ? estilos.etiqueta : `${estilos.etiqueta} ${estilos[`etiqueta_${variante}`]}`
  return <span className={classe}>{children}</span>
}

const ICONES_ALERTA = { erro: CircleAlert, sucesso: CircleCheck, info: Info, alerta: TriangleAlert }

/** tipo: erro | sucesso | info | alerta */
export function Alerta({ tipo = 'info', children }) {
  if (!children) return null
  const Icone = ICONES_ALERTA[tipo]
  return (
    <div className={`${estilos.alerta} ${estilos[`alerta_${tipo}`]}`} role={tipo === 'erro' ? 'alert' : 'status'}>
      <Icone size={17} aria-hidden="true" />
      <div>{children}</div>
    </div>
  )
}

/** Círculo com as iniciais do nome. tipo: paciente | parceiro | medico */
export function Avatar({ nome, tipo = 'paciente', grande = false }) {
  const classes = [estilos.avatar, estilos[`avatar_${tipo}`], grande ? estilos.avatar_grande : '']
  return (
    <span className={classes.filter(Boolean).join(' ')} aria-hidden="true">
      {iniciais(nome)}
    </span>
  )
}

export function Carregando({ texto = 'Carregando…' }) {
  return (
    <div className={estilos.carregando} role="status">
      <span className={estilos.girando} aria-hidden="true" />
      {texto}
    </div>
  )
}

export function EstadoVazio({ icone: Icone = Inbox, children }) {
  return (
    <div className={estilos.vazio}>
      <Icone size={26} strokeWidth={1.5} aria-hidden="true" />
      <div>{children}</div>
    </div>
  )
}

/** Erro de carregamento vindo do polling, com a mensagem do backend. */
export function ErroCarregamento({ erro }) {
  if (!erro) return null
  return <Alerta tipo="erro">{mensagemDeErro(erro, 'Não foi possível carregar os dados.')}</Alerta>
}

/**
 * Seletor de arquivo com validação imediata de extensão e tamanho (RNF01).
 * Chama onChange(arquivo | null) apenas com arquivos válidos.
 */
export function CampoArquivo({ id, rotulo = 'Arquivo', arquivo, onChange, obrigatorio = false }) {
  const [erro, setErro] = useState('')
  const entrada = useRef(null)

  function aoEscolher(evento) {
    const escolhido = evento.target.files?.[0] ?? null
    if (!escolhido) {
      onChange(null)
      return
    }
    const problema = validarArquivo(escolhido)
    setErro(problema || '')
    if (problema) {
      evento.target.value = ''
      onChange(null)
    } else {
      onChange(escolhido)
    }
  }

  function limpar() {
    if (entrada.current) entrada.current.value = ''
    setErro('')
    onChange(null)
  }

  return (
    <div className={estilos.campoArquivo}>
      <label htmlFor={id}>{rotulo}</label>
      <input
        ref={entrada}
        id={id}
        type="file"
        accept={ACCEPT_ARQUIVOS}
        onChange={aoEscolher}
        required={obrigatorio}
      />
      {arquivo ? (
        <>
          <span className={estilos.nomeArquivo}>
            {arquivo.name} ({formatarTamanho(arquivo.size)}){' '}
            <button type="button" className={estilos.botaoLink} onClick={limpar}>
              remover
            </button>
          </span>
          <MiniaturaEscolhida arquivo={arquivo} />
        </>
      ) : (
        <span className={estilos.ajuda}>
          {EXTENSOES_PERMITIDAS.join(', ')} · até {TAMANHO_MAXIMO_MB} MB
        </span>
      )}
      <Alerta tipo="erro">{erro}</Alerta>
    </div>
  )
}

const EXTENSOES_IMAGEM = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
const EXTENSOES_TEXTO = ['.txt', '.md']
const EXTENSOES_PDF = ['.pdf']
const EXTENSOES_DOCX = ['.docx']

function terminaEm(nome, extensoes) {
  const minusculo = nome.toLowerCase()
  return extensoes.some((extensao) => minusculo.endsWith(extensao))
}

function eImagem(nome) {
  return terminaEm(nome, EXTENSOES_IMAGEM)
}

function eTexto(nome) {
  return terminaEm(nome, EXTENSOES_TEXTO)
}

function temMiniatura(arquivo) {
  const nome = arquivo.nome_original
  return eImagem(nome) || eTexto(nome) || terminaEm(nome, EXTENSOES_PDF) || terminaEm(nome, EXTENSOES_DOCX)
}

// Blob baixado por id, convertido para miniatura: as remontagens (filtros trocando
// a lista) reaproveitam em vez de refazer o download
const conteudosDeAnexos = new Map()

function conteudoDeAnexo(arquivo) {
  let promessa = conteudosDeAnexos.get(arquivo.id)
  if (promessa) return promessa
  const nome = arquivo.nome_original
  promessa = (async () => {
    const blob = await obterArquivo(arquivo.id, true)
    if (eImagem(nome)) return { url: URL.createObjectURL(blob) }
    if (terminaEm(nome, EXTENSOES_PDF)) return { url: await urlDaPrimeiraPaginaDePdf(blob) }
    const inteiro = terminaEm(nome, EXTENSOES_DOCX) ? await textoDeDocx(blob) : await blob.text()
    return { texto: inteiro.slice(0, 300) }
  })()
  conteudosDeAnexos.set(arquivo.id, promessa)
  promessa.catch(() => conteudosDeAnexos.delete(arquivo.id)) // falhou: permitir tentar de novo
  return promessa
}

function CorpoMiniatura({ conteudo, nome }) {
  if (!conteudo) return <Paperclip size={15} aria-hidden="true" />
  if (conteudo.url) {
    return <img src={conteudo.url} alt={`Miniatura de ${nome}`} className={estilos.miniaturaAnexo} />
  }
  return (
    <span className={`${estilos.miniaturaAnexo} ${estilos.miniaturaTexto}`} aria-hidden="true">
      {conteudo.texto}
    </span>
  )
}

/** Miniatura de anexo já enviado: imagem pequena ou começo do texto (baixado com o token). */
function MiniaturaDeAnexo({ arquivo, aoAbrir }) {
  const conteudoInicial = conteudosDeAnexos.get(arquivo.id)
  const [conteudo, definConteudo] = useState(conteudoInicial)

  useEffect(() => {
    let atual = true
    conteudoDeAnexo(arquivo)
      .then((resolvido) => {
        if (atual) definConteudo(resolvido)
      })
      .catch(() => {}) // ficar sem miniatura não atrapalha: os botões de visualizar e baixar continuam
    return () => {
      atual = false
    }
  }, [arquivo])

  if (!conteudo) return <Paperclip size={15} aria-hidden="true" />
  return (
    <button type="button" className={estilos.miniaturaBotao} onClick={aoAbrir} title="Visualizar">
      <CorpoMiniatura conteudo={conteudo} nome={arquivo.nome_original} />
    </button>
  )
}

/** Miniatura local do arquivo acabado de escolher, antes de enviar. */
function MiniaturaEscolhida({ arquivo }) {
  const [conteudo, definConteudo] = useState(null)

  useEffect(() => {
    let atual = true
    let urlLocal = null
    async function preparar() {
      if (eImagem(arquivo.name)) {
        urlLocal = URL.createObjectURL(arquivo)
        if (atual) definConteudo({ url: urlLocal })
      } else if (terminaEm(arquivo.name, EXTENSOES_PDF)) {
        const url = await urlDaPrimeiraPaginaDePdf(arquivo)
        if (atual) definConteudo({ url })
      } else if (eTexto(arquivo.name) || terminaEm(arquivo.name, EXTENSOES_DOCX)) {
        const inteiro = eTexto(arquivo.name) ? await arquivo.text() : await textoDeDocx(arquivo)
        if (atual) definConteudo({ texto: inteiro.slice(0, 300) })
      } else {
        definConteudo(null)
      }
    }
    preparar()
    return () => {
      atual = false
      if (urlLocal) URL.revokeObjectURL(urlLocal)
    }
  }, [arquivo])

  if (!conteudo) return null
  return <CorpoMiniatura conteudo={conteudo} nome={arquivo.name} />
}

/** Nome do arquivo com ações de visualizar e baixar (download autenticado). */
export function Anexo({ arquivo }) {
  const [erro, setErro] = useState('')

  async function executar(acao) {
    setErro('')
    try {
      await acao(arquivo)
    } catch (erroAcao) {
      setErro(mensagemDeErro(erroAcao, 'Não foi possível abrir o arquivo.'))
    }
  }

  return (
    <span className={estilos.anexo}>
      {temMiniatura(arquivo) ? (
        <MiniaturaDeAnexo arquivo={arquivo} aoAbrir={() => executar(visualizarArquivo)} />
      ) : (
        <Paperclip size={15} aria-hidden="true" />
      )}
      <span className={estilos.anexoNome}>{arquivo.nome_original}</span>
      <span className={estilos.suave}>({formatarTamanho(arquivo.tamanho_bytes)})</span>
      {podeVisualizar(arquivo) && (
        <button type="button" className={estilos.botaoLink} onClick={() => executar(visualizarArquivo)}>
          <Eye size={14} aria-hidden="true" />
          Visualizar
        </button>
      )}
      <button type="button" className={estilos.botaoLink} onClick={() => executar(baixarArquivo)}>
        <Download size={14} aria-hidden="true" />
        Baixar
      </button>
      {erro && <span className={estilos.suave}>{erro}</span>}
    </span>
  )
}
