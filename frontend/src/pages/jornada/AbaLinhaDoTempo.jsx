import { useMemo, useState } from 'react'

import { Anexo, EstadoVazio, estilos as ui } from '../../components/ui'
import { ROTULOS_TIPO_EVENTO, formatarDataHora } from '../../utils/formatacao'
import estilos from './Jornada.module.css'

const ICONES = { consulta: '🩺', solicitacao: '📋', exame: '🧪', mensagem: '💬' }
const TIPOS = Object.keys(ROTULOS_TIPO_EVENTO)

/** Anexo do evento, quando houver (exame ou mensagem com arquivo). */
function anexoDoEvento(evento) {
  if (evento.tipo === 'exame') return evento.dados.arquivo
  if (evento.tipo === 'mensagem') return evento.dados.arquivo
  return null
}

export default function AbaLinhaDoTempo({ eventos, irParaAba }) {
  const [filtro, setFiltro] = useState([])
  const [recentesPrimeiro, setRecentesPrimeiro] = useState(false)

  const visiveis = useMemo(() => {
    // O backend já devolve em ordem cronológica; o filtro é aplicado aqui para
    // não precisar de outra requisição a cada clique
    const filtrados = filtro.length ? eventos.filter((e) => filtro.includes(e.tipo)) : eventos
    return recentesPrimeiro ? [...filtrados].reverse() : filtrados
  }, [eventos, filtro, recentesPrimeiro])

  const alternarTipo = (tipo) =>
    setFiltro((atual) => (atual.includes(tipo) ? atual.filter((t) => t !== tipo) : [...atual, tipo]))

  const abaDoTipo = { consulta: 'consultas', solicitacao: 'solicitacoes', exame: 'exames', mensagem: 'mensagens' }

  return (
    <div className={estilos.pilha}>
      <div className={ui.cabecalhoItem}>
        <div className={estilos.filtros} role="group" aria-label="Filtrar por tipo">
          <button
            type="button"
            className={filtro.length === 0 ? estilos.filtroAtivo : estilos.filtro}
            onClick={() => setFiltro([])}
            aria-pressed={filtro.length === 0}
          >
            Tudo
          </button>
          {TIPOS.map((tipo) => (
            <button
              key={tipo}
              type="button"
              className={filtro.includes(tipo) ? estilos.filtroAtivo : estilos.filtro}
              onClick={() => alternarTipo(tipo)}
              aria-pressed={filtro.includes(tipo)}
            >
              {ICONES[tipo]} {ROTULOS_TIPO_EVENTO[tipo]}
            </button>
          ))}
        </div>
        <button type="button" className={ui.botaoLink} onClick={() => setRecentesPrimeiro((v) => !v)}>
          {recentesPrimeiro ? 'Mais antigos primeiro' : 'Mais recentes primeiro'}
        </button>
      </div>

      {visiveis.length === 0 ? (
        <EstadoVazio>
          {eventos.length === 0 ? 'Nada registrado nesta jornada ainda.' : 'Nenhum evento deste tipo.'}
        </EstadoVazio>
      ) : (
        <ol className={estilos.linhaDoTempo}>
          {visiveis.map((evento) => {
            const anexo = anexoDoEvento(evento)
            return (
              <li key={`${evento.tipo}-${evento.id}`} className={estilos.evento}>
                <span className={estilos.iconeEvento} aria-hidden="true">
                  {ICONES[evento.tipo]}
                </span>
                <div className={estilos.corpoEvento}>
                  <div className={estilos.metaEvento}>
                    <button type="button" className={ui.botaoLink} onClick={() => irParaAba(abaDoTipo[evento.tipo])}>
                      {ROTULOS_TIPO_EVENTO[evento.tipo]}
                    </button>
                    <time dateTime={evento.data}>{formatarDataHora(evento.data)}</time>
                  </div>
                  <p className={estilos.resumoEvento}>{evento.resumo}</p>
                  {anexo && <Anexo arquivo={anexo} />}
                </div>
              </li>
            )
          })}
        </ol>
      )}
    </div>
  )
}
