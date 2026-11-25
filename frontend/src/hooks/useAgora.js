import { useEffect, useState } from 'react'

/**
 * Hora atual guardada em estado e atualizada a cada `intervaloMs` (padrão: 1 minuto).
 *
 * Use no lugar de `new Date()` / `Date.now()` dentro do render: ler a hora no render deixa o
 * componente impuro (cada render daria um resultado diferente). Ver CLAUDE.md → "Render puro".
 */
export function useAgora(intervaloMs = 60_000) {
  const [agora, setAgora] = useState(() => new Date())

  useEffect(() => {
    const id = setInterval(() => setAgora(new Date()), intervaloMs)
    return () => clearInterval(id)
  }, [intervaloMs])

  return agora
}
