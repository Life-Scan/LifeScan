"""Estado do consentimento LGPD do titular (art. 8º, §5º e art. 11)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.consentimento import Consentimento


def tratamento_bloqueado_por_revogacao(sessao: Session, usuario_id: int) -> bool:
    """Verdadeiro quando o registro de consentimento existe e nenhum aceite está vigente.

    Contas que nunca aceitaram o termo (paciente criado e sem primeiro acesso) não
    bloqueiam: o tratamento segue sob tutela da saúde (art. 11, II, "f") e o aceite
    chega no momento em que o titular assume a conta. Revogado o consentimento, novas
    anotações clínicas ficam bloqueadas até um novo aceite.
    """
    tem_registro = (
        sessao.scalar(
            select(Consentimento.id).where(Consentimento.usuario_id == usuario_id).limit(1)
        )
        is not None
    )
    if not tem_registro:
        return False
    tem_vigente = (
        sessao.scalar(
            select(Consentimento.id)
            .where(Consentimento.usuario_id == usuario_id, Consentimento.revogado_em.is_(None))
            .limit(1)
        )
        is not None
    )
    return not tem_vigente
