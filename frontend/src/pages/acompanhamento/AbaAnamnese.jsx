import { NotebookPen, Pencil } from 'lucide-react'
import { useEffect, useState } from 'react'

import { mensagemDeErro } from '../../api/cliente'
import { acessosAnamnese, salvarAnamnese } from '../../api/servicos'
import { Alerta, EstadoVazio, estilos as ui } from '../../components/ui'
import { ROTULOS_SEXO, formatarDataHora, formatarDataSemHora } from '../../utils/formatacao'
import estilos from './Acompanhamento.module.css'

const CAMPOS_DE_TEXTO = [
  { campo: 'diagnosticos', rotulo: 'Diagnósticos e condições', exemplo: 'Ex.: Hipertensão estágio 1' },
  { campo: 'alergias', rotulo: 'Alergias', exemplo: 'Ex.: Dipirona' },
  { campo: 'medicamentos_em_uso', rotulo: 'Medicamentos em uso', exemplo: 'Ex.: Losartana 50 mg pela manhã' },
  { campo: 'restricoes', rotulo: 'Restrições', exemplo: 'Ex.: Evitar exercícios de alto impacto' },
  { campo: 'objetivos', rotulo: 'Objetivos do tratamento', exemplo: 'Ex.: Reduzir a pressão e perder 8 kg' },
  { campo: 'observacoes', rotulo: 'Observações', exemplo: '' },
]

export default function AbaAnamnese({ anamnese, acompanhamento, ehMedico, ehParceiro, atualizar }) {
  const [editando, setEditando] = useState(false)
  const [acessos, setAcessos] = useState([])

  // Trilha de auditoria (LGPD): o médico e o paciente veem quem acessou a anamnese
  const podeVerTrilha = !ehParceiro
  useEffect(() => {
    if (!podeVerTrilha) return
    acessosAnamnese(acompanhamento.id).then(setAcessos).catch(() => setAcessos([]))
  }, [podeVerTrilha, acompanhamento.id, anamnese.atualizado_em])

  return (
    <div className={estilos.pilha}>
      <div className={ui.cartaoCabecalho} style={{ marginBottom: 0 }}>
        <div>
          <h2>Anamnese de {anamnese.paciente.nome}</h2>
          {anamnese.atualizado_em && <p className={ui.ajuda}>Atualizada em {formatarDataHora(anamnese.atualizado_em)}</p>}
        </div>
        {ehMedico && !editando && (
          <button type="button" className={ui.botao} onClick={() => setEditando(true)}>
            <Pencil size={15} aria-hidden="true" />
            {anamnese.preenchida ? 'Editar anamnese' : 'Preencher anamnese'}
          </button>
        )}
      </div>

      {editando ? (
        <FormularioAnamnese
          anamnese={anamnese}
          acompanhamentoId={acompanhamento.id}
          aoConcluir={async () => {
            setEditando(false)
            await atualizar()
          }}
          aoCancelar={() => setEditando(false)}
        />
      ) : anamnese.preenchida ? (
        <VisualizacaoAnamnese anamnese={anamnese} />
      ) : (
        <EstadoVazio icone={NotebookPen}>
          {ehMedico
            ? 'A anamnese ainda não foi preenchida. Ela resume o paciente para você e para os parceiros atribuídos.'
            : 'O médico ainda não preencheu esta anamnese.'}
        </EstadoVazio>
      )}

      {ehMedico && !editando && (
        <p className={ui.ajuda}>
          Os parceiros atribuídos a este acompanhamento veem esta anamnese, mas não veem consultas, prescrições nem exames.
        </p>
      )}
      {ehParceiro && (
        <p className={ui.ajuda}>Estas informações são mantidas pelo médico responsável pelo paciente.</p>
      )}
      {podeVerTrilha && acessos.length > 0 && (
        <TrilhaDeAcessos acessos={acessos} />
      )}
    </div>
  )
}

const NOMES_DE_PAPEL = { medico: 'Médico', paciente: 'Paciente', parceiro: 'Parceiro' }
const NOMES_DE_ACAO = { leitura: 'leu', escrita: 'alterou' }

function TrilhaDeAcessos({ acessos }) {
  return (
    <p className={ui.ajuda}>
      Registros de acesso (LGPD):{' '}
      {acessos
        .slice(0, 5)
        .map((acesso) => (
          `${NOMES_DE_PAPEL[acesso.tipo_usuario] || acesso.tipo_usuario} ${NOMES_DE_ACAO[acesso.acao] || acesso.acao} em ${formatarDataHora(acesso.ocorreu_em)}`
        ))
        .join(' · ')}
      {acessos.length > 5 && ' · …'}
    </p>
  )
}

