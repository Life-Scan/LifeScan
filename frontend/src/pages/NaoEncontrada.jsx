import { House, SearchX } from 'lucide-react'
import { Link } from 'react-router-dom'

import { EstadoVazio, estilos as ui } from '../components/ui'

export default function NaoEncontrada() {
  return (
    <EstadoVazio
      icone={SearchX}
      titulo="Página não encontrada"
      tituloComo="h1"
      acao={
        <Link to="/painel" className={ui.botao}>
          <House size={16} aria-hidden="true" />
          Voltar ao painel
        </Link>
      }
    >
      O endereço acessado não existe. Confira o link ou volte ao painel.
    </EstadoVazio>
  )
}
