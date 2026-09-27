import axios from 'axios'

export const URL_API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export const CHAVE_TOKEN = 'lifescan_token'

export const api = axios.create({ baseURL: URL_API })

// Injeta o token JWT em todas as requisições
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(CHAVE_TOKEN)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Em 401 (token ausente, inválido ou expirado), limpa a sessão e volta ao login.
// O próprio login devolve 401 para senha errada; nesse caso a tela trata o erro.
api.interceptors.response.use(
  (resposta) => resposta,
  (erro) => {
    const ehLogin = erro.config?.url?.startsWith('/auth/login')
    if (erro.response?.status === 401 && !ehLogin) {
      localStorage.removeItem(CHAVE_TOKEN)
      if (window.location.pathname !== '/login') {
        window.location.assign('/login?sessao=expirada')
      }
    }
    return Promise.reject(erro)
  },
)

/** Extrai uma mensagem legível (em português) de um erro do axios. */
export function mensagemDeErro(erro, padrao = 'Não foi possível concluir a operação.') {
  if (!erro?.response) {
    return 'Não foi possível conectar ao servidor. Verifique se a API está no ar.'
  }
  const dados = erro.response.data
  if (Array.isArray(dados?.erros) && dados.erros.length > 0) {
    return dados.erros
      .map(({ campo, mensagem }) => (campo ? `${rotuloCampo(campo)}: ${mensagem}` : mensagem))
      .join(' ')
  }
  if (typeof dados?.detail === 'string') {
    return dados.detail
  }
  return padrao
}

const ROTULOS_CAMPOS = {
  nome: 'Nome',
  email: 'Email',
  senha: 'Senha',
  papel: 'Tipo de conta',
  titulo: 'Título',
  descricao: 'Descrição',
  prazo: 'Prazo',
  data: 'Data',
  tipo: 'Tipo',
  arquivo: 'Arquivo',
}

function rotuloCampo(campo) {
  const ultimo = campo.split('.').pop()
  return ROTULOS_CAMPOS[ultimo] || ultimo
}