function VisualizacaoAnamnese({ anamnese }) {
  const basicos = [
    { rotulo: 'Idade', valor: anamnese.idade != null ? `${anamnese.idade} anos` : null },
    { rotulo: 'Nascimento', valor: formatarDataSemHora(anamnese.data_nascimento) || null },
    { rotulo: 'Sexo', valor: ROTULOS_SEXO[anamnese.sexo] || null },
    { rotulo: 'Altura', valor: anamnese.altura_cm ? `${anamnese.altura_cm} cm` : null },
    { rotulo: 'Peso', valor: anamnese.peso_kg ? `${String(anamnese.peso_kg).replace('.', ',')} kg` : null },
  ]

  return (
    <>
      <dl className={estilos.anamneseBasicos}>
        {basicos.map(({ rotulo, valor }) => (
          <div key={rotulo} className={estilos.anamneseItem}>
            <dt>{rotulo}</dt>
            <dd>{valor || <span className={ui.suave}>Não informado</span>}</dd>
          </div>
        ))}
      </dl>
      <dl className={estilos.anamneseTextos}>
        {CAMPOS_DE_TEXTO.filter(({ campo }) => anamnese[campo]).map(({ campo, rotulo }) => (
          <div key={campo} className={estilos.anamneseItem}>
            <dt>{rotulo}</dt>
            <dd className={estilos.texto}>{anamnese[campo]}</dd>
          </div>
        ))}
      </dl>
    </>
  )
}

function FormularioAnamnese({ anamnese, acompanhamentoId, aoConcluir, aoCancelar }) {
  const [formulario, setFormulario] = useState(() => ({
    data_nascimento: anamnese.data_nascimento || '',
    sexo: anamnese.sexo || '',
    altura_cm: anamnese.altura_cm ?? '',
    peso_kg: anamnese.peso_kg ?? '',
    ...Object.fromEntries(CAMPOS_DE_TEXTO.map(({ campo }) => [campo, anamnese[campo] || ''])),
  }))
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  const alterar = (campo) => (evento) => setFormulario((atual) => ({ ...atual, [campo]: evento.target.value }))

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      await salvarAnamnese(acompanhamentoId, {
        data_nascimento: formulario.data_nascimento || null,
        sexo: formulario.sexo || null,
        altura_cm: formulario.altura_cm === '' ? null : Number(formulario.altura_cm),
        peso_kg: formulario.peso_kg === '' ? null : Number(formulario.peso_kg),
        ...Object.fromEntries(CAMPOS_DE_TEXTO.map(({ campo }) => [campo, formulario[campo].trim() || null])),
      })
      await aoConcluir()
    } catch (erroEnvio) {
      setErro(mensagemDeErro(erroEnvio))
      setEnviando(false)
    }
  }

  return (
    <form className={`${ui.formulario} ${estilos.formularioDestaque}`} onSubmit={aoEnviar}>
      <Alerta tipo="erro">{erro}</Alerta>
      <div className={ui.linhaCampos}>
        <div>
          <label htmlFor="anamnese-nascimento">Data de nascimento</label>
          <input
            id="anamnese-nascimento"
            type="date"
            value={formulario.data_nascimento}
            max={new Date().toISOString().slice(0, 10)}
            onChange={alterar('data_nascimento')}
          />
        </div>
        <div>
          <label htmlFor="anamnese-sexo">Sexo</label>
          <select id="anamnese-sexo" value={formulario.sexo} onChange={alterar('sexo')}>
            <option value="">Não informado</option>
            {Object.entries(ROTULOS_SEXO).map(([valor, rotulo]) => (
              <option key={valor} value={valor}>
                {rotulo}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="anamnese-altura">Altura (cm)</label>
          <input id="anamnese-altura" type="number" min="30" max="260" value={formulario.altura_cm} onChange={alterar('altura_cm')} />
        </div>
        <div>
          <label htmlFor="anamnese-peso">Peso (kg)</label>
          <input id="anamnese-peso" type="number" min="1" max="500" step="0.1" value={formulario.peso_kg} onChange={alterar('peso_kg')} />
        </div>
      </div>

      {CAMPOS_DE_TEXTO.map(({ campo, rotulo, exemplo }) => (
        <div key={campo}>
          <label htmlFor={`anamnese-${campo}`}>{rotulo}</label>
          <textarea
            id={`anamnese-${campo}`}
            rows={2}
            value={formulario[campo]}
            onChange={alterar(campo)}
            placeholder={exemplo}
          />
        </div>
      ))}

      <p className={ui.ajuda}>Todos os campos são opcionais. Deixe em branco o que não se aplica.</p>
      <div className={ui.acoes}>
        <button type="submit" className={ui.botao} disabled={enviando}>
          {enviando ? 'Salvando…' : 'Salvar anamnese'}
        </button>
        <button type="button" className={ui.botaoSecundario} onClick={aoCancelar} disabled={enviando}>
          Cancelar
        </button>
      </div>
    </form>
  )
}
