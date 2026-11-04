import { ChevronDown, ChevronUp, MailCheck, Pencil, Route, Search, Trash2, UserCheck, Users, UserX } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { mensagemDeErro } from '../api/cliente'
import { atualizarConta, excluirPaciente, obterPagina, reenviarAcesso } from '../api/servicos'
import Paginacao from '../components/Paginacao'
import { useConfirmar } from '../components/Confirmacao'
import { Alerta, Avatar, Carregando, ErroCarregamento, EstadoVazio, Etiqueta, estilos as ui } from '../components/ui'
import { useAtualizacaoPeriodica } from '../hooks/useAtualizacaoPeriodica'
import { formatarData, formatarDataHora } from '../utils/formatacao'
import estilos from './Paginas.module.css'


/** Listagem de pacientes ou parceiros, conforme a tela acessada pelo médico. */
export default function Usuarios({ tipo }) {
  const titulo = tipo === 'paciente' ? 'Pacientes' : 'Parceiros'
  return (
    <div className={estilos.pilha}>
      <div className={estilos.cabecalho}>
        <div>
          <h1>{titulo}</h1>
          <p className={estilos.subtitulo}>
            Busque {titulo.toLowerCase()} e gerencie seus acessos.
          </p>
        </div>
      </div>

      <SecaoContas key={tipo} tipo={tipo} />
    </div>
  )
}

function SecaoContas({ tipo }) {
  const [textoBusca, setTextoBusca] = useState('')
  const [busca, setBusca] = useState('')
  const [aba, setAba] = useState('ativos')
  const [recolhida, setRecolhida] = useState(false)
  useEffect(() => {
    const temporizador = setTimeout(() => setBusca(textoBusca.trim()), 200)
    return () => clearTimeout(temporizador)
  }, [textoBusca])
  const [paginacao, setPaginacao] = useState({ numero: 1, busca })
  const pagina = paginacao.busca === busca ? paginacao.numero : 1
  const setPagina = (numero) => setPaginacao({ numero, busca })
  const { dados, erro, carregando, atualizar } = useAtualizacaoPeriodica(async () => {
    const [atual, outra] = await Promise.all([
      obterPagina('/users', { tipo, ativo: aba === 'ativos', pagina, busca }),
      obterPagina('/users', { tipo, ativo: aba !== 'ativos', tamanho: 1, busca }),
    ])
    return { ...atual, ativos: aba === 'ativos' ? atual.total : outra.total, desativados: aba === 'desativados' ? atual.total : outra.total }
  }, undefined, [tipo, aba, pagina, busca])
  useEffect(() => { if (dados) setPagina(dados.pagina) }, [dados?.pagina])
  const titulo = tipo === 'paciente' ? 'Pacientes' : 'Parceiros'
  const plural = titulo.toLowerCase()
  const abas = [
    { id: 'ativos', titulo, vazio: `Nenhum ${tipo} ativo. Crie uma conta ou reative um ${tipo} na aba ${titulo} desativados.` },
    { id: 'desativados', titulo: `${titulo} desativados`, vazio: `Nenhum ${tipo} desativado.` },
  ]
  const selecionada = abas.find((item) => item.id === aba)

  function mudarAba(valor) {
    setAba(valor)
    setPagina(1)
    setRecolhida(false)
  }

  function navegarAbas(evento, indice) {
    let destino
    if (evento.key === 'ArrowRight' || evento.key === 'ArrowLeft') destino = 1 - indice
    else if (evento.key === 'Home') destino = 0
    else if (evento.key === 'End') destino = 1
    else return
    evento.preventDefault()
    mudarAba(abas[destino].id)
    document.getElementById(`aba-${plural}-${abas[destino].id}`).focus()
  }

  return (
    <section className={ui.cartao} aria-label={titulo}>
      <div className={estilos.cabecalhoContas}>
        <div className={estilos.abasPacientes} role="tablist" aria-label={`Situação dos ${plural}`}>
          {abas.map((item, indice) => (
            <button
              key={item.id}
              type="button"
              role="tab"
              id={`aba-${plural}-${item.id}`}
              aria-controls={`painel-${plural}`}
              aria-selected={aba === item.id}
              tabIndex={aba === item.id ? 0 : -1}
              className={estilos.abaPacientes}
              onClick={() => mudarAba(item.id)}
              onKeyDown={(evento) => navegarAbas(evento, indice)}
            >
              {item.titulo} {dados && <span className={estilos.contagem}>{dados[item.id]}</span>}
            </button>
          ))}
        </div>
        <div role="search" aria-label={`Buscar ${plural}`} className={estilos.buscaContas}>
          <label className="visualmente-oculto" htmlFor={`busca-${tipo}`}>Buscar {plural} por nome ou e-mail</label>
          <input
            id={`busca-${tipo}`}
            type="text"
            role="searchbox"
            placeholder="Buscar por nome ou e-mail"
            value={textoBusca}
            onChange={(evento) => {
              setTextoBusca(evento.target.value)
              setRecolhida(false)
              if (!evento.target.value.trim()) setBusca('')
            }}
            maxLength={255}
          />
          <Search className={estilos.iconeBuscaContas} size={18} aria-hidden="true" />
        </div>
        <button
          type="button"
          className={estilos.recolherContas}
          aria-label={`${recolhida ? 'Expandir' : 'Recolher'} lista de ${plural}`}
          title={`${recolhida ? 'Expandir' : 'Recolher'} lista de ${plural}`}
          aria-expanded={!recolhida}
          aria-controls={`painel-${plural}`}
          onClick={() => setRecolhida((atual) => !atual)}
        >
          {recolhida ? <ChevronDown size={20} aria-hidden="true" /> : <ChevronUp size={20} aria-hidden="true" />}
        </button>
      </div>
      <div role="tabpanel" id={`painel-${plural}`} aria-labelledby={`aba-${plural}-${aba}`} tabIndex={0} hidden={recolhida}>
        <ErroCarregamento erro={erro} />
        {carregando && !dados && <Carregando />}
        {dados && <ListaContas contas={dados.itens} vazio={busca ? `Nenhum ${tipo} ${aba === 'ativos' ? 'ativo' : 'desativado'} encontrado para “${busca}”.` : selecionada.vazio} aoAlterar={atualizar} />}
        <Paginacao dados={dados} aoMudar={setPagina} carregando={carregando} />
      </div>
    </section>
  )
}

