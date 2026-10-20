import { ArrowUpDown, ClipboardList, FileText, History, Stethoscope } from 'lucide-react'
import { useMemo, useState } from 'react'

import { Anexo, EstadoVazio, Etiqueta, estilos as ui } from '../../components/ui'
import { ROTULOS_CATEGORIA, ROTULOS_TIPO_CONSULTA, formatarDataHora } from '../../utils/formatacao'
import { EtiquetaSolicitacao } from './AbaSolicitacoes'
import estilos from './Jornada.module.css'

const TIPOS = [
  { id: 'consulta', rotulo: 'Consultas', icone: Stethoscope, aba: 'consultas' },
  { id: 'solicitacao', rotulo: 'Solicitações', icone: ClipboardList, aba: 'solicitacoes' },
  { id: 'documento', rotulo: 'Documentos', icone: FileText, aba: 'documentos' },
]
const TIPO_POR_ID = Object.fromEntries(TIPOS.map((tipo) => [tipo.id, tipo]))

const TITULOS_SOLICITACAO = {
  exame: 'Exame solicitado',
  consulta_extra: 'Consulta extra marcada',
  orientacao_profissional: 'Orientação profissional solicitada',
  outro: 'Solicitação',
}

/**
 * O que mostrar de cada evento. Montado a partir de `dados` (o registro completo) em vez do
 * `resumo` em texto do backend, para usar etiquetas de status e não repetir o tipo.
 */
function descreverEvento(evento, pacienteId) {
  const { tipo, dados } = evento

  if (tipo === 'consulta') {
    const quantidade = dados.prescricoes.length
    return {
      titulo: ROTULOS_TIPO_CONSULTA[dados.tipo],
      texto: dados.anotacoes,
      detalhes: quantidade > 0 ? [`${quantidade} ${quantidade === 1 ? 'prescrição' : 'prescrições'}`] : [],
    }
  }

  if (tipo === 'solicitacao') {
    return {
      titulo: TITULOS_SOLICITACAO[dados.tipo],
      texto: dados.descricao,
      detalhes: [
        `${dados.tipo === 'consulta_extra' ? 'Marcada para' : 'Prazo'}: ${formatarDataHora(dados.prazo)}`,
        ...(dados.destinatario.id !== pacienteId ? [`A cargo de ${dados.destinatario.nome}`] : []),
      ],
      etiqueta: <EtiquetaSolicitacao solicitacao={dados} />,
    }
  }

  const revisado = dados.status === 'revisado'
  return {
    titulo: dados.titulo,
    detalhes: [`Enviado por ${dados.enviado_por.nome}`, ROTULOS_CATEGORIA[dados.categoria]],
    etiqueta: <Etiqueta variante={revisado ? 'sucesso' : 'alerta'}>{revisado ? 'Revisado' : 'Aguardando revisão'}</Etiqueta>,
    anexo: dados.arquivo,
  }
}

export default function AbaLinhaDoTempo({ eventos, jornada, irParaAba }) {
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
          {TIPOS.map(({ id, rotulo, icone: Icone }) => (
            <button
              key={id}
              type="button"
              className={filtro.includes(id) ? estilos.filtroAtivo : estilos.filtro}
              onClick={() => alternarTipo(id)}
              aria-pressed={filtro.includes(id)}
            >
              <Icone size={14} aria-hidden="true" />
              {rotulo}
            </button>
          ))}
        </div>
        <button type="button" className={ui.botaoLink} onClick={() => setRecentesPrimeiro((v) => !v)}>
          <ArrowUpDown size={14} aria-hidden="true" />
          {recentesPrimeiro ? 'Mais antigos primeiro' : 'Mais recentes primeiro'}
        </button>
      </div>

      {visiveis.length === 0 ? (
        <EstadoVazio icone={History}>
          {eventos.length === 0 ? 'Nada registrado nesta jornada ainda.' : 'Nenhum evento deste tipo.'}
        </EstadoVazio>
      ) : (
        <ol className={estilos.linhaDoTempo}>
          {visiveis.map((evento) => {
            const { icone: Icone, aba, rotulo } = TIPO_POR_ID[evento.tipo]
            const { titulo, texto, detalhes, etiqueta, anexo } = descreverEvento(evento, jornada.paciente.id)
            return (
              <li key={`${evento.tipo}-${evento.id}`} className={estilos.evento}>
                <span className={`${estilos.iconeEvento} ${estilos[`icone_${evento.tipo}`]}`} aria-hidden="true">
                  <Icone size={16} />
                </span>
                <div className={estilos.corpoEvento}>
                  <div className={estilos.topoEvento}>
                    <button
                      type="button"
                      className={estilos.tituloEvento}
                      onClick={() => irParaAba(aba)}
                      title={`Abrir em ${rotulo}`}
                    >
                      {titulo}
                    </button>
                    {etiqueta}
                    <time className={estilos.dataEvento} dateTime={evento.data}>
                      {formatarDataHora(evento.data)}
                    </time>
                  </div>
                  {texto && <p className={estilos.textoEvento}>{texto}</p>}
                  {detalhes.length > 0 && (
                    <div className={estilos.meta}>
                      {detalhes.map((detalhe) => (
                        <span key={detalhe}>{detalhe}</span>
                      ))}
                    </div>
                  )}
                  {anexo && (
                    <div className={estilos.acoesItem}>
                      <Anexo arquivo={anexo} />
                    </div>
                  )}
                </div>
              </li>
            )
          })}
        </ol>
      )}
    </div>
  )
}
