/** Prévia de documentos de texto com formatação, chamada sob demanda (imports preguiçosos).
 *
 * PDF: a primeira página vira uma imagem (canvas). DOCX: o texto inicial.
 * Ambas as bibliotecas só entram no bundle quando um documento desses aparece.
 */

const ALTURA_DE_MINIATURA = 160 // 2x o quadro 80px, para ficar nítido em telas retina

export async function urlDaPrimeiraPaginaDePdf(arquivo) {
  const [pdfjs, { default: urlDoWorker }] = await Promise.all([
    import('pdfjs-dist'),
    import('pdfjs-dist/build/pdf.worker.min.mjs?url'),
  ])
  pdfjs.GlobalWorkerOptions.workerSrc = urlDoWorker
  // No pdfjs v6 quem encerra é a tarefa de carregamento, não o documento
  const tarefa = pdfjs.getDocument({ data: await arquivo.arrayBuffer() })
  const documento = await tarefa.promise
  try {
    const pagina = await documento.getPage(1)
    const base = pagina.getViewport({ scale: 1 })
    const viewport = pagina.getViewport({ scale: ALTURA_DE_MINIATURA / base.height })
    const tela = document.createElement('canvas')
    tela.width = viewport.width
    tela.height = viewport.height
    const contexto = tela.getContext('2d')
    await pagina.render({ canvasContext: contexto, viewport }).promise
    return tela.toDataURL('image/png')
  } finally {
    tarefa.destroy()
  }
}

export async function textoDeDocx(arquivo) {
  const modulo = await import('mammoth/mammoth.browser.min.js')
  const mammoth = modulo.default ?? modulo
  const resposta = await mammoth.extractRawText({ arrayBuffer: await arquivo.arrayBuffer() })
  return resposta.value
}
