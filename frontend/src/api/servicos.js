/** Funções de acesso à API, uma por rota do backend. Todas devolvem os dados da resposta. */
import { api } from './cliente'

const dados = (promessa) => promessa.then((resposta) => resposta.data)

// Autenticação
export const entrar = (email, senha) => dados(api.post('/auth/login', { email, senha }))
export const obterUsuarioAtual = () => dados(api.get('/auth/me'))
export const definirSenha = (novaSenha) => dados(api.post('/auth/set-password', { nova_senha: novaSenha }))
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

// Ficha do paciente e parceiros da jornada
export const obterFicha = (jornadaId) => dados(api.get(`/journeys/${jornadaId}/patient-record`))
export const salvarFicha = (jornadaId, ficha) => dados(api.put(`/journeys/${jornadaId}/patient-record`, ficha))
export const listarParceirosDaJornada = (jornadaId) => dados(api.get(`/journeys/${jornadaId}/partners`))
export const atribuirParceiro = (jornadaId, parceiroId) =>
  dados(api.post(`/journeys/${jornadaId}/partners`, { parceiro_id: parceiroId }))
export const removerParceiro = (jornadaId, parceiroId) =>
  dados(api.delete(`/journeys/${jornadaId}/partners/${parceiroId}`))

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

// Documentos (exames, laudos, planos alimentares, planos de treino, orientações...)
export const listarDocumentos = (jornadaId) => dados(api.get(`/journeys/${jornadaId}/documents`))
export function enviarDocumento(jornadaId, { titulo, categoria, arquivo, solicitacaoId }) {
  const formulario = new FormData()
  formulario.append('titulo', titulo)
  formulario.append('categoria', categoria)
  formulario.append('arquivo', arquivo)
  if (solicitacaoId) formulario.append('solicitacao_id', solicitacaoId)
  return dados(api.post(`/journeys/${jornadaId}/documents`, formulario))
}
export const revisarDocumento = (id, observacao) =>
  dados(api.patch(`/documents/${id}/review`, { observacao_revisao: observacao }))

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
