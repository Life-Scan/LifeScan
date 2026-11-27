import { CalendarClock, CalendarDays, ChevronDown, CircleCheck, ClipboardList, Clock, FileText, TriangleAlert } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { consentimentoLgpd, obterPendencias, revogarConsentimentoLgpd } from '../api/servicos'
import { mensagemDeErro } from '../api/cliente'
import { useConfirmar } from '../components/Confirmacao'
import AgendaConsultas from '../components/AgendaConsultas'
import FormularioConta from '../components/FormularioConta'
import { Alerta, Carregando, ErroCarregamento, Etiqueta, Faixa, estilos as ui } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { cn } from '@/lib/utils'
import { useAgora } from '../hooks/useAgora'
import { useAtualizacaoPeriodica } from '../hooks/useAtualizacaoPeriodica'
import {
  ROTULOS_CATEGORIA,
  ROTULOS_TIPO_SOLICITACAO,
  formatarData,
  formatarDataHora,
  formatarDataPorExtenso,
  formatarPrazoRelativo,
  primeiroNome,
} from '../utils/formatacao'
import { estilos, tonsResumo } from './estilosPaginas'

export default function Painel() {
  const { usuario, ehMedico, ehPaciente, ehColaborador } = useAuth()
  const { dados, erro, carregando, atualizar } = useAtualizacaoPeriodica(obterPendencias)
  const agora = useAgora()
  const resumo = dados ? resumoDoPainel(dados) : null
  // Gaveta de cada resumo: um aberto por vez. "aberturas" remonta o conteúdo a cada abertura, para os
  // itens entrarem em sequência de novo; ao fechar ele continua montado, para a animação de saída.
  const [selecionado, setSelecionado] = useState(null)
  const [aberto, setAberto] = useState(false)
  const [aberturas, setAberturas] = useState(0)

  const refResumos = useRef(null)

  function alternarResumo(id) {
    if (aberto && selecionado === id) {
      setAberto(false)
    } else {
      setSelecionado(id)
      setAberto(true)
      setAberturas((n) => n + 1)
    }
  }

  // A gaveta flutua sobre o conteúdo: fecha com Esc (o foco volta ao resumo) ou com um clique fora
  useEffect(() => {
    if (!aberto) return undefined
    function aoClicarFora(evento) {
      if (!refResumos.current?.contains(evento.target)) setAberto(false)
    }
    function aoTeclar(evento) {
      if (evento.key !== 'Escape') return
      setAberto(false)
      document.getElementById(`resumo-${selecionado}`)?.focus()
    }
    document.addEventListener('pointerdown', aoClicarFora)
    document.addEventListener('keydown', aoTeclar)
    return () => {
      document.removeEventListener('pointerdown', aoClicarFora)
      document.removeEventListener('keydown', aoTeclar)
    }
  }, [aberto, selecionado])
  const subtitulo = ehMedico
    ? 'Veja o que precisa da sua atenção.'
    : ehPaciente
      ? 'Veja o que você precisa fazer e até quando.'
      : ehColaborador
        ? 'Agende as consultas e registre as que já aconteceram.'
        : 'Acompanhe as solicitações destinadas a você.'

  return (
    <div className={estilos.pilha}>
      {/* Dashboard: o que pede atenção fica no topo; cada resumo abre a sua lista (Progressive Disclosure) */}
      <Faixa aria-labelledby="titulo-painel">
        <div className={estilos.faixaTopo}>
          <div>
            <p className={ui.sobretituloFaixa}>{formatarDataPorExtenso(agora)}</p>
            <h1 id="titulo-painel" className={estilos.tituloFaixa}>
              Olá, {primeiroNome(usuario.nome)}
            </h1>
            <p className={estilos.subtituloFaixa}>{resumo?.frase ?? subtitulo}</p>
          </div>
          <span className={estilos.atualizacaoFaixa}>Atualiza sozinho a cada 30 segundos</span>
        </div>
        {resumo && (
          <div ref={refResumos} className={estilos.resumos} style={{ '--colunas': resumo.itens.length }}>
            {resumo.itens.map((item) => {
              const estaAberto = aberto && selecionado === item.id
              // Cada resumo com a sua gaveta logo abaixo, na mesma largura dele
              return (
                <div key={item.id} className={estilos.areaResumo}>
                  <Resumo {...item} aberto={estaAberto} aoAlternar={() => alternarResumo(item.id)} />
                  <GavetaResumo item={item} aberto={estaAberto} chave={`${item.id}-${aberturas}`} />
                </div>
              )
            })}
          </div>
        )}
      </Faixa>

      {ehMedico && <FormularioConta aoCriar={atualizar} />}
      {(ehMedico || ehColaborador) && <AgendaConsultas />}

      <ErroCarregamento erro={erro} />
      {carregando && !dados && <Carregando />}
      {dados?.tipo_usuario === 'paciente' && (
        <Secao id="meus-dados" titulo="Meus dados (LGPD)">
          <CardConsentimentoLgpd />
        </Secao>
      )}
    </div>
  )
}

