import { Link } from 'react-router-dom'

import { EstadoVazio } from '../components/ui'

export default function NaoEncontrada() {
  return (
    <EstadoVazio>
      <h1>Página não encontrada</h1>
      <p>
        O endereço acessado não existe. <Link to="/painel">Voltar ao painel</Link>
      </p>
    </EstadoVazio>
  )
}
