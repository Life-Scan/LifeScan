import { Check, MailCheck, Pencil, Route, UserCheck, UserPlus, UserX, Users, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { mensagemDeErro } from '../api/cliente'
import { atualizarConta, criarConta, listarContas, reenviarAcesso } from '../api/servicos'
import { useConfirmar } from '../components/Confirmacao'
import { Alerta, Avatar, Carregando, ErroCarregamento, EstadoVazio, Etiqueta, estilos as ui } from '../components/ui'
import { useAtualizacaoPeriodica } from '../hooks/useAtualizacaoPeriodica'
import { formatarData, formatarDataHora } from '../utils/formatacao'
import estilos from './Paginas.module.css'

const TIPOS = [
  { valor: 'paciente', rotulo: 'Paciente', descricao: 'Pessoa em tratamento' },
  { valor: 'parceiro', rotulo: 'Parceiro', descricao: 'Profissional que colabora' },
]

/** Pacientes e parceiros em uma única tela: o médico cria as contas e as administra. */
export default function Usuarios() {
  const { dados: contas, erro, carregando, atualizar } = useAtualizacaoPeriodica(() => listarContas())

  const pacientes = contas?.filter((conta) => conta.tipo_usuario === 'paciente')
  const parceiros = contas?.filter((conta) => conta.tipo_usuario === 'parceiro')

  return (
    <div className={estilos.pilha}>
      <div className={estilos.cabecalho}>
        <div>
          <h1>Pacientes e parceiros</h1>
          <p className={estilos.subtitulo}>
            Crie o acesso de quem participa dos tratamentos. Os dados de acesso seguem por email.
          </p>
        </div>
      </div>

      <FormularioConta aoCriar={atualizar} />

      <ErroCarregamento erro={erro} />
      {carregando && !contas && <Carregando />}

      {contas && (
        <>
          <SecaoContas
            titulo="Pacientes"
            contas={pacientes}
            vazio="Nenhum paciente cadastrado ainda."
            aoAlterar={atualizar}
          />
          <SecaoContas
            titulo="Parceiros"
            contas={parceiros}
            vazio="Nenhum parceiro cadastrado ainda. Parceiros são profissionais como nutricionista, fisioterapeuta ou educador físico."
            aoAlterar={atualizar}
          />
        </>
      )}
    </div>
  )
}

function SecaoContas({ titulo, contas, vazio, aoAlterar }) {
  return (
    <section className={ui.cartao} aria-label={titulo}>
      <div className={ui.cartaoCabecalho}>
        <h2>
          {titulo} <span className={estilos.contagem}>{contas.length}</span>
        </h2>
      </div>
      {contas.length === 0 ? (
        <EstadoVazio icone={Users}>{vazio}</EstadoVazio>
      ) : (
        <ul className={ui.lista}>
          {contas.map((conta) => (
            <ItemConta key={conta.id} conta={conta} aoAlterar={aoAlterar} />
          ))}
        </ul>
      )}
    </section>
  )
}

function FormularioConta({ aoCriar }) {
  const [tipo, setTipo] = useState('paciente')
  const [formulario, setFormulario] = useState({ nome: '', email: '', profissao: '' })
  const [erro, setErro] = useState('')
  const [sucesso, setSucesso] = useState('')
  const [enviando, setEnviando] = useState(false)
  const ehParceiro = tipo === 'parceiro'

  const alterar = (campo) => (evento) => setFormulario((atual) => ({ ...atual, [campo]: evento.target.value }))

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    setSucesso('')
    setEnviando(true)
    try {
      const conta = await criarConta({
        tipo_usuario: tipo,
        nome: formulario.nome,
        email: formulario.email,
        ...(ehParceiro ? { profissao: formulario.profissao } : {}),
      })
      setSucesso(`Conta de ${conta.nome} criada. Os dados de acesso foram enviados para ${conta.email}.`)
      setFormulario({ nome: '', email: '', profissao: '' })
      aoCriar()
    } catch (erroCriacao) {
      setErro(mensagemDeErro(erroCriacao))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <section className={ui.cartao}>
      <div className={ui.cartaoCabecalho}>
        <h2>Novo usuário</h2>
      </div>
      <form className={ui.formulario} onSubmit={aoEnviar}>
        <fieldset className={estilos.escolha}>
          <legend>Quem você está cadastrando?</legend>
          {TIPOS.map(({ valor, rotulo, descricao }) => (
            <label key={valor} className={tipo === valor ? estilos.opcaoSelecionada : estilos.opcao}>
              <input
                type="radio"
                name="tipo-usuario"
                value={valor}
                checked={tipo === valor}
                onChange={() => setTipo(valor)}
              />
              <span className={estilos.opcaoRotulo}>{rotulo}</span>
              <span className={estilos.opcaoDescricao}>{descricao}</span>
            </label>
          ))}
        </fieldset>

        <div className={ui.linhaCampos}>
          <div>
            <label htmlFor="conta-nome">Nome completo</label>
            <input id="conta-nome" value={formulario.nome} onChange={alterar('nome')} required minLength={2} maxLength={120} />
          </div>
          <div>
            <label htmlFor="conta-email">Email</label>
            <input id="conta-email" type="email" value={formulario.email} onChange={alterar('email')} required />
          </div>
          {ehParceiro && (
            <div>
              <label htmlFor="conta-profissao">Profissão</label>
              <input
                id="conta-profissao"
                value={formulario.profissao}
                onChange={alterar('profissao')}
                placeholder="Ex.: Nutricionista"
                required
                minLength={2}
                maxLength={100}
              />
            </div>
          )}
        </div>
        <Alerta tipo="erro">{erro}</Alerta>
        <Alerta tipo="sucesso">{sucesso}</Alerta>
        <div className={ui.acoes}>
          <button type="submit" className={ui.botao} disabled={enviando}>
            <UserPlus size={16} aria-hidden="true" />
            {enviando ? 'Criando…' : `Criar ${ehParceiro ? 'parceiro' : 'paciente'} e enviar acesso`}
          </button>
          <span className={ui.ajuda}>
            A pessoa recebe uma senha provisória por email e define a própria senha no primeiro acesso.
          </span>
        </div>
      </form>
    </section>
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
  const [editandoEmail, setEditandoEmail] = useState(false)
  const [novoEmail, setNovoEmail] = useState(conta.email)
  const [reenviarAposSalvar, setReenviarAposSalvar] = useState(true)
  const ehPaciente = conta.tipo_usuario === 'paciente'

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
            mensagem: 'A pessoa não conseguirá mais entrar no sistema. Os dados dela são mantidos e a conta pode ser reativada.',
            rotuloConfirmar: 'Desativar conta',
            perigo: true,
          }
        : {
            titulo: `Reativar a conta de ${conta.nome}?`,
            mensagem: 'A pessoa volta a poder entrar com a senha que já tinha.',
            rotuloConfirmar: 'Reativar conta',
          },
    )
    if (confirmado) executar(() => atualizarConta(conta.id, { ativo: !conta.ativo }))
  }

  useEffect(() => {
    setNovoEmail(conta.email)
  }, [conta.email])

  async function reenviar() {
    const confirmado = await confirmar({
      titulo: 'Reenviar os dados de acesso?',
      mensagem: `Uma nova senha provisória será enviada para ${conta.email}. A anterior deixa de valer.`,
      rotuloConfirmar: 'Reenviar acesso',
    })
    if (confirmado) executar(() => reenviarAcesso(conta.id))
  }

  async function salvarEmail(evento) {
    evento.preventDefault()
    const emailLimpo = novoEmail.trim().toLowerCase()
    if (!emailLimpo) return
    if (emailLimpo === conta.email.toLowerCase()) {
      setEditandoEmail(false)
      return
    }

    setErro('')
    setAviso('')
    setOcupado(true)
    try {
      await atualizarConta(conta.id, { email: emailLimpo })
      let mensagemSucesso = `Email de ${conta.nome} alterado com sucesso para ${emailLimpo}.`
      if (reenviarAposSalvar && conta.ativo) {
        try {
          const resultadoReenvio = await reenviarAcesso(conta.id)
          if (resultadoReenvio?.mensagem) {
            mensagemSucesso = `${mensagemSucesso} Novos dados de acesso enviados!`
          }
        } catch (erroEnvio) {
          mensagemSucesso = `${mensagemSucesso} (Aviso: email alterado com sucesso, mas o envio de email falhou: ${mensagemDeErro(erroEnvio)})`
        }
      }
      setAviso(mensagemSucesso)
      setEditandoEmail(false)
      await aoAlterar()
    } catch (erroSalvar) {
      setErro(mensagemDeErro(erroSalvar))
    } finally {
      setOcupado(false)
    }
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
          {ehPaciente && conta.jornada_id && (
            <Link to={`/jornadas/${conta.jornada_id}`} className={`${ui.botao} ${ui.botaoPequeno}`}>
              <Route size={14} aria-hidden="true" />
              Abrir jornada
            </Link>
          )}
          {ehPaciente && !conta.jornada_id && conta.ativo && (
            <Link to={`/jornadas/nova?paciente=${conta.id}`} className={`${ui.botao} ${ui.botaoPequeno}`}>
              <Route size={14} aria-hidden="true" />
              Abrir nova jornada
            </Link>
          )}
          {conta.ativo && (
            <button
              type="button"
              className={`${ui.botaoSecundario} ${ui.botaoPequeno}`}
              onClick={() => {
                setNovoEmail(conta.email)
                setEditandoEmail((atual) => !atual)
                setErro('')
                setAviso('')
              }}
              disabled={ocupado}
              title="Editar email"
            >
              <Pencil size={14} aria-hidden="true" />
              Editar email
            </button>
          )}
          {conta.ativo && (
            <button type="button" className={`${ui.botaoSecundario} ${ui.botaoPequeno}`} onClick={reenviar} disabled={ocupado}>
              <MailCheck size={14} aria-hidden="true" />
              Reenviar acesso
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
        </div>
      </div>

      {editandoEmail && (
        <form onSubmit={salvarEmail} className={estilos.edicaoEmail}>
          <div className={estilos.edicaoEmailLinha}>
            <div className={estilos.edicaoEmailCampo}>
              <label htmlFor={`email-${conta.id}`}>Novo endereço de email de {conta.nome}:</label>
              <input
                id={`email-${conta.id}`}
                type="email"
                value={novoEmail}
                onChange={(e) => setNovoEmail(e.target.value)}
                required
                autoFocus
                disabled={ocupado}
                placeholder="novo.email@exemplo.com"
              />
            </div>
            {conta.ativo && (
              <div className={estilos.edicaoEmailOpcoes}>
                <label className={estilos.opcaoCheck}>
                  <input
                    type="checkbox"
                    checked={reenviarAposSalvar}
                    onChange={(e) => setReenviarAposSalvar(e.target.checked)}
                    disabled={ocupado}
                  />
                  Enviar dados de acesso para o novo email após salvar
                </label>
              </div>
            )}
            <div className={estilos.edicaoEmailBotoes}>
              <button type="submit" className={`${ui.botao} ${ui.botaoPequeno}`} disabled={ocupado}>
                <Check size={14} aria-hidden="true" />
                Salvar email
              </button>
              <button
                type="button"
                className={`${ui.botaoSecundario} ${ui.botaoPequeno}`}
                onClick={() => {
                  setEditandoEmail(false)
                  setNovoEmail(conta.email)
                }}
                disabled={ocupado}
              >
                <X size={14} aria-hidden="true" />
                Cancelar
              </button>
            </div>
          </div>
        </form>
      )}

      <Alerta tipo="erro">{erro}</Alerta>
      <Alerta tipo="sucesso">{aviso}</Alerta>
    </li>
  )
}
