import { useCallback, useEffect, useRef, useState } from 'react'

export const INTERVALO_PADRAO_MS = 30_000

/**
 * Busca dados e repete a busca periodicamente (polling), RNF04/RNF08.
 *
 * - Pausa quando a aba fica oculta e atualiza assim que ela volta a ficar visível.
 * - `dependencias` reinicia a busca quando mudam (ex.: id da jornada).
 * - Respostas atrasadas de buscas anteriores são descartadas.
 *
 * Devolve { dados, erro, carregando, atualizar }. `atualizar()` força uma busca
 * imediata (útil depois de salvar algo).
 */
export function useAtualizacaoPeriodica(buscar, intervaloMs = INTERVALO_PADRAO_MS, dependencias = []) {
  const [dados, setDados] = useState(null)
  const [erro, setErro] = useState(null)
  const [carregando, setCarregando] = useState(true)

  const buscarRef = useRef(buscar)
  buscarRef.current = buscar
  const numeroDaBusca = useRef(0)

  const atualizar = useCallback(async () => {
    const numero = ++numeroDaBusca.current
    try {
      const resultado = await buscarRef.current()
      if (numero !== numeroDaBusca.current) return
      setDados(resultado)
      setErro(null)
    } catch (erroBusca) {
      if (numero !== numeroDaBusca.current) return
      setErro(erroBusca)
    } finally {
      if (numero === numeroDaBusca.current) setCarregando(false)
    }
  }, [])

  useEffect(() => {
    setCarregando(true)
    setDados(null)
    setErro(null)
    atualizar()

    let temporizador = null
    const iniciar = () => {
      if (temporizador === null) temporizador = setInterval(atualizar, intervaloMs)
    }
    const parar = () => {
      clearInterval(temporizador)
      temporizador = null
    }
    const aoMudarVisibilidade = () => {
      if (document.visibilityState === 'visible') {
        atualizar()
        iniciar()
      } else {
        parar()
      }
    }

    if (document.visibilityState === 'visible') iniciar()
    document.addEventListener('visibilitychange', aoMudarVisibilidade)
    return () => {
      parar()
      document.removeEventListener('visibilitychange', aoMudarVisibilidade)
      // Invalida respostas que chegarem depois da troca de dependências
      numeroDaBusca.current++
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [atualizar, intervaloMs, ...dependencias])

  return { dados, erro, carregando, atualizar }
}
