import { estilos as ui } from './ui'

export default function Paginacao({ dados, aoMudar, carregando = false }) {
  if (!dados || dados.paginas <= 1) return null
  return (
    <nav aria-label="Paginação" className={ui.acoes} style={{ marginTop: '1rem', justifyContent: 'space-between' }}>
      <button type="button" className={ui.botaoSecundario} disabled={carregando || dados.pagina <= 1} onClick={() => aoMudar(dados.pagina - 1)}>Anterior</button>
      <span role="status" className={ui.ajuda}>Página {dados.pagina} de {dados.paginas} · {dados.total} registros</span>
      <button type="button" className={ui.botaoSecundario} disabled={carregando || dados.pagina >= dados.paginas} onClick={() => aoMudar(dados.pagina + 1)}>Próxima</button>
    </nav>
  )
}
