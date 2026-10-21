"""Registro de acessos à anamnese para a trilha de auditoria."""

from sqlalchemy.orm import Session

from app.models.acompanhamento import Acompanhamento
from app.models.registro_acesso import RegistroAcesso
from app.models.usuario import Usuario

ACOES = ("leitura", "escrita")


def registrar_acesso(sessao: Session, usuario: Usuario, acompanhamento: Acompanhamento, acao: str) -> None:
    """Grava quem acessou a anamnese e o que fez. Quem chama decide o commit."""
    if acao not in ACOES:
        raise ValueError(f"Ação inválida: {acao}")
    sessao.add(
        RegistroAcesso(
            usuario_id=usuario.id,
            tipo_usuario=usuario.tipo_usuario.value,
            acompanhamento_id=acompanhamento.id,
            acao=acao,
        )
    )
