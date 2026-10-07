import { NotebookPen, Pencil } from 'lucide-react'
import { useState } from 'react'

import { mensagemDeErro } from '../../api/cliente'
import { salvarFicha } from '../../api/servicos'
import { Alerta, EstadoVazio, estilos as ui } from '../../components/ui'
import { ROTULOS_SEXO, formatarDataHora, formatarDataSemHora } from '../../utils/formatacao'
import estilos from './Jornada.module.css'

const CAMPOS_DE_TEXTO = [
  { campo: 'diagnosticos', rotulo: 'Diagnósticos e condições', exemplo: 'Ex.: Hipertensão estágio 1' },
  { campo: 'alergias', rotulo: 'Alergias', exemplo: 'Ex.: Dipirona' },
  { campo: 'medicamentos_em_uso', rotulo: 'Medicamentos em uso', exemplo: 'Ex.: Losartana 50 mg pela manhã' },
  { campo: 'restricoes', rotulo: 'Restrições', exemplo: 'Ex.: Evitar exercícios de alto impacto' },
  { campo: 'objetivos', rotulo: 'Objetivos do tratamento', exemplo: 'Ex.: Reduzir a pressão e perder 8 kg' },
  { campo: 'observacoes', rotulo: 'Observações', exemplo: '' },
]

export default function AbaFicha({ ficha, jornada, ehMedico, ehParceiro, atualizar }) {
  const [editando, setEditando] = useState(false)

  return (
    <div className={estilos.pilha}>
      <div className={ui.cartaoCabecalho} style={{ marginBottom: 0 }}>
        <div>
          <h2>Ficha de {ficha.paciente.nome}</h2>
          {ficha.atualizado_em && <p className={ui.ajuda}>Atualizada em {formatarDataHora(ficha.atualizado_em)}</p>}
        </div>
        {ehMedico && !editando && (
          <button type="button" className={ui.botao} onClick={() => setEditando(true)}>
            <Pencil size={15} aria-hidden="true" />
            {ficha.preenchida ? 'Editar ficha' : 'Preencher ficha'}
          </button>
        )}
      </div>

      {editando ? (
        <FormularioFicha
          ficha={ficha}
          jornadaId={jornada.id}
          aoConcluir={async () => {
            setEditando(false)
            await atualizar()
          }}
          aoCancelar={() => setEditando(false)}
        />
      ) : ficha.preenchida ? (
        <VisualizacaoFicha ficha={ficha} />
      ) : (
        <EstadoVazio icone={NotebookPen}>
          {ehMedico
            ? 'A ficha ainda não foi preenchida. Ela resume o paciente para você e para os parceiros atribuídos.'
            : 'O médico ainda não preencheu esta ficha.'}
        </EstadoVazio>
      )}

      {ehMedico && !editando && (
        <p className={ui.ajuda}>
          Os parceiros atribuídos a esta jornada veem esta ficha, mas não veem consultas, prescrições nem exames.
        </p>
      )}
      {ehParceiro && (
        <p className={ui.ajuda}>Estas informações são mantidas pelo médico responsável pelo paciente.</p>
      )}
    </div>
  )
}

function VisualizacaoFicha({ ficha }) {
  const basicos = [
    { rotulo: 'Idade', valor: ficha.idade != null ? `${ficha.idade} anos` : null },
    { rotulo: 'Nascimento', valor: formatarDataSemHora(ficha.data_nascimento) || null },
    { rotulo: 'Sexo', valor: ROTULOS_SEXO[ficha.sexo] || null },
    { rotulo: 'Altura', valor: ficha.altura_cm ? `${ficha.altura_cm} cm` : null },
    { rotulo: 'Peso', valor: ficha.peso_kg ? `${String(ficha.peso_kg).replace('.', ',')} kg` : null },
  ]

  return (
    <>
      <dl className={estilos.fichaBasicos}>
        {basicos.map(({ rotulo, valor }) => (
          <div key={rotulo} className={estilos.fichaItem}>
            <dt>{rotulo}</dt>
            <dd>{valor || <span className={ui.suave}>Não informado</span>}</dd>
          </div>
        ))}
      </dl>
      <dl className={estilos.fichaTextos}>
        {CAMPOS_DE_TEXTO.filter(({ campo }) => ficha[campo]).map(({ campo, rotulo }) => (
          <div key={campo} className={estilos.fichaItem}>
            <dt>{rotulo}</dt>
            <dd className={estilos.texto}>{ficha[campo]}</dd>
          </div>
        ))}
      </dl>
    </>
  )
}

function FormularioFicha({ ficha, jornadaId, aoConcluir, aoCancelar }) {
  const [formulario, setFormulario] = useState(() => ({
    data_nascimento: ficha.data_nascimento || '',
    sexo: ficha.sexo || '',
    altura_cm: ficha.altura_cm ?? '',
    peso_kg: ficha.peso_kg ?? '',
    ...Object.fromEntries(CAMPOS_DE_TEXTO.map(({ campo }) => [campo, ficha[campo] || ''])),
  }))
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  const alterar = (campo) => (evento) => setFormulario((atual) => ({ ...atual, [campo]: evento.target.value }))

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      await salvarFicha(jornadaId, {
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
          <label htmlFor="ficha-nascimento">Data de nascimento</label>
          <input
            id="ficha-nascimento"
            type="date"
            value={formulario.data_nascimento}
            max={new Date().toISOString().slice(0, 10)}
            onChange={alterar('data_nascimento')}
          />
        </div>
        <div>
          <label htmlFor="ficha-sexo">Sexo</label>
          <select id="ficha-sexo" value={formulario.sexo} onChange={alterar('sexo')}>
            <option value="">Não informado</option>
            {Object.entries(ROTULOS_SEXO).map(([valor, rotulo]) => (
              <option key={valor} value={valor}>
                {rotulo}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="ficha-altura">Altura (cm)</label>
          <input id="ficha-altura" type="number" min="30" max="260" value={formulario.altura_cm} onChange={alterar('altura_cm')} />
        </div>
        <div>
          <label htmlFor="ficha-peso">Peso (kg)</label>
          <input id="ficha-peso" type="number" min="1" max="500" step="0.1" value={formulario.peso_kg} onChange={alterar('peso_kg')} />
        </div>
      </div>

      {CAMPOS_DE_TEXTO.map(({ campo, rotulo, exemplo }) => (
        <div key={campo}>
          <label htmlFor={`ficha-${campo}`}>{rotulo}</label>
          <textarea
            id={`ficha-${campo}`}
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
          {enviando ? 'Salvando…' : 'Salvar ficha'}
        </button>
        <button type="button" className={ui.botaoSecundario} onClick={aoCancelar} disabled={enviando}>
          Cancelar
        </button>
      </div>
    </form>
  )
}
