/**
 * Moldura das telas de acesso fora do layout (esqueci a senha, definir senha): marca, frase de
 * apoio e o cartão com o título. O login tem visual próprio e não usa esta moldura.
 */
import { estilos as ui } from './ui'

export default function TelaAcesso({ slogan, titulo, rodape, children }) {
  return (
    <div className="grid min-h-screen place-items-center px-4 py-6 bg-[linear-gradient(160deg,var(--cor-primaria-clara),var(--cor-fundo)_55%)]">
      <div className="w-full max-w-[420px]">
        <div className="mb-[0.4rem] flex items-center justify-center gap-[0.6rem] text-[1.6rem] font-bold">
          <img src="/favicon.svg" alt="" width="36" height="36" />
          LifeScan
        </div>
        <p className="mb-6 text-center text-texto-suave">{slogan}</p>

        <div className={ui.cartao}>
          <h1 className="mb-[1.1rem]">{titulo}</h1>
          {children}
          {rodape && <p className="mt-[1.1rem] text-center text-[0.92rem] text-texto-suave">{rodape}</p>}
        </div>
      </div>
    </div>
  )
}
