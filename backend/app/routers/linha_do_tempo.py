from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import obter_acompanhamento_com_acesso
from app.db.sessao import obter_sessao
from app.models.acompanhamento import Acompanhamento
from app.schemas.linha_do_tempo import EventoLinhaDoTempo, TipoEvento
from app.services.linha_do_tempo import montar_linha_do_tempo

router = APIRouter(tags=["Linha do tempo"])


def _interpretar_tipos(texto: str | None) -> set[TipoEvento] | None:
    if not texto:
        return None
    valores = {parte.strip() for parte in texto.split(",") if parte.strip()}
    validos = {tipo.value for tipo in TipoEvento}
    invalidos = sorted(valores - validos)
    if invalidos:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Tipo inválido: {', '.join(invalidos)}. Use: {', '.join(sorted(validos))}.",
        )
    return {TipoEvento(valor) for valor in valores}


@router.get("/follow-ups/{acompanhamento_id}/timeline", response_model=list[EventoLinhaDoTempo])
def obter_linha_do_tempo(
    tipos: str | None = Query(
        None,
        description="Filtro opcional, separado por vírgula: consulta, documento, solicitacao",
    ),
    acompanhamento: Acompanhamento = Depends(obter_acompanhamento_com_acesso),
    sessao: Session = Depends(obter_sessao),
) -> list[EventoLinhaDoTempo]:
    """Linha do tempo do acompanhamento em ordem cronológica."""
    return montar_linha_do_tempo(sessao, acompanhamento, _interpretar_tipos(tipos))
