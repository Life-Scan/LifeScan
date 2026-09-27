import { useEffect, useRef, useState } from 'react'

import { mensagemDeErro } from '../../api/cliente'
import { enviarMensagem } from '../../api/servicos'
import { Alerta, Anexo, CampoArquivo, EstadoVazio, estilos as ui } from '../../components/ui'
import { formatarData, formatarHora } from '../../utils/formatacao'
import estilos from './Jornada.module.css'

export default function AbaMensagens({ mensagens, jornada, usuario, editavel, atualizar }) {
  const [texto, setTexto] = useState('')
  const [arquivo, setArquivo] = useState(null)
  const [mostrarAnexo, setMostrarAnexo] = useState(false)
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)
  const fim = useRef(null)

  // Rola até a última mensagem quando chega uma nova
  const ultimaId = mensagens.at(-1)?.id
  useEffect(() => {
    fim.current?.scrollIntoView({ block: 'nearest' })
  }, [ultimaId])

  async function aoEnviar(evento) {
    evento?.preventDefault()
    if (!texto.trim() && !arquivo) return
    setErro('')
    setEnviando(true)
    try {
      await enviarMensagem(jornada.id, { conteudo: texto.trim(), arquivo })
      setTexto('')
      setArquivo(null)
      setMostrarAnexo(false)
      await atualizar()
    } catch (erroEnvio) {
      setErro(mensagemDeErro(erroEnvio))
    } finally {
      setEnviando(false)
    }
  }

  // Enter envia; Shift+Enter quebra a linha
  function aoTeclar(evento) {
    if (evento.key === 'Enter' && !evento.shiftKey) {
      evento.preventDefault()
      aoEnviar()
    }
  }

  let diaAnterior = null

  return (
    <div className={estilos.chat}>
      <h2>Mensagens</h2>
      <div className={estilos.conversa} aria-live="polite">
        {mensagens.length === 0 && <EstadoVazio>Nenhuma mensagem ainda. Comece a conversa!</EstadoVazio>}
        {mensagens.map((mensagem) => {
          const minha = mensagem.remetente.id === usuario.id
          const dia = formatarData(mensagem.criado_em)
          const separador = dia !== diaAnterior
          diaAnterior = dia
          return (
            <div key={mensagem.id}>
              {separador && <div className={estilos.separadorDia}>{dia}</div>}
              <div className={minha ? estilos.balaoMeu : estilos.balao}>
                {!minha && <span className={estilos.remetente}>{mensagem.remetente.nome}</span>}
                {mensagem.conteudo && <p className={estilos.texto}>{mensagem.conteudo}</p>}
                {mensagem.arquivo && <Anexo arquivo={mensagem.arquivo} />}
                <time className={estilos.horaMensagem} dateTime={mensagem.criado_em}>
                  {formatarHora(mensagem.criado_em)}
                </time>
              </div>
            </div>
          )
        })}
        <div ref={fim} />
      </div>

      {editavel ? (
        <form className={estilos.envioMensagem} onSubmit={aoEnviar}>
          <Alerta tipo="erro">{erro}</Alerta>
          {mostrarAnexo && (
            <CampoArquivo id="mensagem-anexo" rotulo="Anexo" arquivo={arquivo} onChange={setArquivo} />
          )}
          <div className={estilos.linhaEnvio}>
            <label htmlFor="mensagem-texto" className="visualmente-oculto">
              Mensagem
            </label>
            <textarea
              id="mensagem-texto"
              rows={2}
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              onKeyDown={aoTeclar}
              placeholder="Escreva uma mensagem… (Enter envia, Shift+Enter quebra linha)"
            />
            <div className={estilos.botoesEnvio}>
              <button
                type="button"
                className={`${ui.botaoSecundario} ${ui.botaoPequeno}`}
                onClick={() => {
                  if (mostrarAnexo) setArquivo(null)
                  setMostrarAnexo((v) => !v)
                }}
                aria-pressed={mostrarAnexo}
              >
                📎 {mostrarAnexo ? 'Sem anexo' : 'Anexar'}
              </button>
              <button type="submit" className={ui.botao} disabled={enviando || (!texto.trim() && !arquivo)}>
                {enviando ? 'Enviando…' : 'Enviar'}
              </button>
            </div>
          </div>
        </form>
      ) : (
        <p className={ui.ajuda}>A jornada está encerrada; não é possível enviar mensagens.</p>
      )}
    </div>
  )
}
