import { CalendarClock, CircleCheck, ClipboardList, Clock, FileText, TriangleAlert } from 'lucide-react'
import { Link } from 'react-router-dom'

import { obterPendencias } from '../api/servicos'
import { Carregando, ErroCarregamento, EstadoVazio, Etiqueta, estilos as ui } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useAtualizacaoPeriodica } from '../hooks/useAtualizacaoPeriodica'
import {
  ROTULOS_CATEGORIA,
  ROTULOS_TIPO_SOLICITACAO,
  formatarData,
  formatarDataHora,
  formatarPrazoRelativo,
  primeiroNome,
} from '../utils/formatacao'
import estilos from './Paginas.module.css'

export default function Painel() {
  const { usuario, ehMedico, ehPaciente } = useAuth()
  const { dados, erro, carregando } = useAtualizacaoPeriodica(obterPendencias)
  const subtitulo = ehMedico
    ? 'Veja o que precisa da sua atenção.'
    : ehPaciente
      ? 'Veja o que você precisa fazer e até quando.'
      : 'Acompanhe as solicitações destinadas a você.'

  return (
    <div className={estilos.pilha}>
      <div className={estilos.cabecalho}>
        <div>
          <h1>Olá, {primeiroNome(usuario.nome)}!</h1>
          <p className={estilos.subtitulo}>{subtitulo}</p>
        </div>
        <span className={estilos.atualizacao}>Atualiza sozinho a cada 30 segundos</span>
      </div>

      <ErroCarregamento erro={erro} />
      {carregando && !dados && <Carregando />}
      {dados?.tipo_usuario === 'medico' && <PainelMedico painel={dados} />}
      {dados?.tipo_usuario === 'paciente' && <PainelPaciente painel={dados} />}
      {dados?.tipo_usuario === 'parceiro' && <PainelParceiro painel={dados} />}
    </div>
  )
}

function linkJornada(jornadaId, aba) {
  return `/jornadas/${jornadaId}?aba=${aba}`
}

/** Cartão de resumo: número grande com ícone. tom: perigo | alerta | info (aplicado só se houver itens). */
function Resumo({ icone: Icone, numero, rotulo, destino, tom }) {
  const classes = [estilos.resumo, numero > 0 && tom ? estilos[`resumo_${tom}`] : ''].filter(Boolean).join(' ')
  return (
    <a href={destino} className={classes}>
      <span className={estilos.resumoIcone}>
        <Icone size={20} aria-hidden="true" />
      </span>
      <span>
        <span className={estilos.resumoNumero}>{numero}</span>
        <span className={estilos.resumoRotulo}>{rotulo}</span>
      </span>
    </a>
  )
}

function Secao({ id, titulo, quantidade, children }) {
  return (
    <section id={id} className={ui.cartao}>
      <div className={ui.cartaoCabecalho}>
        <h2>
          {titulo}
          {quantidade > 0 && <span className={estilos.contagem}>{quantidade}</span>}
        </h2>
      </div>
      {children}
    </section>
  )
}

function PrazoSolicitacao({ solicitacao }) {
  return solicitacao.vencida ? (
    <Etiqueta variante="perigo">Venceu {formatarPrazoRelativo(solicitacao.prazo)}</Etiqueta>
  ) : (
    <Etiqueta variante="alerta">Vence {formatarPrazoRelativo(solicitacao.prazo)}</Etiqueta>
  )
}

function ItemSolicitacao({ solicitacao, mostrarPaciente, mostrarDestinatario }) {
  return (
    <li className={solicitacao.vencida ? ui.itemListaDestaque : ui.itemLista}>
      <div className={ui.cabecalhoItem}>
        <Link to={linkJornada(solicitacao.jornada.id, 'solicitacoes')} className={estilos.linkItem}>
          {ROTULOS_TIPO_SOLICITACAO[solicitacao.tipo]}
        </Link>
        <PrazoSolicitacao solicitacao={solicitacao} />
      </div>
      <p className={estilos.textoItem}>{solicitacao.descricao}</p>
      <div className={estilos.meta}>
        {mostrarPaciente && <span>{solicitacao.jornada.paciente.nome}</span>}
        <span>Prazo: {formatarDataHora(solicitacao.prazo)}</span>
        {mostrarDestinatario && solicitacao.destinatario.tipo_usuario === 'parceiro' && (
          <span>
            A cargo de {solicitacao.destinatario.nome} ({solicitacao.destinatario.profissao})
          </span>
        )}
      </div>
    </li>
  )
}

function ListaSolicitacoes({ solicitacoes, vazio, ...opcoes }) {
  if (solicitacoes.length === 0) return <EstadoVazio icone={CircleCheck}>{vazio}</EstadoVazio>
  return (
    <ul className={ui.lista}>
      {solicitacoes.map((s) => (
        <ItemSolicitacao key={s.id} solicitacao={s} {...opcoes} />
      ))}
    </ul>
  )
}

