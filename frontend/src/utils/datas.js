/** "2026-11-27" no fuso local: chave estável para agrupar compromissos por dia. */
export function chaveDiaLocal(data) {
  const ano = data.getFullYear()
  const mes = String(data.getMonth() + 1).padStart(2, '0')
  const dia = String(data.getDate()).padStart(2, '0')
  return `${ano}-${mes}-${dia}`
}

/** Meia-noite (local) do dia da data. */
export function inicioDoDia(data) {
  return new Date(data.getFullYear(), data.getMonth(), data.getDate())
}

/** Mesmo horário, `dias` dias depois (negativo: antes). */
export function somarDias(data, dias) {
  return new Date(data.getFullYear(), data.getMonth(), data.getDate() + dias)
}
