"""Cria dados de exemplo: um médico, um paciente, o vínculo e uma jornada com histórico.

Uso (na pasta backend, com o venv ativo e o banco migrado):
    python -m scripts.seed

Pode ser executado mais de uma vez: se o médico de exemplo já existir, nada é feito.
"""

import uuid
from datetime import timedelta

from sqlalchemy import select

from app.core.config import obter_configuracoes
from app.core.seguranca import gerar_hash_senha
from app.db.base import agora_utc
from app.db.sessao import SessaoLocal
from app.models import (
    Arquivo,
    Consulta,
    Exame,
    Jornada,
    Mensagem,
    PapelUsuario,
    PassoJornada,
    Prescricao,
    Solicitacao,
    TipoConsulta,
    TipoSolicitacao,
    Usuario,
    VinculoMedicoPaciente,
)

SENHA_EXEMPLO = "lifescan123"
EMAIL_MEDICO = "medico@lifescan.com"
EMAIL_PACIENTE = "paciente@lifescan.com"


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


def criar_dados_de_exemplo() -> None:
    with SessaoLocal() as sessao:
        if sessao.scalar(select(Usuario.id).where(Usuario.email == EMAIL_MEDICO)):
            print("Os dados de exemplo já existem. Nada foi alterado.")
            return

        agora = agora_utc()
        senha_hash = gerar_hash_senha(SENHA_EXEMPLO)

        medico = Usuario(nome="Dra. Ana Souza", email=EMAIL_MEDICO, senha_hash=senha_hash, papel=PapelUsuario.medico)
        paciente = Usuario(nome="Carlos Lima", email=EMAIL_PACIENTE, senha_hash=senha_hash, papel=PapelUsuario.paciente)
        sessao.add_all([medico, paciente])
        sessao.flush()

        sessao.add(VinculoMedicoPaciente(medico_id=medico.id, paciente_id=paciente.id))
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
                    tipo=TipoSolicitacao.exame,
                    descricao="Hemograma completo e perfil lipídico",
                    prazo=agora - timedelta(days=2),  # vencida
                    criado_em=agora - timedelta(days=20),
                ),
                Solicitacao(
                    jornada_id=jornada.id,
                    tipo=TipoSolicitacao.orientacao_profissional,
                    descricao="Enviar o plano alimentar da nutricionista",
                    prazo=agora + timedelta(days=2),
                    criado_em=agora - timedelta(days=20),
                ),
                Solicitacao(
                    jornada_id=jornada.id,
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
            Exame(
                jornada_id=jornada.id,
                enviado_por_id=paciente.id,
                titulo="Diário de medições de pressão",
                arquivo_id=arquivo.id,
                criado_em=agora - timedelta(days=3),
            )
        )

        sessao.add_all(
            [
                Mensagem(
                    jornada_id=jornada.id,
                    remetente_id=medico.id,
                    conteudo="Olá, Carlos! Lembre-se de medir a pressão todos os dias e anotar os valores.",
                    criado_em=agora - timedelta(days=19),
                ),
                Mensagem(
                    jornada_id=jornada.id,
                    remetente_id=paciente.id,
                    conteudo="Doutora, enviei o diário de medições. A pressão está baixando!",
                    criado_em=agora - timedelta(days=3),
                ),
            ]
        )

        sessao.commit()

    print("Dados de exemplo criados:")
    print(f"  Médico:   {EMAIL_MEDICO} / {SENHA_EXEMPLO}")
    print(f"  Paciente: {EMAIL_PACIENTE} / {SENHA_EXEMPLO}")


if __name__ == "__main__":
    criar_dados_de_exemplo()
