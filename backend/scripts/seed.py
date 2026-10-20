"""Cria dados de exemplo: médico, paciente, parceiro e uma jornada com histórico.

Uso (na pasta backend, com o venv ativo e o banco migrado):
    python -m scripts.seed

Pode ser executado mais de uma vez: se o paciente de exemplo já existir, nada é feito.
Se já houver um médico (criado com scripts.criar_medico), ele é reaproveitado.
"""

import uuid
from datetime import date, timedelta

from sqlalchemy import select

from app.core.config import obter_configuracoes
from app.core.seguranca import gerar_hash_senha
from app.db.base import agora_utc
from app.db.sessao import SessaoLocal
from app.models import (
    Arquivo,
    AtribuicaoParceiro,
    CategoriaDocumento,
    Consulta,
    Documento,
    FichaPaciente,
    Jornada,
    PassoJornada,
    Prescricao,
    Sexo,
    Solicitacao,
    TipoConsulta,
    TipoSolicitacao,
    TipoUsuario,
    Usuario,
)
from app.models.usuario import PROFISSAO_MEDICO

SENHA_EXEMPLO = "lifescan123"
EMAIL_MEDICO = "medico@lifescan.com"
EMAIL_PACIENTE = "paciente@lifescan.com"
EMAIL_PARCEIRO = "parceiro@lifescan.com"


def _gravar_arquivo_texto(jornada_id: int, usuario_id: int, nome: str, conteudo: str) -> Arquivo:
    config = obter_configuracoes()
    config.pasta_uploads.mkdir(parents=True, exist_ok=True)
    nome_armazenado = f"{uuid.uuid4().hex}.txt"
    dados = conteudo.encode("utf-8")
    (config.pasta_uploads / nome_armazenado).write_bytes(dados)
    return Arquivo(
        jornada_id=jornada_id,
        nome_original=nome,
        nome_armazenado=nome_armazenado,
        tipo_mime="text/plain",
        tamanho_bytes=len(dados),
        enviado_por_id=usuario_id,
    )


def _complementar_ficha_e_parceiro(sessao) -> list[str]:
    """Garante a ficha do paciente de exemplo e o parceiro atribuído à jornada dele.

    Roda também quando os dados de exemplo já existiam, para bancos criados antes
    de a ficha e os parceiros existirem.
    """
    paciente = sessao.scalar(select(Usuario).where(Usuario.email == EMAIL_PACIENTE))
    parceiro = sessao.scalar(select(Usuario).where(Usuario.email == EMAIL_PARCEIRO))
    jornada = sessao.scalar(select(Jornada).where(Jornada.paciente_id == paciente.id))
    criados = []

    if not sessao.scalar(select(FichaPaciente.id).where(FichaPaciente.paciente_id == paciente.id)):
        sessao.add(
            FichaPaciente(
                paciente_id=paciente.id,
                data_nascimento=date(1978, 3, 14),
                sexo=Sexo.masculino,
                altura_cm=172,
                peso_kg=84.5,
                diagnosticos="Hipertensão arterial estágio 1",
                alergias="Dipirona",
                medicamentos_em_uso="Losartana 50 mg, 1 comprimido pela manhã",
                restricoes="Reduzir o sal. Evitar exercícios de alta intensidade até nova avaliação.",
                objetivos="Manter a pressão abaixo de 13x8 e perder 8 kg em 6 meses.",
            )
        )
        criados.append("ficha do paciente")

    if parceiro and jornada and not sessao.scalar(
        select(AtribuicaoParceiro.id).where(
            AtribuicaoParceiro.jornada_id == jornada.id,
            AtribuicaoParceiro.parceiro_id == parceiro.id,
        )
    ):
        sessao.add(AtribuicaoParceiro(jornada_id=jornada.id, parceiro_id=parceiro.id))
        criados.append("parceiro atribuído à jornada")

    sessao.commit()
    return criados


