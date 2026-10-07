import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'

import estilos from './ui.module.css'

const ContextoConfirmacao = createContext(null)

/**
 * Janela de confirmação própria, no lugar do window.confirm do navegador.
 *
 * Uso:
 *   const confirmar = useConfirmar()
 *   if (!(await confirmar({ titulo, mensagem, rotuloConfirmar, perigo }))) return
 */
export function ProvedorConfirmacao({ children }) {
  const [pedido, setPedido] = useState(null)
  const dialogo = useRef(null)

  const confirmar = useCallback(
    (opcoes) => new Promise((resolver) => setPedido({ ...opcoes, resolver })),
    [],
  )

  // showModal() cuida do foco, da tecla Esc e de bloquear o resto da página
  useEffect(() => {
    if (pedido && !dialogo.current?.open) dialogo.current?.showModal()
  }, [pedido])

  function responder(resposta) {
    pedido.resolver(resposta)
    dialogo.current?.close()
    setPedido(null)
  }

  return (
    <ContextoConfirmacao.Provider value={confirmar}>
      {children}
      {pedido && (
        <dialog
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
