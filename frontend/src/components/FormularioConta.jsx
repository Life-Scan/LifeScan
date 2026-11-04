import { UserPlus } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { mensagemDeErro } from '../api/cliente'
import { criarConta } from '../api/servicos'
import { Alerta, estilos as ui } from './ui'
import estilos from '../pages/Paginas.module.css'

const TIPOS = [
  { valor: 'paciente', rotulo: 'Paciente', descricao: 'Pessoa em tratamento' },
  { valor: 'parceiro', rotulo: 'Parceiro', descricao: 'Profissional que colabora' },
]

export default function FormularioConta({ aoCriar }) {
  const [tipo, setTipo] = useState('paciente')
  const [formulario, setFormulario] = useState({ nome: '', email: '', profissao: '' })
  const [erro, setErro] = useState('')
  const [sucesso, setSucesso] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const ehParceiro = tipo === 'parceiro'

  const alterar = (campo) => (evento) => setFormulario((atual) => ({ ...atual, [campo]: evento.target.value }))

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    setSucesso(null)
    setEnviando(true)
    try {
      const conta = await criarConta({
        tipo_usuario: tipo,
        nome: formulario.nome,
        email: formulario.email,
        ...(ehParceiro ? { profissao: formulario.profissao } : {}),
      })
      setSucesso({ nome: conta.nome, email: conta.email, tipo: conta.tipo_usuario })
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
        <Alerta tipo="sucesso">
          {sucesso && (
            <>
              Conta de {sucesso.nome} criada com sucesso. Os dados de acesso foram enviados para {sucesso.email}.{' '}
              Consulte e gerencie esse cadastro na tela de{' '}
              <Link to={sucesso.tipo === 'paciente' ? '/pacientes' : '/parceiros'}>
                {sucesso.tipo === 'paciente' ? 'Pacientes' : 'Parceiros'}
              </Link>.
            </>
          )}
        </Alerta>
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