function ListaContas({ contas, vazio, aoAlterar }) {
  if (contas.length === 0) return <EstadoVazio icone={Users}>{vazio}</EstadoVazio>
  return (
    <ul className={ui.lista}>
      {contas.map((conta) => <ItemConta key={conta.id} conta={conta} aoAlterar={aoAlterar} />)}
    </ul>
  )
}

function SituacaoConta({ conta }) {
  if (!conta.ativo) return <Etiqueta>Desativada</Etiqueta>
  if (conta.primeiro_acesso_pendente) return <Etiqueta variante="alerta">Aguardando primeiro acesso</Etiqueta>
  return <Etiqueta variante="sucesso">Ativa</Etiqueta>
}

function ItemConta({ conta, aoAlterar }) {
  const confirmar = useConfirmar()
  const [erro, setErro] = useState('')
  const [aviso, setAviso] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const [editando, setEditando] = useState(false)
  const ehPaciente = conta.tipo_usuario === 'paciente'
  const tipo = ehPaciente ? 'paciente' : 'parceiro'
  const lista = ehPaciente ? 'Pacientes' : 'Parceiros'

  async function executar(acao) {
    setErro('')
    setAviso('')
    setOcupado(true)
    try {
      const resultado = await acao()
      if (resultado?.mensagem) setAviso(resultado.mensagem)
      await aoAlterar()
    } catch (erroAcao) {
      setErro(mensagemDeErro(erroAcao))
    } finally {
      setOcupado(false)
    }
  }

  async function alternarAtivo() {
    const confirmado = await confirmar(
      conta.ativo
        ? {
            titulo: `Desativar a conta de ${conta.nome}?`,
            mensagem: `O ${tipo} será movido para a aba ${lista} desativados e perderá o acesso ao sistema. O histórico será mantido e a conta poderá ser reativada nessa aba.`,
            rotuloConfirmar: `Desativar ${tipo}`,
            perigo: true,
          }
        : {
            titulo: `Reativar a conta de ${conta.nome}?`,
            mensagem: `O ${tipo} voltará à lista de ${lista} e poderá entrar com a senha que já tinha.`,
            rotuloConfirmar: 'Reativar conta',
          },
    )
    if (confirmado) executar(() => atualizarConta(conta.id, { ativo: !conta.ativo }))
  }

  async function reenviar() {
    const confirmado = await confirmar({
      titulo: 'Reenviar os dados de acesso?',
      mensagem: `Uma nova senha provisória será enviada para ${conta.email}. A anterior deixa de valer.`,
      rotuloConfirmar: 'Reenviar acesso',
    })
    if (confirmado) executar(() => reenviarAcesso(conta.id))
  }

  async function excluir() {
    const confirmado = await confirmar({
      titulo: `Excluir definitivamente ${conta.nome}?`,
      mensagem: `A conta ${conta.email} será apagada e o email poderá ser usado em um novo cadastro. Essa ação não pode ser desfeita. Pacientes com acompanhamento ou histórico vinculado não podem ser excluídos.`,
      rotuloConfirmar: 'Excluir paciente',
      perigo: true,
    })
    if (confirmado) executar(() => excluirPaciente(conta.id))
  }

  async function salvarEdicao(dados, reenviarAposSalvar) {
    const atualizada = await atualizarConta(conta.id, dados)
    let avisoEnvio = ''
    if (reenviarAposSalvar && atualizada.email !== conta.email) {
      try {
        await reenviarAcesso(conta.id)
        avisoEnvio = ' Novos dados de acesso enviados para o novo email.'
      } catch (erroEnvio) {
        avisoEnvio = ` Os dados foram salvos, mas o envio falhou: ${mensagemDeErro(erroEnvio)}`
      }
    }
    await aoAlterar()
    setEditando(false)
    setErro('')
    setAviso((atualizada.email !== conta.email
      ? 'Dados atualizados. O novo email será usado para entrar no sistema. Se necessário, use Reenviar acesso.'
      : `Dados do ${tipo} atualizados.`) + avisoEnvio)
  }

  if (editando && conta.ativo) {
    return (
      <li className={ui.itemLista}>
        <FormularioEdicaoConta conta={conta} aoSalvar={salvarEdicao} aoCancelar={() => setEditando(false)} />
      </li>
    )
  }

  return (
    <li className={ui.itemLista}>
      <div className={ui.linhaComAcoes}>
        <div className={ui.pessoa}>
          <Avatar nome={conta.nome} tipo={conta.tipo_usuario} />
          <div>
            <div className={ui.pessoaNome}>
              {conta.nome} <SituacaoConta conta={conta} />
            </div>
            <div className={estilos.meta}>
              {conta.profissao && <span>{conta.profissao}</span>}
              <span>{conta.email}</span>
              <span>Criada em {formatarData(conta.criado_em)}</span>
              {conta.ultimo_login_em && <span>Último acesso: {formatarDataHora(conta.ultimo_login_em)}</span>}
            </div>
          </div>
        </div>
        <div className={ui.acoes}>
          {ehPaciente && conta.acompanhamento_id && (
            <Link to={`/acompanhamentos/${conta.acompanhamento_id}`} className={`${ui.botao} ${ui.botaoPequeno}`}>
              <Route size={14} aria-hidden="true" />
              Abrir acompanhamento
            </Link>
          )}
          {ehPaciente && !conta.acompanhamento_id && conta.ativo && (
            <Link to={`/acompanhamentos/novo?paciente=${conta.id}`} className={`${ui.botao} ${ui.botaoPequeno}`}>
              <Route size={14} aria-hidden="true" />
              Abrir novo acompanhamento
            </Link>
          )}
          {conta.ativo && (
            <button type="button" className={`${ui.botaoSecundario} ${ui.botaoPequeno}`} onClick={reenviar} disabled={ocupado}>
              <MailCheck size={14} aria-hidden="true" />
              Reenviar acesso
            </button>
          )}
          {conta.ativo && (
            <button type="button" className={`${ui.botaoSecundario} ${ui.botaoPequeno}`} onClick={() => setEditando(true)} disabled={ocupado}>
              <Pencil size={14} aria-hidden="true" />
              Editar
            </button>
          )}
          <button
            type="button"
            className={`${conta.ativo ? ui.botaoPerigo : ui.botaoSecundario} ${ui.botaoPequeno}`}
            onClick={alternarAtivo}
            disabled={ocupado}
          >
            {conta.ativo ? <UserX size={14} aria-hidden="true" /> : <UserCheck size={14} aria-hidden="true" />}
            {conta.ativo ? 'Desativar' : 'Reativar'}
          </button>
          {ehPaciente && !conta.ativo && (
            <button type="button" className={`${ui.botaoPerigo} ${ui.botaoPequeno}`} onClick={excluir} disabled={ocupado}>
              <Trash2 size={14} aria-hidden="true" />
              Excluir
            </button>
          )}
        </div>
      </div>
      <Alerta tipo="erro">{erro}</Alerta>
      <Alerta tipo="sucesso">{aviso}</Alerta>
    </li>
  )
}

