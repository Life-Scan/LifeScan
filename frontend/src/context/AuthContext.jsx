import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { CHAVE_TOKEN } from '../api/cliente'
import * as servicos from '../api/servicos'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  // Enquanto valida o token salvo, as rotas protegidas mostram "carregando"
  const [carregando, setCarregando] = useState(() => Boolean(localStorage.getItem(CHAVE_TOKEN)))

  useEffect(() => {
    if (!localStorage.getItem(CHAVE_TOKEN)) return
    servicos
      .obterUsuarioAtual()
      .then(setUsuario)
      .catch(() => localStorage.removeItem(CHAVE_TOKEN))
      .finally(() => setCarregando(false))
  }, [])

  const entrar = useCallback(async (email, senha) => {
    const { token_acesso: token, usuario: dadosUsuario } = await servicos.entrar(email, senha)
    localStorage.setItem(CHAVE_TOKEN, token)
    setUsuario(dadosUsuario)
    return dadosUsuario
  }, [])

  /** Troca a senha e atualiza o usuário em memória (libera quem entrou com a provisória). */
  const trocarSenha = useCallback(async (senhaAtual, novaSenha) => {
    const atualizado = await servicos.trocarSenha(senhaAtual, novaSenha)
    setUsuario(atualizado)
    return atualizado
  }, [])

  const sair = useCallback(() => {
    localStorage.removeItem(CHAVE_TOKEN)
    setUsuario(null)
  }, [])

  const valor = useMemo(
    () => ({
      usuario,
      carregando,
      ehMedico: usuario?.tipo_usuario === 'medico',
      ehPaciente: usuario?.tipo_usuario === 'paciente',
      ehParceiro: usuario?.tipo_usuario === 'parceiro',
      entrar,
      trocarSenha,
      sair,
    }),
    [usuario, carregando, entrar, trocarSenha, sair],
  )

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const contexto = useContext(AuthContext)
  if (!contexto) throw new Error('useAuth precisa estar dentro de <AuthProvider>.')
  return contexto
}
