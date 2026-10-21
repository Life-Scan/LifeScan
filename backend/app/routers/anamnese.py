from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import (
    obter_acompanhamento_com_acesso,
    obter_acompanhamento_com_acesso_de_parceiro,
    obter_acompanhamento_do_medico,
    obter_usuario_atual,
)
from app.db.base import agora_utc
from app.db.sessao import obter_sessao
from app.models.anamnese import Anamnese
from app.models.acompanhamento import Acompanhamento
from app.models.consentimento import Consentimento
from app.models.registro_acesso import RegistroAcesso
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.anamnese import (
    AcessoAnamneseSaida,
    AnamneseEntrada,
    AnamneseSaida,
    ConsentimentoSaida,
    DadosBasicosAnamneseEntrada,
    PortabilidadeAnamneseSaida,
)
from app.schemas.usuario import UsuarioResumo
from app.services.registro_acesso import registrar_acesso

router = APIRouter(prefix="/follow-ups/{acompanhamento_id}/anamnesis", tags=["Anamnese do paciente"])

CAMPOS_DE_TEXTO = (
    "diagnosticos",
    "alergias",
    "medicamentos_em_uso",
    "restricoes",
    "objetivos",
    "observacoes",
)
CAMPOS = ("data_nascimento", "sexo", "altura_cm", "peso_kg", *CAMPOS_DE_TEXTO)
# O que o titular pode corrigir (nascimento, sexo, altura e peso)
CAMPOS_BASICOS = ("data_nascimento", "sexo", "altura_cm", "peso_kg")


def _calcular_idade(nascimento: date | None) -> int | None:
    if nascimento is None:
        return None
    hoje = date.today()
    ainda_nao_fez_aniversario = (hoje.month, hoje.day) < (nascimento.month, nascimento.day)
    return hoje.year - nascimento.year - ainda_nao_fez_aniversario


def _montar_saida(
    acompanhamento: Acompanhamento, anamnese: Anamnese | None, para_parceiro: bool = False
) -> AnamneseSaida:
    paciente = UsuarioResumo.model_validate(acompanhamento.paciente)
    if anamnese is None:
        return AnamneseSaida(paciente=paciente, preenchida=False)
    saida = AnamneseSaida(
        paciente=paciente,
        preenchida=True,
        idade=_calcular_idade(anamnese.data_nascimento),
        atualizado_em=anamnese.atualizado_em,
        **{campo: getattr(anamnese, campo) for campo in CAMPOS},
    )
    if para_parceiro:
        # Minimização (LGPD, art. 6º, III): o parceiro precisa da idade para
        # contextualizar o cuidado, não da data completa de nascimento do titular
        saida.data_nascimento = None
    return saida


def _obter_anamnese(sessao: Session, acompanhamento: Acompanhamento) -> Anamnese | None:
    return sessao.scalar(select(Anamnese).where(Anamnese.paciente_id == acompanhamento.paciente_id))


