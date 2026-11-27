import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'

import { estilos } from './ui'

const ContextoConfirmacao = createContext(null)

/**
 * Janela de confirmação própria, no lugar do window.confirm do navegador.
 *
 * Uso:
 *   const confirmar = useConfirmar()
 *   if (!(await confirmar({ titulo, mensagem, rotuloConfirmar, perigo }))) return
 */
export function ProvedorConfirmacao({ children }) {
  // O pedido continua montado depois de respondido: a janela sai animada (.dialogo-animado) com o
  // mesmo texto. `aberto` diz se ela está na tela; `id` remonta o <dialog> a cada pedido novo.
  const [pedido, setPedido] = useState(null)
  const [aberto, setAberto] = useState(false)
  const proximoId = useRef(0)
  const dialogo = useRef(null)

  const confirmar = useCallback(
    (opcoes) =>
      new Promise((resolver) => {
        proximoId.current += 1
        setPedido({ ...opcoes, resolver, id: proximoId.current })
        setAberto(true)
      }),
    [],
  )

  // showModal() cuida do foco, da tecla Esc e de bloquear o resto da página
  useEffect(() => {
    if (aberto && !dialogo.current?.open) dialogo.current?.showModal()
  }, [aberto, pedido])

  function responder(resposta) {
    if (!aberto) return
    pedido.resolver(resposta)
    dialogo.current?.close()
    setAberto(false)
  }

  return (
    <ContextoConfirmacao.Provider value={confirmar}>
      {children}
      {pedido && (
        <dialog
          key={pedido.id}
          ref={dialogo}
          className={estilos.dialogo}
          aria-labelledby="confirmacao-titulo"
          onCancel={(evento) => {
            evento.preventDefault()
            responder(false)
          }}
          // Clique fora da caixa (no fundo escurecido) cancela
          onClick={(evento) => evento.target === dialogo.current && responder(false)}
        >
          <div className={estilos.dialogoConteudo}>
            <h2 id="confirmacao-titulo">{pedido.titulo}</h2>
            {pedido.mensagem && <p className={estilos.dialogoMensagem}>{pedido.mensagem}</p>}
            <div className={estilos.dialogoAcoes}>
              {/* Em ações destrutivas o foco inicial fica em "Cancelar", para um Enter distraído não confirmar */}
              <button
                type="button"
                className={estilos.botaoSecundario}
                onClick={() => responder(false)}
                autoFocus={Boolean(pedido.perigo)}
              >
                {pedido.rotuloCancelar || 'Cancelar'}
              </button>
              <button
                type="button"
                className={pedido.perigo ? estilos.botaoPerigoSolido : estilos.botao}
                onClick={() => responder(true)}
                autoFocus={!pedido.perigo}
              >
                {pedido.rotuloConfirmar || 'Confirmar'}
              </button>
            </div>
          </div>
        </dialog>
      )}
    </ContextoConfirmacao.Provider>
  )
}

export function useConfirmar() {
  const confirmar = useContext(ContextoConfirmacao)
  if (!confirmar) throw new Error('useConfirmar precisa estar dentro de <ProvedorConfirmacao>.')
  return confirmar
}