function linkAcompanhamento(acompanhamentoId, aba) {
  return `/acompanhamentos/${acompanhamentoId}?aba=${aba}`
}

/** Frase do topo da faixa: quantos itens pedem atenção. */
function fraseAtencao(quantidade) {
  if (quantidade === 0) return 'Nada pede sua atenção agora.'
  return quantidade === 1 ? '1 item pede sua atenção.' : `${quantidade} itens pedem sua atenção.`
}

/**
 * Resumos da faixa do Painel, por tipo de usuário, e a frase com o que pede atenção (o que está
 * pendente ou para revisar; consultas agendadas não contam). Cada resumo traz o título e a lista que
 * a gaveta mostra ao ser aberto. Colaborador não tem resumos: null.
 */
function resumoDoPainel(painel) {
  if (painel.tipo_usuario === 'medico') {
    const { documentos_aguardando_revisao: documentos, solicitacoes_vencidas: vencidas } = painel
    const proximas = painel.solicitacoes_proximas_do_prazo
    const rotuloProximas = `Vencem em até ${painel.dias_prazo_proximo} dias`
    return {
      frase: fraseAtencao(documentos.length + vencidas.length + proximas.length),
      itens: [
        {
          id: 'documentos',
          icone: FileText,
          numero: documentos.length,
          rotulo: 'Documentos para revisar',
          tom: 'info',
          titulo: 'Documentos aguardando revisão',
          conteudo: <ListaDocumentos documentos={documentos} />,
        },
        {
          id: 'vencidas',
          icone: TriangleAlert,
          numero: vencidas.length,
          rotulo: 'Solicitações vencidas',
          tom: 'perigo',
          titulo: 'Solicitações vencidas',
          conteudo: (
            <ListaSolicitacoes solicitacoes={vencidas} vazio="Nenhuma solicitação vencida." mostrarPaciente mostrarDestinatario />
          ),
        },
        {
          id: 'proximas',
          icone: Clock,
          numero: proximas.length,
          rotulo: rotuloProximas,
          tom: 'alerta',
          titulo: rotuloProximas,
          conteudo: (
            <ListaSolicitacoes
              solicitacoes={proximas}
              vazio="Nenhuma solicitação vencendo nos próximos dias."
              mostrarPaciente
              mostrarDestinatario
            />
          ),
        },
      ],
    }
  }
  if (painel.tipo_usuario === 'paciente') {
    const { solicitacoes_pendentes: pendentes, consultas_extras: consultasExtras, proximas_consultas: proximas } = painel
    const vencidas = pendentes.filter((s) => s.vencida)
    return {
      frase: fraseAtencao(pendentes.length),
      itens: [
        {
          id: 'pendencias',
          icone: ClipboardList,
          numero: pendentes.length,
          rotulo: 'Pendências',
          tom: 'alerta',
          titulo: 'O que você precisa fazer',
          conteudo: <ListaSolicitacoes solicitacoes={pendentes} vazio="Nenhuma pendência no momento." />,
        },
        {
          id: 'vencidas',
          icone: TriangleAlert,
          numero: vencidas.length,
          rotulo: 'Vencidas',
          tom: 'perigo',
          titulo: 'Pendências vencidas',
          conteudo: <ListaSolicitacoes solicitacoes={vencidas} vazio="Nenhuma pendência vencida." />,
        },
        {
          id: 'consultas-extras',
          icone: CalendarClock,
          numero: consultasExtras.length,
          rotulo: 'Consultas extras marcadas',
          tom: 'info',
          titulo: 'Consultas extras marcadas pelo médico',
          conteudo: <ListaConsultasExtras consultas={consultasExtras} />,
        },
        {
          id: 'proximas-consultas',
          icone: CalendarDays,
          numero: proximas.length,
          rotulo: 'Consultas agendadas',
          tom: 'info',
          titulo: 'Suas próximas consultas',
          conteudo: <ListaAgendamentos agendamentos={proximas} vazio="Nenhuma consulta agendada no momento." />,
        },
      ],
    }
  }
  if (painel.tipo_usuario === 'parceiro') {
    const pendentes = painel.solicitacoes_pendentes
    const vazioParceiro = (
      <>
        Nenhuma solicitação pendente. Em <Link to="/acompanhamentos">Pacientes</Link> você consulta a anamnese de quem foi
        atribuído a você e envia documentos.
      </>
    )
    return {
      frase: fraseAtencao(pendentes.length),
      itens: [
        {
          id: 'pendencias',
          icone: ClipboardList,
          numero: pendentes.length,
          rotulo: 'Solicitações para você',
          tom: 'alerta',
          titulo: 'Solicitações destinadas a você',
          conteudo: <ListaSolicitacoes solicitacoes={pendentes} vazio={vazioParceiro} mostrarPaciente />,
        },
        {
          id: 'vencidas',
          icone: TriangleAlert,
          numero: pendentes.filter((s) => s.vencida).length,
          rotulo: 'Vencidas',
          tom: 'perigo',
          titulo: 'Solicitações vencidas',
          conteudo: (
            <ListaSolicitacoes
              solicitacoes={pendentes.filter((s) => s.vencida)}
              vazio="Nenhuma solicitação vencida."
              mostrarPaciente
            />
          ),
        },
      ],
    }
  }
  return null
}

