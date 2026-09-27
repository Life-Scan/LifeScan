import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { mensagemDeErro } from '../api/cliente'
import { Alerta, estilos as ui } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import estilos from './Auth.module.css'

const PAPEIS = [
  { valor: 'paciente', rotulo: 'Paciente', descricao: 'Acompanho meu tratamento' },
  { valor: 'medico', rotulo: 'Médico(a)', descricao: 'Acompanho meus pacientes' },
]

export default function Cadastro() {
  const { cadastrar } = useAuth()
  const navegar = useNavigate()

  const [formulario, setFormulario] = useState({ nome: '', email: '', senha: '', confirmacao: '', papel: 'paciente' })
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  const alterar = (campo) => (evento) => setFormulario((atual) => ({ ...atual, [campo]: evento.target.value }))

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    if (formulario.senha !== formulario.confirmacao) {
      setErro('As senhas não conferem.')
      return
    }
    setEnviando(true)
    try {
      const { nome, email, senha, papel } = formulario
      await cadastrar({ nome, email, senha, papel })
      navegar('/painel', { replace: true })
    } catch (erroCadastro) {
      setErro(mensagemDeErro(erroCadastro))
      setEnviando(false)
    }
  }

  return (
    <div className={estilos.fundo}>
      <div className={estilos.caixa}>
        <div className={estilos.marca}>
          <img src="/favicon.svg" alt="" width="36" height="36" />
          LifeScan
        </div>
        <p className={estilos.slogan}>Crie sua conta para começar.</p>

        <div className={ui.cartao}>
          <h1 className={estilos.titulo}>Cadastro</h1>
          <form className={ui.formulario} onSubmit={aoEnviar}>
            <Alerta tipo="erro">{erro}</Alerta>

            <fieldset className={estilos.papeis}>
              <legend>Tipo de conta</legend>
              {PAPEIS.map(({ valor, rotulo, descricao }) => (
                <label
                  key={valor}
                  className={formulario.papel === valor ? estilos.papelSelecionado : estilos.papel}
                >
                  <input
                    type="radio"
                    name="papel"
                    value={valor}
                    checked={formulario.papel === valor}
                    onChange={alterar('papel')}
                  />
                  {rotulo}
                  <small>{descricao}</small>
                </label>
              ))}
            </fieldset>

            <div>
              <label htmlFor="nome">Nome completo</label>
              <input id="nome" autoComplete="name" value={formulario.nome} onChange={alterar('nome')} required minLength={2} />
            </div>
            <div>
              <label htmlFor="email">Email</label>
              <input id="email" type="email" autoComplete="email" value={formulario.email} onChange={alterar('email')} required />
            </div>
            <div className={ui.linhaCampos}>
              <div>
                <label htmlFor="senha">Senha</label>
                <input
                  id="senha"
                  type="password"
                  autoComplete="new-password"
                  value={formulario.senha}
                  onChange={alterar('senha')}
                  required
                  minLength={6}
                />
              </div>
              <div>
                <label htmlFor="confirmacao">Confirmar senha</label>
                <input
                  id="confirmacao"
                  type="password"
                  autoComplete="new-password"
                  value={formulario.confirmacao}
                  onChange={alterar('confirmacao')}
                  required
                />
              </div>
            </div>
            <p className={ui.ajuda}>A senha precisa ter pelo menos 6 caracteres.</p>

            <button type="submit" className={ui.botao} disabled={enviando}>
              {enviando ? 'Criando conta…' : 'Criar conta'}
            </button>
          </form>
          <p className={estilos.rodape}>
            Já tem conta? <Link to="/login">Entrar</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
