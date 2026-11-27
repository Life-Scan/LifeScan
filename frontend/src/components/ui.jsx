/** Componentes pequenos de interface usados em várias páginas. */
import { CircleAlert, CircleCheck, Download, Eye, Inbox, Info, Paperclip, TriangleAlert } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { textoDeDocx, urlDaPrimeiraPaginaDePdf } from '../utils/previaDocumentos'
import { mensagemDeErro } from '../api/cliente'
import { obterArquivo, verificarQualidade } from '../api/servicos'
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
/*
 * Classes das peças compartilhadas (antes em ui.module.css). As páginas usam como antes:
 * className={ui.cartao}. Para somar o tamanho pequeno a um botão, use cn(), que resolve o
 * conflito de padding e fonte: className={cn(ui.botaoSecundario, ui.botaoPequeno)}.
 * Cada variante traz a string inteira (sem cn na definição): o cn descartaria border-l-* ao
 * encontrar um border-[cor] depois.
 */
const BOTAO =
  'inline-flex items-center justify-center gap-[0.45rem] px-4 py-[0.55rem] border rounded-raio-pequeno ' +
  'font-semibold text-[0.92rem] leading-[1.3] no-underline cursor-pointer whitespace-nowrap ' +
  'transition-[background,border-color] duration-150 ease-[ease] disabled:opacity-55 disabled:cursor-not-allowed'

const ITEM_LISTA = 'rounded-raio-pequeno px-4 py-[0.85rem]'

const ETIQUETA =
  'inline-flex items-center gap-1 px-[0.55rem] py-[0.12rem] rounded-full border ' +
  'text-[0.76rem] font-semibold leading-[1.4] whitespace-nowrap'

const ALERTA =
  'flex items-start gap-[0.55rem] px-[0.9rem] py-[0.7rem] rounded-raio-pequeno border text-[0.92rem] [&_svg]:mt-[0.15rem]'

const AVATAR = 'inline-grid place-items-center shrink-0 rounded-full font-bold tracking-[0.02em] select-none'

export const estilos = {
  cartao: 'bg-superficie border border-borda rounded-raio shadow-sombra p-5',
  cartaoCabecalho: 'flex items-center justify-between gap-3 flex-wrap mb-4',

  botao: `${BOTAO} border-primaria bg-primaria text-white hover:not-disabled:bg-primaria-escura hover:not-disabled:border-primaria-escura`,
  botaoSecundario: `${BOTAO} border-borda-forte bg-superficie text-texto hover:not-disabled:bg-superficie-suave hover:not-disabled:border-texto-suave`,
  botaoPerigo: `${BOTAO} border-borda-forte bg-superficie text-perigo hover:not-disabled:bg-perigo-clara hover:not-disabled:border-perigo`,
  botaoPerigoSolido: `${BOTAO} border-perigo bg-perigo text-white hover:not-disabled:bg-[#8f1c13] hover:not-disabled:border-[#8f1c13]`,
  // leading repetido: o cn() descarta o leading do botão quando um text-[tamanho] vem depois
  botaoPequeno: 'px-[0.7rem] py-[0.32rem] text-[0.84rem] leading-[1.3] gap-[0.35rem]',
  botaoLink:
    'inline-flex items-center gap-[0.3rem] bg-transparent border-0 p-0 text-primaria font-semibold cursor-pointer ' +
    'no-underline hover:underline hover:underline-offset-2',

  formulario: 'grid gap-[0.9rem]',
  linhaCampos: 'grid gap-[0.9rem] grid-cols-[repeat(auto-fit,minmax(200px,1fr))]',
  // ui-acoes não tem estilo: marca o grupo para a linhaComAcoes encontrar o filho direto
  acoes: 'ui-acoes flex flex-wrap items-center gap-2',
  ajuda: 'text-[0.85rem] text-texto-suave',
  suave: 'text-texto-suave',

  lista: 'list-none m-0 p-0 grid gap-[0.6rem]',
  itemLista: `${ITEM_LISTA} border border-borda bg-superficie`,
  itemListaDestaque: `${ITEM_LISTA} border border-[#f3c0ba] border-l-3 border-l-perigo bg-[#fff8f7]`,
  cabecalhoItem: 'flex justify-between items-start gap-3 flex-wrap',

  campoArquivo: 'grid gap-[0.35rem]',
  nomeArquivo: 'text-[0.88rem] text-texto-suave break-all',
  anexo:
    'inline-flex items-center gap-[0.6rem] flex-wrap max-w-full px-[0.65rem] py-[0.4rem] border border-borda ' +
    'rounded-raio-pequeno bg-superficie-suave text-[0.86rem] [&>svg]:text-texto-suave',
  anexoNome: 'font-semibold break-all',
  miniaturaBotao: 'p-0 border-0 bg-transparent leading-[0] cursor-zoom-in',
  miniaturaAnexo: 'size-[80px] object-cover border border-borda rounded-[8px] bg-superficie',
  // Arquivo sem imagem (.txt/.md/.docx): começo do conteúdo dentro do mesmo quadro
  miniaturaTexto:
    'box-border block p-[7px] font-mono text-[0.6rem] leading-[1.35] text-texto-suave overflow-hidden ' +
    '[word-break:break-word] whitespace-pre-wrap cursor-zoom-in',

  dialogo:
    'w-[min(440px,calc(100vw-2rem))] p-0 border-0 rounded-raio bg-superficie text-texto shadow-sombra-elevada ' +
    'backdrop:bg-[rgb(15_23_32/45%)]',
  dialogoConteudo: 'grid gap-[0.6rem] p-[1.4rem]',
  dialogoMensagem: 'text-texto-suave',
  dialogoAcoes: 'flex justify-end gap-2 flex-wrap mt-3',

  pessoa: 'flex items-center gap-3 min-w-0 flex-1 [&>div]:min-w-0',
  pessoaNome: 'flex items-center gap-2 flex-wrap font-semibold',
  // Ações à direita sem quebrar em telas largas; abaixo de 860px empilha
  linhaComAcoes:
    'flex justify-between items-center gap-4 [&>.ui-acoes]:shrink-0 [&>.ui-acoes]:flex-nowrap ' +
    'ate-860:flex-col ate-860:items-stretch ate-860:gap-[0.7rem] ate-860:[&>.ui-acoes]:flex-wrap',
}

