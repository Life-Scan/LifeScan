/**
 * Máscaras e conversões automáticas para e-mail, telefone e datas (DD/MM/AAAA e DD/MM/AAAA HH:MM).
 */

/** Remove espaços, converte para minúsculas e mantém apenas caracteres válidos de e-mail. */
export function mascaraEmail(valor) {
  const limpo = String(valor ?? '')
    .replace(/\s+/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9@._+-]/g, '')

  const primeiroArroba = limpo.indexOf('@')
  if (primeiroArroba === -1) return limpo
  return limpo.slice(0, primeiroArroba + 1) + limpo.slice(primeiroArroba + 1).replace(/@/g, '')
}

/** Formata telefone brasileiro com 10 ou 11 dígitos: (XX) XXXX-XXXX ou (XX) XXXXX-XXXX. */
export function mascaraTelefone(valor) {
  const digitos = String(valor ?? '').replace(/\D/g, '').slice(0, 11)
  if (digitos.length === 0) return ''
  if (digitos.length <= 2) return `(${digitos}`
  if (digitos.length <= 6) return `(${digitos.slice(0, 2)}) ${digitos.slice(2)}`
  if (digitos.length <= 10) return `(${digitos.slice(0, 2)}) ${digitos.slice(2, 6)}-${digitos.slice(6)}`
  return `(${digitos.slice(0, 2)}) ${digitos.slice(2, 7)}-${digitos.slice(7)}`
}

/** Formata data no padrão brasileiro DD/MM/AAAA conforme o usuário digita. */
export function mascaraData(valor) {
  const digitos = String(valor ?? '').replace(/\D/g, '').slice(0, 8)
  if (digitos.length <= 2) return digitos
  if (digitos.length <= 4) return `${digitos.slice(0, 2)}/${digitos.slice(2)}`
  return `${digitos.slice(0, 2)}/${digitos.slice(2, 4)}/${digitos.slice(4)}`
}

/** Formata data e hora no padrão brasileiro DD/MM/AAAA HH:MM conforme o usuário digita. */
export function mascaraDataHora(valor) {
  const digitos = String(valor ?? '').replace(/\D/g, '').slice(0, 12)
  if (digitos.length <= 8) return mascaraData(digitos)
  const data = mascaraData(digitos.slice(0, 8))
  const hora = digitos.slice(8)
  if (hora.length <= 2) return `${data} ${hora}`
  return `${data} ${hora.slice(0, 2)}:${hora.slice(2)}`
}

/** Converte "YYYY-MM-DD" para "DD/MM/AAAA". */
export function dataIsoParaBr(iso) {
  if (!iso) return ''
  const [ano, mes, dia] = String(iso).slice(0, 10).split('-')
  if (!ano || !mes || !dia) return ''
  return `${dia}/${mes}/${ano}`
}

/** Valida "DD/MM/AAAA" (calendário real) e devolve "YYYY-MM-DD" ou null. */
export function dataBrParaIso(texto) {
  const match = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(String(texto ?? '').trim())
  if (!match) return null
  const dia = Number(match[1])
  const mes = Number(match[2])
  const ano = Number(match[3])
  if (ano < 1900 || mes < 1 || mes > 12 || dia < 1 || dia > 31) return null

  const conferencia = new Date(Date.UTC(ano, mes - 1, dia))
  if (
    conferencia.getUTCFullYear() !== ano ||
    conferencia.getUTCMonth() !== mes - 1 ||
    conferencia.getUTCDate() !== dia
  ) {
    return null
  }
  return `${String(ano).padStart(4, '0')}-${String(mes).padStart(2, '0')}-${String(dia).padStart(2, '0')}`
}

/** Converte "YYYY-MM-DDTHH:MM" para "DD/MM/AAAA HH:MM". */
export function dataHoraIsoParaBr(isoLocal) {
  if (!isoLocal) return ''
  const [dataIso, hora] = String(isoLocal).slice(0, 16).split('T')
  const dataBr = dataIsoParaBr(dataIso)
  if (!dataBr || !hora) return ''
  return `${dataBr} ${hora}`
}

/** Valida "DD/MM/AAAA HH:MM" e devolve "YYYY-MM-DDTHH:MM" ou null. */
export function dataHoraBrParaIso(texto) {
  const match = /^(\d{2}\/\d{2}\/\d{4})\s+(\d{2}):(\d{2})$/.exec(String(texto ?? '').trim())
  if (!match) return null
  const dataIso = dataBrParaIso(match[1])
  if (!dataIso) return null
  const hora = Number(match[2])
  const minuto = Number(match[3])
  if (hora < 0 || hora > 23 || minuto < 0 || minuto > 59) return null
  return `${dataIso}T${match[2]}:${match[3]}`
}
