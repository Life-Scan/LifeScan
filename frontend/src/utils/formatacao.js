const formatoData = new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
const formatoDataHora = new Intl.DateTimeFormat('pt-BR', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})
const formatoHora = new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit' })

export const formatarData = (iso) => (iso ? formatoData.format(new Date(iso)) : '')
export const formatarDataHora = (iso) => (iso ? formatoDataHora.format(new Date(iso)) : '')
export const formatarHora = (iso) => (iso ? formatoHora.format(new Date(iso)) : '')

/** "hoje", "amanhã", "em 3 dias", "há 2 dias" etc., contando dias do calendário local. */
export function formatarPrazoRelativo(iso) {
  const inicioDoDia = (data) => new Date(data.getFullYear(), data.getMonth(), data.getDate())
  const dias = Math.round((inicioDoDia(new Date(iso)) - inicioDoDia(new Date())) / 86_400_000)
  if (dias === 0) return 'hoje'
  if (dias === 1) return 'amanhã'
  if (dias === -1) return 'ontem'
  return dias > 0 ? `em ${dias} dias` : `há ${-dias} dias`
}

export function formatarTamanho(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1).replace('.', ',')} MB`
}

/** Valor para <input type="datetime-local"> a partir de uma Date, no horário local. */
export function paraCampoDataHora(data) {
  const deslocamento = data.getTimezoneOffset() * 60_000
  return new Date(data.getTime() - deslocamento).toISOString().slice(0, 16)
}

/** Converte o valor de <input type="datetime-local"> (horário local) para ISO em UTC. */
export const campoDataHoraParaIso = (valor) => new Date(valor).toISOString()

export const ROTULOS_PASSO = { consulta: 'Consulta', exame: 'Exame', retorno: 'Retorno' }
export const PASSOS = ['consulta', 'exame', 'retorno']

export const ROTULOS_TIPO_CONSULTA = { consulta: 'Consulta', retorno: 'Retorno' }

export const ROTULOS_TIPO_SOLICITACAO = {
  exame: 'Exame',
  consulta_extra: 'Consulta extra',
  orientacao_profissional: 'Orientação de outro profissional',
  outro: 'Outro',
}

export const ROTULOS_STATUS_SOLICITACAO = {
  pendente: 'Pendente',
  atendida: 'Atendida',
  cancelada: 'Cancelada',
}

export const ROTULOS_STATUS_EXAME = { enviado: 'Aguardando revisão', revisado: 'Revisado' }

export const ROTULOS_TIPO_EVENTO = {
  consulta: 'Consulta',
  solicitacao: 'Solicitação',
  exame: 'Exame',
}