const ETIQUETAS = {
  neutra: 'bg-superficie-suave text-texto-suave border-borda',
  perigo: 'bg-perigo-clara text-perigo border-transparent',
  alerta: 'bg-alerta-clara text-alerta border-transparent',
  sucesso: 'bg-sucesso-clara text-sucesso border-transparent',
  info: 'bg-info-clara text-info border-transparent',
  primaria: 'bg-primaria-clara text-primaria-escura border-transparent',
}

const ALERTAS = {
  erro: 'bg-perigo-clara text-perigo border-[#f5c2bc]',
  sucesso: 'bg-sucesso-clara text-sucesso border-[#b9e2c5]',
  info: 'bg-info-clara text-info border-[#bcd5f2]',
  alerta: 'bg-alerta-clara text-alerta border-[#f0d68f]',
}

const AVATARES = {
  paciente: 'bg-primaria-clara text-primaria-escura',
  parceiro: 'bg-info-clara text-info',
  colaborador: 'bg-alerta-clara text-alerta',
  medico: 'bg-primaria text-white',
}

/** variante: neutra | perigo | alerta | sucesso | info | primaria */
export function Etiqueta({ variante = 'neutra', children }) {
  return <span className={`${ETIQUETA} ${ETIQUETAS[variante]}`}>{children}</span>
}

const ICONES_ALERTA = { erro: CircleAlert, sucesso: CircleCheck, info: Info, alerta: TriangleAlert }

/** tipo: erro | sucesso | info | alerta */
export function Alerta({ tipo = 'info', children }) {
  if (!children) return null
  const Icone = ICONES_ALERTA[tipo]
  return (
    <div className={`${ALERTA} ${ALERTAS[tipo]}`} role={tipo === 'erro' ? 'alert' : 'status'}>
      <Icone size={17} aria-hidden="true" />
      <div>{children}</div>
    </div>
  )
}

/** Círculo com as iniciais do nome. tipo: paciente | parceiro | medico */
export function Avatar({ nome, tipo = 'paciente', grande = false }) {
  const tamanho = grande ? 'size-[2.9rem] text-base' : 'size-9 text-[0.82rem]'
  return (
    <span className={`${AVATAR} ${tamanho} ${AVATARES[tipo] ?? AVATARES.paciente}`} aria-hidden="true">
      {iniciais(nome)}
    </span>
  )
}

export function Carregando({ texto = 'Carregando…' }) {
  return (
    <div className="flex items-center gap-[0.6rem] py-4 text-texto-suave" role="status">
      <span
        className="size-[18px] rounded-full border-2 border-borda border-t-primaria animate-girar"
        aria-hidden="true"
      />
      {texto}
    </div>
  )
}

export function EstadoVazio({ icone: Icone = Inbox, children }) {
  return (
    <div className="grid justify-items-center gap-2 text-center px-4 py-7 text-texto-suave text-[0.92rem] bg-superficie-suave rounded-raio-pequeno [&_svg]:text-[#9aa7b3]">
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
/**
 * Legibilidade da imagem escolhida, pelo componente de IA (docs/ia-legibilidade.md). Só para image/*:
 * PDF, DOCX e TXT não passam pela IA. O resultado fica guardado junto do arquivo a que se refere, então
 * uma resposta atrasada de uma foto já trocada nunca aparece. Falha da API não mostra nada.
 */
function useQualidadeDaFoto(arquivo) {
  const [verificacao, setVerificacao] = useState({ arquivo: null, resultado: null })
  const ehImagem = Boolean(arquivo?.type?.startsWith('image/'))

  useEffect(() => {
    if (!ehImagem) return undefined
    let ativo = true
    verificarQualidade(arquivo)
      .then((resultado) => {
        if (ativo) setVerificacao({ arquivo, resultado })
      })
      // Falhou (rede, 415, 503): fica sem aviso; o envio segue normal
      .catch(() => {
        if (ativo) setVerificacao({ arquivo, resultado: null })
      })
    return () => {
      ativo = false
    }
  }, [arquivo, ehImagem])

  if (!ehImagem) return { verificando: false, resultado: null }
  const doArquivoAtual = verificacao.arquivo === arquivo
  return { verificando: !doArquivoAtual, resultado: doArquivoAtual ? verificacao.resultado : null }
}

export function CampoArquivo({ id, rotulo = 'Arquivo', arquivo, onChange, obrigatorio = false }) {
  const [erro, setErro] = useState('')
  const entrada = useRef(null)
  const qualidade = useQualidadeDaFoto(arquivo)
  const resultado = qualidade.resultado

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
          {qualidade.verificando && (
            <span className={estilos.ajuda} role="status">
              Verificando a qualidade da foto…
            </span>
          )}
          {/* O aviso só orienta: "alerta" (amarelo), não "erro", porque o envio continua liberado */}
          {resultado && !resultado.legivel && (
            <Alerta tipo="alerta">{resultado.motivo} Se preferir, você pode enviar assim mesmo.</Alerta>
          )}
          {/* Legível, mas com dica (ex.: documento inclinado) */}
          {resultado?.legivel && resultado.motivo && <Alerta tipo="info">{resultado.motivo}</Alerta>}
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
