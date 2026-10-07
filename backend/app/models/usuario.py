import enum
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, DataHora, agora_utc, coluna_enum


class TipoUsuario(str, enum.Enum):
    medico = "medico"
    paciente = "paciente"
    parceiro = "parceiro"


# O sistema tem um único médico, e a profissão dele é fixa
PROFISSAO_MEDICO = "Médico"


class Usuario(Base):
    """Médico, paciente ou parceiro. Não existe cadastro público: o médico é criado
    por script e é ele quem cria as contas de pacientes e parceiros."""

    __tablename__ = "usuarios"
    __table_args__ = (
        # A profissão só pode ficar vazia para pacientes
        CheckConstraint(
            "tipo_usuario = 'paciente' OR profissao IS NOT NULL",
            name="ck_usuarios_profissao_obrigatoria",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo_usuario: Mapped[TipoUsuario] = mapped_column(coluna_enum(TipoUsuario, "tipo_usuario"))
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    profissao: Mapped[str | None] = mapped_column(String(100))
    # Vazio enquanto a pessoa não definiu a própria senha (só tem a provisória)
    senha_hash: Mapped[str | None] = mapped_column(String(255))
    # Senha provisória enviada por email: vale por tempo limitado e, enquanto existir,
    # a senha definitiva (se houver) continua funcionando
    senha_provisoria_hash: Mapped[str | None] = mapped_column(String(255))
    senha_provisoria_expira_em: Mapped[datetime | None] = mapped_column(DataHora)
    # Ligado quando o último login foi feito com a senha provisória
    deve_trocar_senha: Mapped[bool] = mapped_column(Boolean, default=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    ultimo_login_em: Mapped[datetime | None] = mapped_column(DataHora)
    criado_em: Mapped[datetime] = mapped_column(DataHora, default=agora_utc)

    @property
    def primeiro_acesso_pendente(self) -> bool:
        """A pessoa ainda não entrou e definiu a própria senha."""
        return self.senha_hash is None
