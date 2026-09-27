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

  const iniciarSessao = useCallback(({ token_acesso: token, usuario: dadosUsuario }) => {
    localStorage.setItem(CHAVE_TOKEN, token)
    setUsuario(dadosUsuario)
    return dadosUsuario
  }, [])

  const entrar = useCallback(
    async (email, senha) => iniciarSessao(await servicos.entrar(email, senha)),
    [iniciarSessao],
  )

  const cadastrar = useCallback(
    async (cadastro) => iniciarSessao(await servicos.cadastrar(cadastro)),
    [iniciarSessao],
  )

  const sair = useCallback(() => {
    localStorage.removeItem(CHAVE_TOKEN)
    setUsuario(null)
  }, [])

  const valor = useMemo(
    () => ({
      usuario,
      carregando,
      ehMedico: usuario?.papel === 'medico',
      ehPaciente: usuario?.papel === 'paciente',
      entrar,
      cadastrar,
      sair,
    }),
    [usuario, carregando, entrar, cadastrar, sair],
  )

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const contexto = useContext(AuthContext)
  if (!contexto) throw new Error('useAuth precisa estar dentro de <AuthProvider>.')
  return contexto
}