function PainelMedico({ painel }) {
  const {
    documentos_aguardando_revisao: documentos,
    solicitacoes_vencidas: vencidas,
    solicitacoes_proximas_do_prazo: proximas,
    dias_prazo_proximo: diasPrazo,
  } = painel

  return (
    <>
      <div className={estilos.resumos}>
        <Resumo icone={FileText} numero={documentos.length} rotulo="Documentos para revisar" destino="#documentos" tom="info" />
        <Resumo icone={TriangleAlert} numero={vencidas.length} rotulo="Solicitações vencidas" destino="#vencidas" tom="perigo" />
        <Resumo icone={Clock} numero={proximas.length} rotulo={`Vencem em até ${diasPrazo} dias`} destino="#proximas" tom="alerta" />
      </div>

      <div className={estilos.grade}>
        <Secao id="documentos" titulo="Documentos aguardando revisão" quantidade={documentos.length}>
          {documentos.length === 0 ? (
            <EstadoVazio icone={CircleCheck}>Nenhum documento aguardando revisão.</EstadoVazio>
          ) : (
            <ul className={ui.lista}>
              {documentos.map((documento) => (
                <li key={documento.id} className={ui.itemLista}>
                  <div className={ui.cabecalhoItem}>
                    <Link to={linkJornada(documento.jornada.id, 'documentos')} className={estilos.linkItem}>
                      {documento.titulo}
                    </Link>
                    <Etiqueta variante="info">{ROTULOS_CATEGORIA[documento.categoria]}</Etiqueta>
                  </div>
                  <div className={estilos.meta}>
                    <span>{documento.jornada.paciente.nome}</span>
                    {documento.enviado_por.id !== documento.jornada.paciente.id && (
                      <span>Enviado por {documento.enviado_por.nome}</span>
                    )}
                    <span>{formatarData(documento.criado_em)}</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Secao>

        <Secao id="vencidas" titulo="Solicitações vencidas" quantidade={vencidas.length}>
          <ListaSolicitacoes
            solicitacoes={vencidas}
            vazio="Nenhuma solicitação vencida."
            mostrarPaciente
            mostrarDestinatario
          />
        </Secao>

        <Secao id="proximas" titulo={`Vencem em até ${diasPrazo} dias`} quantidade={proximas.length}>
          <ListaSolicitacoes
            solicitacoes={proximas}
            vazio="Nenhuma solicitação vencendo nos próximos dias."
            mostrarPaciente
            mostrarDestinatario
          />
        </Secao>
      </div>
    </>
  )
}

function PainelPaciente({ painel }) {
  const { solicitacoes_pendentes: pendentes, consultas_extras: consultasExtras } = painel
  const vencidas = pendentes.filter((s) => s.vencida).length

  return (
    <>
      <div className={estilos.resumos}>
        <Resumo icone={ClipboardList} numero={pendentes.length} rotulo="Pendências" destino="#pendencias" tom="alerta" />
        <Resumo icone={TriangleAlert} numero={vencidas} rotulo="Vencidas" destino="#pendencias" tom="perigo" />
        <Resumo icone={CalendarClock} numero={consultasExtras.length} rotulo="Consultas extras marcadas" destino="#consultas-extras" tom="info" />
      </div>

      <div className={estilos.grade}>
        <Secao id="pendencias" titulo="O que você precisa fazer" quantidade={pendentes.length}>
          <ListaSolicitacoes solicitacoes={pendentes} vazio="Nenhuma pendência no momento." />
        </Secao>

        <Secao id="consultas-extras" titulo="Consultas extras marcadas pelo médico" quantidade={consultasExtras.length}>
          {consultasExtras.length === 0 ? (
            <EstadoVazio icone={CalendarClock}>Nenhuma consulta extra marcada.</EstadoVazio>
          ) : (
            <ul className={ui.lista}>
              {consultasExtras.map((s) => (
                <li key={s.id} className={ui.itemLista}>
                  <div className={ui.cabecalhoItem}>
                    <strong>{formatarDataHora(s.prazo)}</strong>
                    <Etiqueta variante="info">{formatarPrazoRelativo(s.prazo)}</Etiqueta>
                  </div>
                  <p className={estilos.textoItem}>{s.descricao}</p>
                </li>
              ))}
            </ul>
          )}
        </Secao>
      </div>
    </>
  )
}

function PainelParceiro({ painel }) {
  const pendentes = painel.solicitacoes_pendentes
  const vencidas = pendentes.filter((s) => s.vencida).length

  return (
    <>
      <div className={estilos.resumos}>
        <Resumo icone={ClipboardList} numero={pendentes.length} rotulo="Solicitações para você" destino="#pendencias" tom="alerta" />
        <Resumo icone={TriangleAlert} numero={vencidas} rotulo="Vencidas" destino="#pendencias" tom="perigo" />
      </div>

      <Secao id="pendencias" titulo="Solicitações destinadas a você" quantidade={pendentes.length}>
        <ListaSolicitacoes
          solicitacoes={pendentes}
          vazio={
            <>
              Nenhuma solicitação pendente. Em <Link to="/jornadas">Pacientes</Link> você consulta a ficha de quem
              foi atribuído a você e envia documentos.
            </>
          }
          mostrarPaciente
        />
      </Secao>
    </>
  )
}
