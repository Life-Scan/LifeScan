import { X } from 'lucide-react'
import { useEffect, useId, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

import { cn } from '@/lib/utils'
import { estilos } from './ui'

const LARGURAS = {
  media: 'w-[min(560px,calc(100vw-2rem))]',
  grande: 'w-[min(820px,calc(100vw-2rem))]',
}

const CAMPOS = 'input:not([type=hidden]):not(:disabled), select:not(:disabled), textarea:not(:disabled)'

/**
 * Janela para formulários (criar e editar), no lugar de campos que surgiam no meio da página.
 * Mesmo <dialog> animado da confirmação (.dialogo-animado: fade + escala 0.96 → 1, ~200ms).
 *
 * - showModal(): bloqueia o resto da página e prende o foco. Ao abrir, o foco vai para o primeiro campo;
 *   ao fechar, volta para o botão que abriu.
 * - Fecha pelo X, pelo Esc ou pelo "Cancelar" do formulário (aoFechar). Clicar no fundo escuro NÃO
 *   fecha: um clique distraído não deve jogar fora o que foi digitado.
 * - O conteúdo continua montado depois de fechar, para a saída animar com ele; cada nova abertura
 *   remonta o conteúdo, então o formulário sempre começa limpo.
 * - Portal para o <body>: não herda estilos do item da lista e funciona dentro de outra janela
 *   (Remarcar dentro da Agenda do dia).
 *
 * Uso: <Modal aberto={aberto} aoFechar={() => setAberto(false)} titulo="Nova consulta">…</Modal>
 */
export default function Modal({ aberto, aoFechar, titulo, descricao, largura = 'media', children }) {
  const dialogo = useRef(null)
  const quemAbriu = useRef(null)
  const idTitulo = useId()
  const idDescricao = useId()

  // Conta as aberturas (ajuste de estado durante o render, sem efeito): a chave remonta o conteúdo
  const [abertoAntes, setAbertoAntes] = useState(aberto)
  const [abertura, setAbertura] = useState(aberto ? 1 : 0)
  if (aberto !== abertoAntes) {
    setAbertoAntes(aberto)
    if (aberto) setAbertura((n) => n + 1)
  }

  useEffect(() => {
    const elemento = dialogo.current
    if (!elemento) return
    if (aberto && !elemento.open) {
      quemAbriu.current = document.activeElement
      elemento.showModal()
      elemento.querySelector(`[data-corpo-modal] :is(${CAMPOS})`)?.focus()
    } else if (!aberto && elemento.open) {
      elemento.close()
      const foco = document.activeElement
      if (quemAbriu.current?.isConnected && (foco === document.body || elemento.contains(foco))) quemAbriu.current.focus()
    }
  }, [aberto, abertura])

  return createPortal(
    <dialog
      ref={dialogo}
      className={cn(estilos.dialogo, estilos.modal, LARGURAS[largura])}
      aria-labelledby={idTitulo}
      aria-describedby={descricao ? idDescricao : undefined}
      onCancel={(evento) => {
        // Esc: o React fecha (e a saída anima). stopPropagation: num modal dentro de outro, o Esc
        // não deve chegar ao onCancel da janela de baixo pela árvore do React.
        evento.preventDefault()
        evento.stopPropagation()
        if (aberto) aoFechar()
      }}
      // Pelo portal, o envio do formulário ainda subiria pela árvore do React até um form de fora
      onSubmit={(evento) => evento.stopPropagation()}
    >
      <header className={estilos.modalCabecalho}>
        <div className="min-w-0">
          <h2 id={idTitulo} className={estilos.modalTitulo}>{titulo}</h2>
          {descricao && <p id={idDescricao} className={estilos.dialogoMensagem}>{descricao}</p>}
        </div>
        <button type="button" className={estilos.modalFechar} onClick={aoFechar} aria-label="Fechar janela">
          <X size={18} aria-hidden="true" />
        </button>
      </header>
      <div data-corpo-modal className={estilos.modalCorpo}>
        {abertura > 0 && <div key={abertura}>{children}</div>}
      </div>
    </dialog>,
    document.body,
  )
}
