import { obterArquivo } from '../api/servicos'

// Mesmas regras do backend (RNF01); o backend continua sendo quem decide
export const EXTENSOES_PERMITIDAS = ['pdf', 'png', 'jpg', 'jpeg', 'webp', 'dcm', 'txt']
export const TAMANHO_MAXIMO_MB = Number(import.meta.env.VITE_MAX_UPLOAD_MB) || 30
export const ACCEPT_ARQUIVOS = EXTENSOES_PERMITIDAS.map((extensao) => `.${extensao}`).join(',')

/** Devolve uma mensagem de erro, ou null se o arquivo puder ser enviado. */
export function validarArquivo(arquivo) {
  const extensao = arquivo.name.includes('.') ? arquivo.name.split('.').pop().toLowerCase() : ''
  if (!EXTENSOES_PERMITIDAS.includes(extensao)) {
    return `Formato não permitido. Use: ${EXTENSOES_PERMITIDAS.join(', ')}.`
  }
  if (arquivo.size > TAMANHO_MAXIMO_MB * 1024 * 1024) {
    return `Arquivo muito grande. O tamanho máximo é ${TAMANHO_MAXIMO_MB} MB.`
  }
  if (arquivo.size === 0) {
    return 'O arquivo está vazio.'
  }
  return null
}

/** Baixa o arquivo pelo endpoint autenticado e dispara o "salvar como" do navegador. */
export async function baixarArquivo({ id, nome_original: nome }) {
  const blob = await obterArquivo(id)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = nome
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 10_000)
}

const TIPOS_VISUALIZAVEIS = ['application/pdf', 'image/png', 'image/jpeg', 'image/webp', 'text/plain']

export const podeVisualizar = (arquivo) => TIPOS_VISUALIZAVEIS.includes(arquivo.tipo_mime)

/** Abre o arquivo em outra aba (PDF, imagens e texto). */
export async function visualizarArquivo({ id }) {
  // A aba é aberta antes da requisição para não ser barrada pelo bloqueador de pop-ups
  const aba = window.open('', '_blank')
  try {
    const blob = await obterArquivo(id, true)
    const url = URL.createObjectURL(blob)
    if (aba) {
      aba.location.href = url
    } else {
      window.location.assign(url)
    }
    setTimeout(() => URL.revokeObjectURL(url), 60_000)
  } catch (erro) {
    aba?.close()
    throw erro
  }
}
