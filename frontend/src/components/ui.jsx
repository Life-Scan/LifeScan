/** Componentes pequenos de interface usados em várias páginas. */
import { useRef, useState } from 'react'

import { mensagemDeErro } from '../api/cliente'
import {
  ACCEPT_ARQUIVOS,
  EXTENSOES_PERMITIDAS,
  TAMANHO_MAXIMO_MB,
  baixarArquivo,
  podeVisualizar,
  validarArquivo,
  visualizarArquivo,
} from '../utils/arquivos'
import { formatarTamanho } from '../utils/formatacao'
import estilos from './ui.module.css'

export { estilos }

/** variante: neutra | perigo | alerta | sucesso | info | primaria */
export function Etiqueta({ variante = 'neutra', children }) {
  const classe = variante === 'neutra' ? estilos.etiqueta : `${estilos.etiqueta} ${estilos[`etiqueta_${variante}`]}`
  return <span className={classe}>{children}</span>
}

/** tipo: erro | sucesso | info | alerta */
export function Alerta({ tipo = 'info', children }) {
  if (!children) return null
  return (
    <div className={`${estilos.alerta} ${estilos[`alerta_${tipo}`]}`} role={tipo === 'erro' ? 'alert' : 'status'}>
      {children}
    </div>
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

export function EstadoVazio({ children }) {
  return <div className={estilos.vazio}>{children}</div>
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
        <span className={estilos.nomeArquivo}>
          {arquivo.name} ({formatarTamanho(arquivo.size)}){' '}
          <button type="button" className={estilos.botaoLink} onClick={limpar}>
            remover
          </button>
        </span>
      ) : (
        <span className={estilos.ajuda}>
          {EXTENSOES_PERMITIDAS.join(', ')} · até {TAMANHO_MAXIMO_MB} MB
        </span>
      )}
      <Alerta tipo="erro">{erro}</Alerta>
    </div>
  )
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
      <span aria-hidden="true">📎</span>
      <span className={estilos.anexoNome}>{arquivo.nome_original}</span>
      <span className={estilos.suave}>({formatarTamanho(arquivo.tamanho_bytes)})</span>
      {podeVisualizar(arquivo) && (
        <button type="button" className={estilos.botaoLink} onClick={() => executar(visualizarArquivo)}>
          visualizar
        </button>
      )}
      <button type="button" className={estilos.botaoLink} onClick={() => executar(baixarArquivo)}>
        baixar
      </button>
      {erro && <span className={estilos.suave}>{erro}</span>}
    </span>
  )
}
