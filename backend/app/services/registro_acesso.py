"""Registro de acessos à anamnese para a trilha de auditoria."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import agora_utc
from app.models.acompanhamento import Acompanhamento
from app.models.registro_acesso import RegistroAcesso
from app.models.usuario import Usuario

ACOES = ("leitura", "escrita")

# Leituras iguais em sequência (ex.: auto-atualização da tela a cada 30s) viram
# uma só: dentro desta janela, a última leitura já prova o acesso. Escritas são
# sempre registradas, sem deduplicação.
JANELA_LEITURA = timedelta(minutes=5)


def registrar_acesso(sessao: Session, usuario: Usuario, acompanhamento: Acompanhamento, acao: str) -> None:
    """Grava quem acessou a anamnese e o que fez. Quem chama decide o commit."""
    if acao not in ACOES:
        raise ValueError(f"Ação inválida: {acao}")
    if acao == "leitura" and _leitura_recente(sessao, usuario.id, acompanhamento.id):
        return
    sessao.add(
        RegistroAcesso(
            usuario_id=usuario.id,
            tipo_usuario=usuario.tipo_usuario.value,
            acompanhamento_id=acompanhamento.id,
            acao=acao,
        )
    )


def _leitura_recente(sessao: Session, usuario_id: int, acompanhamento_id: int) -> bool:
    """Já existe leitura deste usuário neste acompanhamento na janela atual?"""
    limite = agora_utc() - JANELA_LEITURA
    anterior = sessao.scalar(
        select(RegistroAcesso.id)
        .where(
            RegistroAcesso.usuario_id == usuario_id,
            RegistroAcesso.acompanhamento_id == acompanhamento_id,
            RegistroAcesso.acao == "leitura",
            RegistroAcesso.ocorreu_em >= limite,
        )
        .limit(1)
    )
    return anterior is not None
