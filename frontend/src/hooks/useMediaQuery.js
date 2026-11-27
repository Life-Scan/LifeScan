import { useCallback, useSyncExternalStore } from 'react'

/**
 * true enquanto a media query casa (ex.: '(max-width: 720px)'), acompanhando a mudança de tamanho da
 * janela. Para trocar de componente por tamanho de tela; para só mudar o estilo, use as variantes do
 * Tailwind (ate-720:...).
 */
export function useMediaQuery(consulta) {
  const assinar = useCallback(
    (avisar) => {
      const lista = window.matchMedia(consulta)
      lista.addEventListener('change', avisar)
      return () => lista.removeEventListener('change', avisar)
    },
    [consulta],
  )
  return useSyncExternalStore(assinar, () => window.matchMedia(consulta).matches)
}