function FormularioEdicaoConta({ conta, aoSalvar, aoCancelar }) {
  const ehParceiro = conta.tipo_usuario === 'parceiro'
  const tipo = ehParceiro ? 'parceiro' : 'paciente'
  const [nome, setNome] = useState(conta.nome)
  const [email, setEmail] = useState(conta.email)
  const [profissao, setProfissao] = useState(conta.profissao || '')
  const [reenviarAposSalvar, setReenviarAposSalvar] = useState(true)
  const [erro, setErro] = useState('')
  const [salvando, setSalvando] = useState(false)

  async function enviar(evento) {
    evento.preventDefault()
    setErro('')
    setSalvando(true)
    try {
      await aoSalvar({ nome: nome.trim(), email: email.trim(), ...(ehParceiro ? { profissao: profissao.trim() } : {}) }, reenviarAposSalvar)
    } catch (erroEdicao) {
      setErro(mensagemDeErro(erroEdicao))
    } finally {
      setSalvando(false)
    }
  }

  return (
    <form className={ui.formulario} onSubmit={enviar} aria-label={`Editar ${tipo} ${conta.nome}`}>
      <h3>Editar {tipo}</h3>
      <fieldset className={estilos.camposEdicao} disabled={salvando}>
        <legend className="visualmente-oculto">Dados do {tipo}</legend>
        <div className={ui.linhaCampos}>
          <div>
            <label htmlFor={`editar-nome-${conta.id}`}>Nome completo</label>
            <input id={`editar-nome-${conta.id}`} value={nome} onChange={(evento) => setNome(evento.target.value)} required minLength={2} maxLength={120} autoFocus />
          </div>
          <div>
            <label htmlFor={`editar-email-${conta.id}`}>Email</label>
            <input id={`editar-email-${conta.id}`} type="email" value={email} onChange={(evento) => setEmail(evento.target.value)} required maxLength={255} aria-describedby={`ajuda-email-${conta.id}`} />
          </div>
          {ehParceiro && (
            <div>
              <label htmlFor={`editar-profissao-${conta.id}`}>Profissão</label>
              <input id={`editar-profissao-${conta.id}`} value={profissao} onChange={(evento) => setProfissao(evento.target.value)} required minLength={2} maxLength={100} />
            </div>
          )}
        </div>
        <p id={`ajuda-email-${conta.id}`} className={ui.ajuda}>O email é usado para entrar no sistema e receber os dados de acesso.</p>
        <label className={estilos.opcaoCheck}>
          <input type="checkbox" checked={reenviarAposSalvar} onChange={(evento) => setReenviarAposSalvar(evento.target.checked)} />
          Enviar novos dados de acesso se o email for alterado
        </label>
        <Alerta tipo="erro">{erro}</Alerta>
        <div className={ui.acoes}>
          <button type="submit" className={ui.botao}>{salvando ? 'Salvando…' : 'Salvar alterações'}</button>
          <button type="button" className={ui.botaoSecundario} onClick={aoCancelar}>Cancelar</button>
        </div>
      </fieldset>
    </form>
  )
}
