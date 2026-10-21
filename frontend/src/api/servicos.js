/** Funções de acesso à API, uma por rota do backend. Todas devolvem os dados da resposta. */
import { api } from './cliente'

const dados = (promessa) => promessa.then((resposta) => resposta.data)

// Listas visíveis usam paginação no servidor; os seletores existentes mantêm sua API.
export const obterPagina = (caminho, parametros = {}) =>
  dados(api.get(caminho, { params: { pagina: 1, tamanho: 20, ...parametros } }))

// Autenticação
export const entrar = (email, senha) => dados(api.post('/auth/login', { email, senha }))
export const obterUsuarioAtual = () => dados(api.get('/auth/me'))
export const definirSenha = (novaSenha, aceiteLgpd) => dados(api.post('/auth/set-password', { nova_senha: novaSenha, aceite_lgpd: aceiteLgpd }))
export const esqueciSenha = (email) => dados(api.post('/auth/forgot-password', { email }))

// Contas de pacientes e parceiros (médico)
export const listarContas = (tipo) => dados(api.get('/users', { params: tipo ? { tipo } : {} }))
export const criarConta = (conta) => dados(api.post('/users', conta))
export const atualizarConta = (id, alteracoes) => dados(api.patch(`/users/${id}`, alteracoes))
export const excluirPaciente = (id) => dados(api.delete(`/users/${id}`))
export const reenviarAcesso = (id) => dados(api.post(`/users/${id}/resend-access`))

// Acompanhamentos
export const listarAcompanhamentos = () => dados(api.get('/follow-ups'))
export const obterAcompanhamento = (id) => dados(api.get(`/follow-ups/${id}`))
export const obterResumoAcompanhamento = (id) => dados(api.get(`/follow-ups/${id}/summary`))
export const criarAcompanhamento = (acompanhamento) => dados(api.post('/follow-ups', acompanhamento))
export const alterarPasso = (id, passo) => dados(api.patch(`/follow-ups/${id}/step`, { passo_atual: passo }))
export const alterarStatusAcompanhamento = (id, status) => dados(api.patch(`/follow-ups/${id}/status`, { status }))

// Ficha do paciente e parceiros da acompanhamento
export const obterAnamnese = (acompanhamentoId) => dados(api.get(`/follow-ups/${acompanhamentoId}/anamnesis`))
export const salvarAnamnese = (acompanhamentoId, anamnese) => dados(api.put(`/follow-ups/${acompanhamentoId}/anamnesis`, anamnese))
export const acessosAnamnese = (acompanhamentoId) => dados(api.get(`/follow-ups/${acompanhamentoId}/anamnesis/acessos`))
export const exportarAnamnese = (acompanhamentoId) =>
  api.get(`/follow-ups/${acompanhamentoId}/anamnesis/portabilidade`, { responseType: 'blob' }).then((r) => r.data)
export const listarParceirosDoAcompanhamento = (acompanhamentoId) => dados(api.get(`/follow-ups/${acompanhamentoId}/partners`))
export const atribuirParceiro = (acompanhamentoId, parceiroId) =>
  dados(api.post(`/follow-ups/${acompanhamentoId}/partners`, { parceiro_id: parceiroId }))
export const removerParceiro = (acompanhamentoId, parceiroId) =>
  dados(api.delete(`/follow-ups/${acompanhamentoId}/partners/${parceiroId}`))

// Consultas
export const listarConsultas = (acompanhamentoId) => dados(api.get(`/follow-ups/${acompanhamentoId}/consultations`))
export const registrarConsulta = (acompanhamentoId, consulta) =>
  dados(api.post(`/follow-ups/${acompanhamentoId}/consultations`, consulta))

// Solicitações
export const listarSolicitacoes = (acompanhamentoId, parametros) => dados(api.get(`/follow-ups/${acompanhamentoId}/requests`, { params: parametros }))
export const criarSolicitacao = (acompanhamentoId, solicitacao) =>
  dados(api.post(`/follow-ups/${acompanhamentoId}/requests`, solicitacao))
export const concluirSolicitacao = (id) => dados(api.patch(`/requests/${id}/complete`))
export const cancelarSolicitacao = (id) => dados(api.patch(`/requests/${id}/cancel`))

// Documentos (exames, laudos, planos alimentares, planos de treino, orientações...)
export const listarDocumentos = (acompanhamentoId) => dados(api.get(`/follow-ups/${acompanhamentoId}/documents`))
export function enviarDocumento(acompanhamentoId, { titulo, categoria, arquivo, solicitacaoId }) {
  const formulario = new FormData()
  formulario.append('titulo', titulo)
  formulario.append('categoria', categoria)
  formulario.append('arquivo', arquivo)
  if (solicitacaoId) formulario.append('solicitacao_id', solicitacaoId)
  return dados(api.post(`/follow-ups/${acompanhamentoId}/documents`, formulario))
}
export const revisarDocumento = (id, observacao) =>
  dados(api.patch(`/documents/${id}/review`, { observacao_revisao: observacao }))

// Linha do tempo e painel
export const obterLinhaDoTempo = (acompanhamentoId, tipos) =>
  dados(api.get(`/follow-ups/${acompanhamentoId}/timeline`, { params: tipos?.length ? { tipos: tipos.join(',') } : {} }))
export const obterPendencias = () => dados(api.get('/dashboard/pending'))

// Arquivos: o download exige o token, então buscamos o conteúdo como blob
export async function obterArquivo(arquivoId, inline = false) {
  const resposta = await api.get(`/files/${arquivoId}/download`, {
    params: inline ? { inline: true } : {},
    responseType: 'blob',
  })
  return resposta.data
}
