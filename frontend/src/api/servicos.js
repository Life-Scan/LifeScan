/** Funções de acesso à API, uma por rota do backend. Todas devolvem os dados da resposta. */
import { api } from './cliente'

const dados = (promessa) => promessa.then((resposta) => resposta.data)

// Autenticação
export const entrar = (email, senha) => dados(api.post('/auth/login', { email, senha }))
export const obterUsuarioAtual = () => dados(api.get('/auth/me'))
export const trocarSenha = (senhaAtual, novaSenha) =>
  dados(api.post('/auth/change-password', { senha_atual: senhaAtual, nova_senha: novaSenha }))
export const esqueciSenha = (email) => dados(api.post('/auth/forgot-password', { email }))

// Contas de pacientes e parceiros (médico)
export const listarContas = (tipo) => dados(api.get('/users', { params: tipo ? { tipo } : {} }))
export const criarConta = (conta) => dados(api.post('/users', conta))
export const atualizarConta = (id, alteracoes) => dados(api.patch(`/users/${id}`, alteracoes))
export const reenviarAcesso = (id) => dados(api.post(`/users/${id}/resend-access`))

// Jornadas
export const listarJornadas = () => dados(api.get('/journeys'))
export const obterJornada = (id) => dados(api.get(`/journeys/${id}`))
export const criarJornada = (jornada) => dados(api.post('/journeys', jornada))
export const alterarPasso = (id, passo) => dados(api.patch(`/journeys/${id}/step`, { passo_atual: passo }))
export const alterarStatusJornada = (id, status) => dados(api.patch(`/journeys/${id}/status`, { status }))

// Consultas
export const listarConsultas = (jornadaId) => dados(api.get(`/journeys/${jornadaId}/consultations`))
export const registrarConsulta = (jornadaId, consulta) =>
  dados(api.post(`/journeys/${jornadaId}/consultations`, consulta))

// Solicitações
export const listarSolicitacoes = (jornadaId) => dados(api.get(`/journeys/${jornadaId}/requests`))
export const criarSolicitacao = (jornadaId, solicitacao) =>
  dados(api.post(`/journeys/${jornadaId}/requests`, solicitacao))
export const concluirSolicitacao = (id) => dados(api.patch(`/requests/${id}/complete`))
export const cancelarSolicitacao = (id) => dados(api.patch(`/requests/${id}/cancel`))

// Exames
export const listarExames = (jornadaId) => dados(api.get(`/journeys/${jornadaId}/exams`))
export function enviarExame(jornadaId, { titulo, arquivo, solicitacaoId }) {
  const formulario = new FormData()
  formulario.append('titulo', titulo)
  formulario.append('arquivo', arquivo)
  if (solicitacaoId) formulario.append('solicitacao_id', solicitacaoId)
  return dados(api.post(`/journeys/${jornadaId}/exams`, formulario))
}
export const revisarExame = (id, observacao) =>
  dados(api.patch(`/exams/${id}/review`, { observacao_revisao: observacao }))

// Linha do tempo e painel
export const obterLinhaDoTempo = (jornadaId, tipos) =>
  dados(api.get(`/journeys/${jornadaId}/timeline`, { params: tipos?.length ? { tipos: tipos.join(',') } : {} }))
export const obterPendencias = () => dados(api.get('/dashboard/pending'))

// Arquivos: o download exige o token, então buscamos o conteúdo como blob
export async function obterArquivo(arquivoId, inline = false) {
  const resposta = await api.get(`/files/${arquivoId}/download`, {
    params: inline ? { inline: true } : {},
    responseType: 'blob',
  })
  return resposta.data
}
