"""Contas de pacientes e parceiros, criadas e administradas pelo médico."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import exigir_tipo
from app.db.sessao import obter_sessao
from app.models.arquivo import Arquivo
from app.models.atribuicao import AtribuicaoParceiro
from app.models.documento import Documento
from app.models.ficha import FichaPaciente
from app.models.jornada import Jornada
from app.models.solicitacao import Solicitacao
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.auth import MensagemSaida
from app.schemas.usuario import ContaAtualizacao, ContaEntrada, ContaSaida
from app.schemas.paginacao import Pagina, Paginacao, paginar
from app.services.contas import enviar_acesso_da_conta
from app.services.email import ErroEnvioEmail

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
    try:
        enviar_acesso_da_conta(usuario)
    except ErroEnvioEmail as err:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Falha ao enviar email por SMTP: {err}") from err
    sessao.add(usuario)
    sessao.commit()
    return _montar_saidas(sessao, [usuario])[0]


@router.get("", response_model=Pagina[ContaSaida] | list[ContaSaida])
def listar_contas(
    tipo: TipoUsuario | None = Query(None, description="paciente ou parceiro"),
    ativo: bool | None = Query(None),
    paginacao: Paginacao = Depends(),
    sessao: Session = Depends(obter_sessao),
):
    consulta = select(Usuario).where(Usuario.tipo_usuario != TipoUsuario.medico)
    if tipo is not None:
        consulta = consulta.where(Usuario.tipo_usuario == tipo)
    if ativo is not None:
        consulta = consulta.where(Usuario.ativo == ativo)
    resultado = paginar(sessao, consulta.order_by(Usuario.nome, Usuario.id), paginacao)
    if isinstance(resultado, dict):
        resultado["itens"] = _montar_saidas(sessao, resultado["itens"])
        return resultado
    return _montar_saidas(sessao, resultado)


@router.patch("/{usuario_id}", response_model=ContaSaida)
def atualizar_conta(
    usuario_id: int,
    dados: ContaAtualizacao,
    sessao: Session = Depends(obter_sessao),
) -> ContaSaida:
    """Altera nome, email, profissão (parceiro) ou ativa/desativa a conta."""
    usuario = _obter_conta(sessao, usuario_id)
    if dados.email is not None:
        if sessao.scalar(select(Usuario.id).where(Usuario.email == dados.email, Usuario.id != usuario_id)):
            raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma conta com este email.")
        usuario.email = dados.email
    if dados.nome is not None:
        usuario.nome = dados.nome
    if dados.profissao is not None and usuario.tipo_usuario == TipoUsuario.parceiro:
        usuario.profissao = dados.profissao
    if dados.ativo is not None:
        usuario.ativo = dados.ativo
    try:
        sessao.commit()
    except IntegrityError:
        sessao.rollback()
        # Outra requisição pode ter usado o email entre a consulta e o commit.
        if dados.email is not None and sessao.scalar(
            select(Usuario.id).where(Usuario.email == dados.email, Usuario.id != usuario_id)
        ):
            raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma conta com este email.") from None
        raise
    return _montar_saidas(sessao, [usuario])[0]


@router.delete("/{usuario_id}", response_model=MensagemSaida)
def excluir_paciente(usuario_id: int, sessao: Session = Depends(obter_sessao)) -> MensagemSaida:
    """Exclusão definitiva de pacientes desativados sem histórico vinculado."""
    usuario = _obter_conta(sessao, usuario_id)
    if usuario.tipo_usuario != TipoUsuario.paciente:
        raise HTTPException(status.HTTP_409_CONFLICT, "Apenas pacientes podem ser excluídos por esta opção.")
    if usuario.ativo:
        raise HTTPException(status.HTTP_409_CONFLICT, "Desative o paciente antes de excluir a conta.")

    vinculos = (
        Jornada.paciente_id, Jornada.medico_id, FichaPaciente.paciente_id,
        Arquivo.enviado_por_id, Documento.enviado_por_id,
        Solicitacao.destinatario_id, AtribuicaoParceiro.parceiro_id,
    )
    mensagem_historico = "Este paciente possui jornada ou histórico vinculado e não pode ser excluído. Reative a conta para reutilizá-la."
    if any(sessao.scalar(select(coluna).where(coluna == usuario_id).limit(1)) is not None for coluna in vinculos):
        raise HTTPException(status.HTTP_409_CONFLICT, mensagem_historico)
    sessao.delete(usuario)
    try:
        sessao.commit()
    except IntegrityError as err:
        sessao.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, mensagem_historico) from err
    return MensagemSaida(mensagem="Paciente excluído definitivamente. O email está disponível para um novo cadastro.")


@router.post("/{usuario_id}/resend-access", response_model=MensagemSaida)
def reenviar_acesso(usuario_id: int, sessao: Session = Depends(obter_sessao)) -> MensagemSaida:
    """Gera uma nova senha provisória e reenvia os dados de acesso por email."""
    usuario = _obter_conta(sessao, usuario_id)
    if not usuario.ativo:
        raise HTTPException(status.HTTP_409_CONFLICT, "Reative a conta antes de reenviar o acesso.")
    try:
        enviar_acesso_da_conta(usuario)
    except ErroEnvioEmail as err:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Falha ao enviar email por SMTP: {err}") from err
    sessao.commit()
    return MensagemSaida(mensagem=f"Dados de acesso enviados para {usuario.email}.")
