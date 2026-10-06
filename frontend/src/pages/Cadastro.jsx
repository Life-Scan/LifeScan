import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { mensagemDeErro } from '../api/cliente'
import { Alerta } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import estilos from './Login.module.css'
import cadastro from './Cadastro.module.css'

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
    <main className={estilos.fundo}>
      <div className={estilos.caixa}>
        <section className={estilos.apresentacao} aria-labelledby="titulo-apresentacao">
          <div className={estilos.marca}>
            <img src="/favicon.svg" alt="" width="44" height="44" />
            <span>LifeScan<span className={estilos.descricaoMarca}>CUIDADO QUE CONECTA</span></span>
          </div>
          <div className={estilos.mensagem}>
            <p className={estilos.sobretitulo}>UMA NOVA JORNADA COMEÇA AQUI</p>
            <h2 id="titulo-apresentacao">O primeiro passo{' '}<br />para um cuidado{' '}<br />mais próximo.</h2>
            <p>Conecte-se ao seu cuidado. Médico e paciente, juntos entre uma consulta e outra.</p>
          </div>
          <ul className={cadastro.beneficios}>
            <li><span aria-hidden="true">01</span><div><strong>Tratamento em um só lugar</strong><p>Consultas, exames e orientações organizados.</p></div></li>
            <li><span aria-hidden="true">02</span><div><strong>Mais clareza em cada etapa</strong><p>Acompanhe os próximos passos da jornada.</p></div></li>
            <li><span aria-hidden="true">03</span><div><strong>Uma conexão que continua</strong><p>Troque mensagens ao longo do tratamento.</p></div></li>
          </ul>
          <p className={estilos.nota}>Médico e paciente. Uma jornada compartilhada.</p>
        </section>

        <section className={`${estilos.acesso} ${cadastro.acesso}`} aria-labelledby="titulo-cadastro">
          <div className={`${estilos.formularioCaixa} ${cadastro.conteudo}`}>
          <p className={estilos.sobretitulo}>FAÇA PARTE DO LIFESCAN</p>
          <h1 id="titulo-cadastro" className={estilos.titulo}>Crie sua conta</h1>
          <p className={estilos.subtitulo}>Comece uma jornada de cuidado mais conectado.</p>
          <form className={`${estilos.formulario} ${cadastro.formulario}`} onSubmit={aoEnviar}>
            <Alerta tipo="erro">{erro}</Alerta>

            <fieldset className={cadastro.papeis}>
              <legend>Como você vai usar o LifeScan?</legend>
              {PAPEIS.map(({ valor, rotulo, descricao }) => (
                <label
                  key={valor}
                  className={`${cadastro.papel} ${formulario.papel === valor ? cadastro.selecionado : ''}`}
                >
                  <input
                    type="radio"
                    name="papel"
                    value={valor}
                    checked={formulario.papel === valor}
                    onChange={alterar('papel')}
                  />
                  <span><strong>{rotulo}</strong><small>{descricao}</small></span>
                </label>
              ))}
            </fieldset>

            <div>
              <label htmlFor="nome">Nome completo</label>
              <input id="nome" autoComplete="name" placeholder="Como podemos chamar você?" value={formulario.nome} onChange={alterar('nome')} required minLength={2} />
            </div>
            <div>
              <label htmlFor="email">Email</label>
              <input id="email" type="email" autoComplete="email" placeholder="voce@exemplo.com" value={formulario.email} onChange={alterar('email')} required />
            </div>
            <div className={cadastro.senhas}>
              <div>
                <label htmlFor="senha">Senha</label>
                <input
                  id="senha"
                  type="password"
                  autoComplete="new-password"
                  placeholder="Crie uma senha"
                  aria-describedby="ajuda-senha"
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
                  placeholder="Repita sua senha"
                  value={formulario.confirmacao}
                  onChange={alterar('confirmacao')}
                  required
                />
              </div>
            </div>
            <p id="ajuda-senha" className={cadastro.ajuda}>Use pelo menos 6 caracteres na sua senha.</p>

            <button type="submit" className={estilos.botao} disabled={enviando}>
              {enviando ? 'Criando conta…' : 'Criar minha conta'}<span aria-hidden="true">→</span>
            </button>
          </form>
          <p className={estilos.rodape}>
            Já tem conta? <Link to="/login">Entrar na minha conta</Link>
          </p>
          <p className={`${estilos.assinatura} ${cadastro.assinatura}`}>Seu cuidado tem continuidade aqui.</p>
          </div>
        </section>
      </div>
    </main>
  )
}