@router.get("", response_model=AnamneseSaida)
def obter_anamnese(
    acompanhamento: Acompanhamento = Depends(obter_acompanhamento_com_acesso_de_parceiro),
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> AnamneseSaida:
    """Anamnese do paciente: visível ao médico, ao próprio paciente e aos parceiros atribuídos."""
    saida = _montar_saida(
        acompanhamento, _obter_anamnese(sessao, acompanhamento), para_parceiro=usuario.tipo_usuario is TipoUsuario.parceiro
    )
    registrar_acesso(sessao, usuario, acompanhamento, "leitura")
    sessao.commit()
    return saida


@router.get("/acessos", response_model=list[AcessoAnamneseSaida])
def listar_acessos_da_anamnese(
    acompanhamento: Acompanhamento = Depends(obter_acompanhamento_com_acesso),
    sessao: Session = Depends(obter_sessao),
) -> list[AcessoAnamneseSaida]:
    """Trilha de quem leu ou alterou a anamnese (LGPD, art. 18, V).

    Sempre pseudônima: devolve apenas o tipo de usuário (médico, paciente ou parceiro),
    sem nomes. Mais recentes primeiro; o parceiro não vê a trilha.
    """
    registros = sessao.scalars(
        select(RegistroAcesso)
        .where(RegistroAcesso.acompanhamento_id == acompanhamento.id)
        .order_by(RegistroAcesso.ocorreu_em.desc(), RegistroAcesso.id.desc())
        .limit(30)
    ).all()
    return [
        AcessoAnamneseSaida(tipo_usuario=TipoUsuario(r.tipo_usuario), acao=r.acao, ocorreu_em=r.ocorreu_em)
        for r in registros
    ]


@router.get("/portabilidade")
def exportar_anamnese(
    acompanhamento: Acompanhamento = Depends(obter_acompanhamento_com_acesso),
    sessao: Session = Depends(obter_sessao),
) -> Response:
    """Portabilidade da anamnese para o titular ou para o médico dele (LGPD, art. 18, V).

    Devolve tudo o que o sistema guarda a respeito: a anamnese, os consentimentos
    registrados e a trilha de acessos, em JSON baixável. O parceiro não exporta.
    """
    anamnese = _obter_anamnese(sessao, acompanhamento)
    consentimentos = sessao.scalars(
        select(Consentimento)
        .where(Consentimento.usuario_id == acompanhamento.paciente_id)
        .order_by(Consentimento.concedido_em.desc())
    ).all()
    acessos = sessao.scalars(
        select(RegistroAcesso)
        .where(RegistroAcesso.acompanhamento_id == acompanhamento.id)
        .order_by(RegistroAcesso.ocorreu_em.desc(), RegistroAcesso.id.desc())
        .limit(30)
    ).all()

    exportacao = PortabilidadeAnamneseSaida(
        gerado_em=agora_utc(),
        paciente=UsuarioResumo.model_validate(acompanhamento.paciente),
        anamnese=_montar_saida(acompanhamento, anamnese),
        consentimentos=[
            ConsentimentoSaida.model_validate(c, from_attributes=True) for c in consentimentos
        ],
        acessos=[
            AcessoAnamneseSaida(tipo_usuario=TipoUsuario(r.tipo_usuario), acao=r.acao, ocorreu_em=r.ocorreu_em)
            for r in acessos
        ],
    )
    conteudo = exportacao.model_dump_json(indent=2, exclude_none=True)
    return Response(
        content=conteudo,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="anamnese-{acompanhamento.id}.json"'},
    )


@router.patch("/dados-basicos", response_model=AnamneseSaida)
def corrigir_dados_basicos(
    dados: DadosBasicosAnamneseEntrada,
    acompanhamento: Acompanhamento = Depends(obter_acompanhamento_com_acesso),
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> AnamneseSaida:
    """Correção dos dados básicos pelo próprio paciente (LGPD, art. 18, III).

    Grava o bloco inteiro (nascimento, sexo, altura e peso) a partir do formulário:
    o que vier vazio fica em branco. O conteúdo clínico não é tocado. Continua
    disponível ao médico, que pode corrigir por quem é atendido.
    """
    anamnese = _obter_anamnese(sessao, acompanhamento)
    if anamnese is None:
        anamnese = Anamnese(paciente_id=acompanhamento.paciente_id)
        sessao.add(anamnese)

    for campo in CAMPOS_BASICOS:
        setattr(anamnese, campo, getattr(dados, campo))
    registrar_acesso(sessao, usuario, acompanhamento, "escrita")
    sessao.commit()
    return _montar_saida(acompanhamento, anamnese)


@router.put("", response_model=AnamneseSaida)
def salvar_anamnese(
    dados: AnamneseEntrada,
    acompanhamento: Acompanhamento = Depends(obter_acompanhamento_do_medico),
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> AnamneseSaida:
    """O médico cria ou substitui a anamnese inteira.

    Continua editável com o acompanhamento encerrado: a anamnese descreve o paciente, não o tratamento.
    """
    anamnese = _obter_anamnese(sessao, acompanhamento)
    if anamnese is None:
        anamnese = Anamnese(paciente_id=acompanhamento.paciente_id)
        sessao.add(anamnese)

    for campo in CAMPOS:
        valor = getattr(dados, campo)
        if campo in CAMPOS_DE_TEXTO:
            valor = valor or None
        setattr(anamnese, campo, valor)
    registrar_acesso(sessao, usuario, acompanhamento, "escrita")
    sessao.commit()
    return _montar_saida(acompanhamento, anamnese)