/**
 * Resumo dentro da faixa: número grande com ícone colorido pelo tom (perigo | alerta | info). É um
 * botão que abre e fecha a gaveta com a lista (aria-expanded); a seta gira quando aberto.
 */
function Resumo({ id, icone: Icone, numero, rotulo, tom, aberto, aoAlternar }) {
  return (
    <button
      type="button"
      id={`resumo-${id}`}
      className={estilos.resumo}
      aria-expanded={aberto}
      aria-controls={`gaveta-${id}`}
      onClick={aoAlternar}
    >
      <span className={`${estilos.resumoIcone} ${tonsResumo[tom]}`}>
        <Icone size={20} aria-hidden="true" />
      </span>
      <span>
        <span className={estilos.resumoNumero}>{numero}</span>
        <span className={estilos.resumoRotulo}>{rotulo}</span>
      </span>
      <ChevronDown size={18} aria-hidden="true" className={cn(estilos.resumoSeta, aberto && estilos.resumoSetaAberta)} />
    </button>
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
  const agora = useAgora()
  return solicitacao.vencida ? (
    <Etiqueta variante="perigo">Venceu {formatarPrazoRelativo(solicitacao.prazo, agora)}</Etiqueta>
  ) : (
    <Etiqueta variante="alerta">Vence {formatarPrazoRelativo(solicitacao.prazo, agora)}</Etiqueta>
  )
}

/**
 * Dropdown abaixo do resumo, na largura dele, flutuando sobre o conteúdo. Abre animando a altura;
 * fechado fica inerte (o Tab e o leitor de tela não entram no que está escondido). `chave` muda a cada
 * abertura, para o conteúdo remontar e os itens entrarem em sequência de novo.
 */
function GavetaResumo({ item, aberto, chave }) {
  return (
    <div className={cn(estilos.gaveta, aberto && estilos.gavetaAberta)}>
      <div id={`gaveta-${item.id}`} className={estilos.gavetaJanela} inert={!aberto}>
        <div className={estilos.gavetaMoldura}>
          <span className={estilos.gavetaSeta} aria-hidden="true" />
          <section key={chave} aria-labelledby={`titulo-gaveta-${item.id}`} className={estilos.gavetaConteudo}>
            <div className={estilos.gavetaCabecalho}>
              <span className={`${estilos.gavetaIcone} ${tonsResumo[item.tom]}`}>
                <item.icone size={17} aria-hidden="true" />
              </span>
              <h2 id={`titulo-gaveta-${item.id}`} className={estilos.gavetaTitulo}>
                {item.titulo}
              </h2>
              <span className={estilos.gavetaQuantidade}>{item.numero}</span>
            </div>
            {item.conteudo}
          </section>
        </div>
      </div>
    </div>
  )
}

/** Os itens da gaveta entram em sequência (30ms entre eles, até o oitavo). */
function atrasoEntrada(indice) {
  return { animationDelay: `${Math.min(indice, 8) * 30}ms` }
}

/** Lista vazia dentro da gaveta: texto claro numa moldura tracejada. icone: o elemento já pronto. */
function VazioGaveta({ icone = <CircleCheck size={18} aria-hidden="true" />, children }) {
  return (
    <p className={estilos.vazioGaveta}>
      {icone}
      <span>{children}</span>
    </p>
  )
}

function ItemSolicitacao({ solicitacao, indice, mostrarPaciente, mostrarDestinatario }) {
  return (
    <li className={solicitacao.vencida ? estilos.itemGavetaDestaque : estilos.itemGaveta} style={atrasoEntrada(indice)}>
      <div className={ui.cabecalhoItem}>
        <Link to={linkAcompanhamento(solicitacao.acompanhamento.id, 'solicitacoes')} className={estilos.linkGaveta}>
          {ROTULOS_TIPO_SOLICITACAO[solicitacao.tipo]}
        </Link>
        <PrazoSolicitacao solicitacao={solicitacao} />
      </div>
      <p className={estilos.textoGaveta}>{solicitacao.descricao}</p>
      <div className={estilos.metaGaveta}>
        {mostrarPaciente && <span>{solicitacao.acompanhamento.paciente.nome}</span>}
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
  if (solicitacoes.length === 0) return <VazioGaveta>{vazio}</VazioGaveta>
  return (
    <ul className={estilos.listaGaveta}>
      {solicitacoes.map((s, indice) => (
        <ItemSolicitacao key={s.id} solicitacao={s} indice={indice} {...opcoes} />
      ))}
    </ul>
  )
}

/** Documentos enviados que aguardam a revisão do médico. */
function ListaDocumentos({ documentos }) {
  if (documentos.length === 0) return <VazioGaveta>Nenhum documento aguardando revisão.</VazioGaveta>
  return (
    <ul className={estilos.listaGaveta}>
      {documentos.map((documento, indice) => (
        <li key={documento.id} className={estilos.itemGaveta} style={atrasoEntrada(indice)}>
          <div className={ui.cabecalhoItem}>
            <Link to={linkAcompanhamento(documento.acompanhamento.id, 'documentos')} className={estilos.linkGaveta}>
              {documento.titulo}
            </Link>
            <Etiqueta variante="info">{ROTULOS_CATEGORIA[documento.categoria]}</Etiqueta>
          </div>
          <div className={estilos.metaGaveta}>
            <span>{documento.acompanhamento.paciente.nome}</span>
            {documento.enviado_por.id !== documento.acompanhamento.paciente.id && <span>Enviado por {documento.enviado_por.nome}</span>}
            <span>{formatarData(documento.criado_em)}</span>
          </div>
        </li>
      ))}
    </ul>
  )
}

/** Consultas extras que o médico marcou para o paciente. */
function ListaConsultasExtras({ consultas }) {
  const agora = useAgora()
  if (consultas.length === 0) return <VazioGaveta icone={<CalendarClock size={18} aria-hidden="true" />}>Nenhuma consulta extra marcada.</VazioGaveta>
  return (
    <ul className={estilos.listaGaveta}>
      {consultas.map((s, indice) => (
        <li key={s.id} className={estilos.itemGaveta} style={atrasoEntrada(indice)}>
          <div className={ui.cabecalhoItem}>
            <strong className="tabular-nums text-menu-texto-forte">{formatarDataHora(s.prazo)}</strong>
            <Etiqueta variante="info">{formatarPrazoRelativo(s.prazo, agora)}</Etiqueta>
          </div>
          <p className={estilos.textoGaveta}>{s.descricao}</p>
        </li>
      ))}
    </ul>
  )
}

const MENSAGEM_REVOGACAO =
  'Você pode revogar a autorização dada para o tratamento dos seus dados de saúde (LGPD, art. 18). ' +
  'As informações já registradas continuam arquivadas por guarda legal do prontuário, mas o médico ' +
  'não consegue anotar dados novos até que haja um novo aceite. Deseja revogar?'

function CardConsentimentoLgpd() {
  const [estado, setEstado] = useState(null)
  const [erro, setErro] = useState('')
  const confirmar = useConfirmar()

  // Trilha única: estado do aceite vigente (pacientes têm um só registro vigente, ou revogado)
  useEffect(() => {
    consentimentoLgpd().then(setEstado).catch(() => setEstado(null))
  }, [])

  if (!estado) return <p className={ui.ajuda}>Não foi possível ler a situação do seu consentimento.</p>

  if (estado.concedido_em == null) {
    return (
      <p className={ui.ajuda}>
        Você ainda não aceitou o termo de tratamento de dados. Ele é apresentado quando você define sua senha.
      </p>
    )
  }

  async function aoRevogar() {
    if (
      !(await confirmar({
        titulo: 'Revogar consentimento',
        mensagem: MENSAGEM_REVOGACAO,
        rotuloConfirmar: 'Revogar',
        perigo: true,
      }))
    ) {
      return
    }
    setErro('')
    try {
      const atualizado = await revogarConsentimentoLgpd()
      setEstado(atualizado)
    } catch (erroRevogacao) {
      setErro(mensagemDeErro(erroRevogacao))
    }
  }

  return (
    <div>
      <p className={ui.ajuda}>
        {estado.vigente
          ? `Consentimento vigente, concedido em ${formatarDataHora(estado.concedido_em)} (termo ${estado.versao_termo}).`
          : `Consentimento revogado em ${formatarDataHora(estado.revogado_em)}.`}
      </p>
      {estado.vigente ? (
        <>
          <button type="button" className={ui.botaoSecundario} onClick={aoRevogar}>
            Revogar consentimento
          </button>
          <p className={ui.ajuda}>
            Revogado, o médico não anota dados novos até haver novo aceite. Para aceitar o termo de novo, use
            &quot;Esqueci minha senha&quot; e defina uma nova senha.
          </p>
        </>
      ) : (
        <p className={ui.ajuda}>
          Para aceitar o termo de novo, use &quot;Esqueci minha senha&quot; e defina uma nova senha.
        </p>
      )}
      {erro && <Alerta tipo="erro">{erro}</Alerta>}
    </div>
  )
}

/** Próximas consultas do paciente, com data, distância e observação. */
function ListaAgendamentos({ agendamentos, vazio }) {
  const agora = useAgora()
  if (agendamentos.length === 0) return <VazioGaveta icone={<CalendarDays size={18} aria-hidden="true" />}>{vazio}</VazioGaveta>
  return (
    <ul className={estilos.listaGaveta}>
      {agendamentos.map((agendamento, indice) => (
        <li key={agendamento.id} className={estilos.itemGaveta} style={atrasoEntrada(indice)}>
          <div className={ui.cabecalhoItem}>
            <strong className="tabular-nums text-menu-texto-forte">{formatarDataHora(agendamento.data_hora)}</strong>
            <Etiqueta variante="info">{formatarPrazoRelativo(agendamento.data_hora, agora)}</Etiqueta>
          </div>
          {agendamento.observacao && <div className={estilos.metaGaveta}><span>{agendamento.observacao}</span></div>}
        </li>
      ))}
    </ul>
  )
}
