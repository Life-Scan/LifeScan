from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, DataHora, agora_utc

# Versão do termo de consentimento que a pessoa aceita ao definir a própria senha.
# A cada mudança de conteúdo do termo, suba a versão: aí os consentimentos antigos
# continuam provando qual texto foi aceito, e novos acessos registram a versão nova.
VERSAO_TERMO = "2026-10-v1"

FINALIDADE = "anamnese e acompanhamento clínico"


class Consentimento(Base):
    """Registro de aceite do termo de tratamento de dados (LGPD, art. 11).

    Uma linha por aceite, guardando também o IP de origem: junto com a versão do
    termo, permite provar depois qual texto e em que contexto o titular consentiu.
    """

    __tablename__ = "consentimentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    finalidade: Mapped[str] = mapped_column(String(120), default=FINALIDADE)
    versao_termo: Mapped[str] = mapped_column(String(20), default=VERSAO_TERMO)
    # Nulo enquanto o consentimento vale; preenchido quando o titular o revoga
    revogado_em: Mapped[datetime | None] = mapped_column(DataHora)
    ip_aceite: Mapped[str | None] = mapped_column(String(45))
    concedido_em: Mapped[datetime] = mapped_column(DataHora, default=agora_utc)