def criar_dados_de_exemplo() -> None:
    with SessaoLocal() as sessao:
        if sessao.scalar(select(Usuario.id).where(Usuario.email == EMAIL_PACIENTE)):
            criados = _complementar_ficha_e_parceiro(sessao)
            if criados:
                print("Dados de exemplo complementados: " + ", ".join(criados) + ".")
            else:
                print("Os dados de exemplo já existem. Nada foi alterado.")
            return

        agora = agora_utc()
        senha_hash = gerar_hash_senha(SENHA_EXEMPLO)

        medico = sessao.scalar(select(Usuario).where(Usuario.tipo_usuario == TipoUsuario.medico))
        medico_criado = medico is None
        if medico_criado:
            medico = Usuario(
                tipo_usuario=TipoUsuario.medico,
                nome="Dra. Ana Souza",
                email=EMAIL_MEDICO,
                profissao=PROFISSAO_MEDICO,
                senha_hash=senha_hash,
            )
            sessao.add(medico)

        # Contas de exemplo já com senha definida, para dispensar o fluxo da senha provisória
        paciente = Usuario(
            tipo_usuario=TipoUsuario.paciente,
            nome="Carlos Lima",
            email=EMAIL_PACIENTE,
            senha_hash=senha_hash,
        )
        parceiro = Usuario(
            tipo_usuario=TipoUsuario.parceiro,
            nome="Marina Costa",
            email=EMAIL_PARCEIRO,
            profissao="Nutricionista",
            senha_hash=senha_hash,
        )
        sessao.add_all([paciente, parceiro])
        sessao.flush()

        jornada = Jornada(
            medico_id=medico.id,
            paciente_id=paciente.id,
            titulo="Controle da hipertensão",
            descricao="Acompanhamento da pressão arterial após o diagnóstico de hipertensão estágio 1.",
            passo_atual=PassoJornada.exame,
            criado_em=agora - timedelta(days=21),
        )
        sessao.add(jornada)
        sessao.flush()

        sessao.add(
            Consulta(
                jornada_id=jornada.id,
                tipo=TipoConsulta.consulta,
                data=agora - timedelta(days=20),
                anotacoes="Pressão 145x95. Iniciar medicação e reduzir o sal. Pedir exames de rotina.",
                prescricoes=[
                    Prescricao(descricao="Losartana 50 mg", dosagem="1 comprimido", instrucoes="Pela manhã, todos os dias"),
                    Prescricao(descricao="Caminhada", dosagem="30 minutos", instrucoes="5 vezes por semana"),
                ],
            )
        )

        sessao.add_all(
            [
                Solicitacao(
                    jornada_id=jornada.id,
                    destinatario_id=paciente.id,
                    tipo=TipoSolicitacao.exame,
                    descricao="Hemograma completo e perfil lipídico",
                    prazo=agora - timedelta(days=2),  # vencida
                    criado_em=agora - timedelta(days=20),
                ),
                Solicitacao(
                    jornada_id=jornada.id,
                    # Destinada à nutricionista parceira, que é atribuída à jornada logo abaixo
                    destinatario_id=parceiro.id,
                    tipo=TipoSolicitacao.orientacao_profissional,
                    descricao="Montar e enviar o plano alimentar com redução de sódio",
                    prazo=agora + timedelta(days=2),
                    criado_em=agora - timedelta(days=20),
                ),
                Solicitacao(
                    jornada_id=jornada.id,
                    destinatario_id=paciente.id,
                    tipo=TipoSolicitacao.consulta_extra,
                    descricao="Consulta extra para reavaliar a dose da medicação",
                    prazo=agora + timedelta(days=7),
                    criado_em=agora - timedelta(days=5),
                ),
            ]
        )

        arquivo = _gravar_arquivo_texto(
            jornada.id,
            paciente.id,
            "medicoes_pressao.txt",
            "Medições de pressão arterial (em casa)\n"
            "Semana 1: 142x92, 140x90, 138x91\n"
            "Semana 2: 135x88, 132x86, 130x85\n",
        )
        sessao.add(arquivo)
        sessao.flush()
        sessao.add(
            Documento(
                jornada_id=jornada.id,
                enviado_por_id=paciente.id,
                categoria=CategoriaDocumento.outro,
                titulo="Diário de medições de pressão",
                arquivo_id=arquivo.id,
                criado_em=agora - timedelta(days=3),
            )
        )

        sessao.commit()
        _complementar_ficha_e_parceiro(sessao)
        email_medico = medico.email

    print("Dados de exemplo criados:")
    if medico_criado:
        print(f"  Médico:   {EMAIL_MEDICO} / {SENHA_EXEMPLO}")
    else:
        print(f"  Médico:   {email_medico} (conta já existente, senha inalterada)")
    print(f"  Paciente: {EMAIL_PACIENTE} / {SENHA_EXEMPLO}")
    print(f"  Parceiro: {EMAIL_PARCEIRO} / {SENHA_EXEMPLO}")


if __name__ == "__main__":
    criar_dados_de_exemplo()
