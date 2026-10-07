"""Contas de pacientes e parceiros, criadas e administradas pelo médico."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import exigir_tipo
from app.db.sessao import obter_sessao
from app.models.jornada import Jornada
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.auth import MensagemSaida
from app.schemas.usuario import ContaAtualizacao, ContaEntrada, ContaSaida
from app.services.contas import enviar_acesso_da_conta

router = APIRouter(
    prefix="/users",
    tags=["Contas"],
    dependencies=[Depends(exigir_tipo(TipoUsuario.medico))],
)


def _montar_saidas(sessao: Session, usuarios: list[Usuario]) -> list[ContaSaida]:
    ids = [usuario.id for usuario in usuarios]
    jornadas = dict(
        sessao.execute(select(Jornada.paciente_id, Jornada.id).where(Jornada.paciente_id.in_(ids))).all()
    )
    saidas = []
    for usuario in usuarios:
        saida = ContaSaida.model_validate(usuario)
        saida.jornada_id = jornadas.get(usuario.id)
        saidas.append(saida)
    return saidas


def _obter_conta(sessao: Session, usuario_id: int) -> Usuario:
    usuario = sessao.get(Usuario, usuario_id)
    # A conta do médico não é administrada por aqui
    if usuario is None or usuario.tipo_usuario == TipoUsuario.medico:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conta não encontrada.")
    return usuario


@router.post("", response_model=ContaSaida, status_code=status.HTTP_201_CREATED)
def criar_conta(dados: ContaEntrada, sessao: Session = Depends(obter_sessao)) -> ContaSaida:
    """Cria a conta de um paciente ou parceiro e envia os dados de acesso por email.

    A conta já pode ser usada pelo médico (abrir jornada, registrar consultas...)
    antes de a pessoa entrar pela primeira vez.
    """
    if sessao.scalar(select(Usuario.id).where(Usuario.email == dados.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma conta com este email.")

    usuario = Usuario(
        tipo_usuario=dados.tipo_usuario,
        nome=dados.nome,
        email=dados.email,
        profissao=dados.profissao,
    )
    enviar_acesso_da_conta(usuario)
    sessao.add(usuario)
    sessao.commit()
    return _montar_saidas(sessao, [usuario])[0]


@router.get("", response_model=list[ContaSaida])
def listar_contas(
    tipo: TipoUsuario | None = Query(None, description="paciente ou parceiro"),
    sessao: Session = Depends(obter_sessao),
) -> list[ContaSaida]:
    consulta = select(Usuario).where(Usuario.tipo_usuario != TipoUsuario.medico)
    if tipo is not None:
        consulta = consulta.where(Usuario.tipo_usuario == tipo)
    usuarios = list(sessao.scalars(consulta.order_by(Usuario.nome, Usuario.id)))
    return _montar_saidas(sessao, usuarios)


@router.patch("/{usuario_id}", response_model=ContaSaida)
def atualizar_conta(
    usuario_id: int,
    dados: ContaAtualizacao,
    sessao: Session = Depends(obter_sessao),
) -> ContaSaida:
    """Altera nome, profissão (parceiro) ou ativa/desativa a conta."""
    usuario = _obter_conta(sessao, usuario_id)
    if dados.nome is not None:
        usuario.nome = dados.nome
    if dados.profissao is not None and usuario.tipo_usuario == TipoUsuario.parceiro:
        usuario.profissao = dados.profissao
    if dados.ativo is not None:
        usuario.ativo = dados.ativo
    sessao.commit()
    return _montar_saidas(sessao, [usuario])[0]


@router.post("/{usuario_id}/resend-access", response_model=MensagemSaida)
def reenviar_acesso(usuario_id: int, sessao: Session = Depends(obter_sessao)) -> MensagemSaida:
    """Gera uma nova senha provisória e reenvia os dados de acesso por email."""
    usuario = _obter_conta(sessao, usuario_id)
    if not usuario.ativo:
        raise HTTPException(status.HTTP_409_CONFLICT, "Reative a conta antes de reenviar o acesso.")
    enviar_acesso_da_conta(usuario)
    sessao.commit()
    return MensagemSaida(mensagem=f"Dados de acesso enviados para {usuario.email}.")
