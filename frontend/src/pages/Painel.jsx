import { Link } from 'react-router-dom'

import { obterPendencias } from '../api/servicos'
import { Carregando, ErroCarregamento, EstadoVazio, Etiqueta, estilos as ui } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useAtualizacaoPeriodica } from '../hooks/useAtualizacaoPeriodica'
import {
  ROTULOS_TIPO_SOLICITACAO,
  formatarData,
  formatarDataHora,
  formatarPrazoRelativo,
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
          <h1>Olá, {usuario.nome.split(' ')[0]}!</h1>
          <p className={estilos.subtitulo}>{subtitulo}</p>
        </div>
        <span className={estilos.atualizacao}>Atualiza automaticamente a cada 30 segundos</span>
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

function Resumo({ numero, rotulo, destino, variante }) {
  const classe = [estilos.resumo, numero > 0 && variante ? estilos[variante] : ''].join(' ')
  return (
    <a href={destino} className={classe}>
      <span className={estilos.resumoNumero}>{numero}</span>
      <span className={estilos.resumoRotulo}>{rotulo}</span>
    </a>
  )
}

function Secao({ id, titulo, children }) {
  return (
    <section id={id} className={ui.cartao}>
      <div className={ui.cartaoCabecalho}>
        <h2>{titulo}</h2>
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

function ItemSolicitacao({ solicitacao, mostrarPaciente }) {
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
        <span>Prazo: {formatarDataHora(solicitacao.prazo)}</span>
        {mostrarPaciente && <span>Paciente: {solicitacao.jornada.paciente.nome}</span>}
      </div>
    </li>
  )
}

function PainelMedico({ painel }) {
  const {
    exames_aguardando_revisao: exames,
    solicitacoes_vencidas: vencidas,
    solicitacoes_proximas_do_prazo: proximas,
    dias_prazo_proximo: diasPrazo,
  } = painel

  return (
    <>
      <div className={estilos.resumos}>
        <Resumo numero={exames.length} rotulo="Exames para revisar" destino="#exames" variante="resumoAlerta" />
        <Resumo numero={vencidas.length} rotulo="Solicitações vencidas" destino="#vencidas" variante="resumoPerigo" />
        <Resumo numero={proximas.length} rotulo={`Vencem em até ${diasPrazo} dias`} destino="#proximas" variante="resumoAlerta" />
      </div>

      <div className={estilos.grade}>
        <Secao id="exames" titulo="Exames aguardando revisão">
          {exames.length === 0 ? (
            <EstadoVazio>Nenhum exame aguardando revisão.</EstadoVazio>
          ) : (
            <ul className={ui.lista}>
              {exames.map((exame) => (
                <li key={exame.id} className={ui.itemLista}>
                  <Link to={linkJornada(exame.jornada.id, 'exames')} className={estilos.linkItem}>
                    {exame.titulo}
                  </Link>
                  <div className={estilos.meta}>
                    <span>Paciente: {exame.jornada.paciente.nome}</span>
                    <span>Enviado em {formatarData(exame.criado_em)}</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Secao>

        <Secao id="vencidas" titulo="Solicitações vencidas">
          {vencidas.length === 0 ? (
            <EstadoVazio>Nenhuma solicitação vencida.</EstadoVazio>
          ) : (
            <ul className={ui.lista}>
              {vencidas.map((s) => (
                <ItemSolicitacao key={s.id} solicitacao={s} mostrarPaciente />
              ))}
            </ul>
          )}
        </Secao>

        <Secao id="proximas" titulo={`Próximas do prazo (${diasPrazo} dias)`}>
          {proximas.length === 0 ? (
            <EstadoVazio>Nenhuma solicitação vencendo nos próximos dias.</EstadoVazio>
          ) : (
            <ul className={ui.lista}>
              {proximas.map((s) => (
                <ItemSolicitacao key={s.id} solicitacao={s} mostrarPaciente />
              ))}
            </ul>
          )}
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
        <Resumo numero={pendentes.length} rotulo="Pendências" destino="#pendencias" variante="resumoAlerta" />
        <Resumo numero={vencidas} rotulo="Vencidas" destino="#pendencias" variante="resumoPerigo" />
        <Resumo numero={consultasExtras.length} rotulo="Consultas extras marcadas" destino="#consultas-extras" />
      </div>

      <div className={estilos.grade}>
        <Secao id="pendencias" titulo="O que você precisa fazer">
          {pendentes.length === 0 ? (
            <EstadoVazio>Nenhuma pendência no momento. 🎉</EstadoVazio>
          ) : (
            <ul className={ui.lista}>
              {pendentes.map((s) => (
                <ItemSolicitacao key={s.id} solicitacao={s} />
              ))}
            </ul>
          )}
        </Secao>

        <Secao id="consultas-extras" titulo="Consultas extras marcadas pelo médico">
          {consultasExtras.length === 0 ? (
            <EstadoVazio>Nenhuma consulta extra marcada.</EstadoVazio>
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
  return (
    <Secao id="pendencias" titulo="Solicitações destinadas a você">
      {pendentes.length === 0 ? (
        <EstadoVazio>
          Nenhuma solicitação no momento. Quando o médico atribuir você ao tratamento de um paciente, as solicitações
          aparecem aqui.
        </EstadoVazio>
      ) : (
        <ul className={ui.lista}>
          {pendentes.map((s) => (
            <ItemSolicitacao key={s.id} solicitacao={s} mostrarPaciente />
          ))}
        </ul>
      )}
    </Secao>
  )
}
