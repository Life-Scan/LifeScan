import { useState } from 'react'
import { Link } from 'react-router-dom'

import { mensagemDeErro } from '../api/cliente'
import { atualizarConta, criarConta, listarContas, reenviarAcesso } from '../api/servicos'
import { Alerta, Carregando, ErroCarregamento, EstadoVazio, Etiqueta, estilos as ui } from '../components/ui'
import { useAtualizacaoPeriodica } from '../hooks/useAtualizacaoPeriodica'
import { formatarData, formatarDataHora } from '../utils/formatacao'
import estilos from './Paginas.module.css'

const TEXTOS = {
  paciente: {
    titulo: 'Pacientes',
    subtitulo: 'Crie o acesso do paciente com o email informado na consulta. Os dados de acesso seguem por email.',
    novo: 'Novo paciente',
    lista: 'Pacientes cadastrados',
    vazio: 'Nenhum paciente cadastrado ainda.',
  },
  parceiro: {
    titulo: 'Parceiros',
    subtitulo: 'Profissionais que colaboram no tratamento (nutricionista, fisioterapeuta, educador físico…).',
    novo: 'Novo parceiro',
    lista: 'Parceiros cadastrados',
    vazio: 'Nenhum parceiro cadastrado ainda.',
  },
}

/** Contas de pacientes ou de parceiros, criadas e administradas pelo médico. */
export default function Contas({ tipo }) {
  const textos = TEXTOS[tipo]
  const { dados: contas, erro, carregando, atualizar } = useAtualizacaoPeriodica(
    () => listarContas(tipo),
    undefined,
    [tipo],
  )

  return (
    <div className={estilos.pilha}>
      <div className={estilos.cabecalho}>
        <div>
          <h1>{textos.titulo}</h1>
          <p className={estilos.subtitulo}>{textos.subtitulo}</p>
        </div>
      </div>

      {/* A key reinicia o formulário ao alternar entre Pacientes e Parceiros */}
      <FormularioConta key={tipo} tipo={tipo} titulo={textos.novo} aoCriar={atualizar} />

      <section className={ui.cartao}>
        <div className={ui.cartaoCabecalho}>
          <h2>{textos.lista}</h2>
        </div>
        <ErroCarregamento erro={erro} />
        {carregando && !contas && <Carregando />}
        {contas?.length === 0 && <EstadoVazio>{textos.vazio}</EstadoVazio>}
        {contas?.length > 0 && (
          <ul className={ui.lista}>
            {contas.map((conta) => (
              <ItemConta key={conta.id} conta={conta} aoAlterar={atualizar} />
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

function FormularioConta({ tipo, titulo, aoCriar }) {
  const ehParceiro = tipo === 'parceiro'
  const [formulario, setFormulario] = useState({ nome: '', email: '', profissao: '' })
  const [erro, setErro] = useState('')
  const [sucesso, setSucesso] = useState('')
  const [enviando, setEnviando] = useState(false)

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
      setSucesso(`Conta criada. Os dados de acesso foram enviados para ${conta.email}.`)
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
        <h2>{titulo}</h2>
      </div>
      <form className={ui.formulario} onSubmit={aoEnviar}>
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
            {enviando ? 'Criando…' : 'Criar conta e enviar acesso'}
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
  const [erro, setErro] = useState('')
  const [aviso, setAviso] = useState('')
  const [ocupado, setOcupado] = useState(false)
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

  function alternarAtivo() {
    const pergunta = conta.ativo
      ? `Desativar a conta de ${conta.nome}? A pessoa não conseguirá mais entrar no sistema.`
      : `Reativar a conta de ${conta.nome}?`
    if (window.confirm(pergunta)) executar(() => atualizarConta(conta.id, { ativo: !conta.ativo }))
  }

  function reenviar() {
    const pergunta = `Enviar uma nova senha provisória para ${conta.email}?`
    if (window.confirm(pergunta)) executar(() => reenviarAcesso(conta.id))
  }

  return (
    <li className={ui.itemLista}>
      <div className={ui.cabecalhoItem}>
        <div>
          <strong>{conta.nome}</strong> <SituacaoConta conta={conta} />
          <div className={estilos.meta}>
            <span>{conta.email}</span>
            {conta.profissao && <span>{conta.profissao}</span>}
            <span>Criada em {formatarData(conta.criado_em)}</span>
            {conta.ultimo_login_em && <span>Último acesso: {formatarDataHora(conta.ultimo_login_em)}</span>}
          </div>
        </div>
        <div className={ui.acoes}>
          {ehPaciente && conta.jornada_id && (
            <Link to={`/jornadas/${conta.jornada_id}`} className={`${ui.botao} ${ui.botaoPequeno}`}>
              Abrir jornada
            </Link>
          )}
          {ehPaciente && !conta.jornada_id && conta.ativo && (
            <Link to={`/jornadas/nova?paciente=${conta.id}`} className={`${ui.botao} ${ui.botaoPequeno}`}>
              Abrir nova jornada
            </Link>
          )}
          {conta.ativo && (
            <button type="button" className={`${ui.botaoSecundario} ${ui.botaoPequeno}`} onClick={reenviar} disabled={ocupado}>
              Reenviar acesso
            </button>
          )}
          <button
            type="button"
            className={`${conta.ativo ? ui.botaoPerigo : ui.botaoSecundario} ${ui.botaoPequeno}`}
            onClick={alternarAtivo}
            disabled={ocupado}
          >
            {conta.ativo ? 'Desativar' : 'Reativar'}
          </button>
        </div>
      </div>
      <Alerta tipo="erro">{erro}</Alerta>
      <Alerta tipo="sucesso">{aviso}</Alerta>
    </li>
  )
}
