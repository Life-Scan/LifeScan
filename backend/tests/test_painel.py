from datetime import timedelta

from tests.conftest import (
    criar_jornada,
    criar_solicitacao,
    definir_prazo,
    enviar_exame,
    enviar_mensagem,
    vincular,
)


def _painel(cliente, usuario) -> dict:
    resposta = cliente.get("/dashboard/pending", headers=usuario["headers"])
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def test_painel_vazio_por_papel(cliente, medico, paciente, jornada):
    do_medico = _painel(cliente, medico)
    assert do_medico["papel"] == "medico"
    assert do_medico["dias_prazo_proximo"] == 3
    for chave in (
        "exames_aguardando_revisao",
        "solicitacoes_vencidas",
        "solicitacoes_proximas_do_prazo",
        "mensagens_nao_respondidas",
    ):
        assert do_medico[chave] == []

    do_paciente = _painel(cliente, paciente)
    assert do_paciente == {"papel": "paciente", "solicitacoes_pendentes": [], "consultas_extras": []}


def test_painel_exige_login(cliente):
    assert cliente.get("/dashboard/pending").status_code == 401


def test_medico_ve_exames_aguardando_revisao(cliente, medico, paciente, jornada):
    enviar_exame(cliente, paciente, jornada)
    revisado = enviar_exame(cliente, paciente, jornada).json()
    cliente.patch(f"/exams/{revisado['id']}/review", json={}, headers=medico["headers"])
    # Arquivo enviado pelo próprio médico não entra como pendência dele
    enviar_exame(cliente, medico, jornada)

    exames = _painel(cliente, medico)["exames_aguardando_revisao"]
    assert len(exames) == 1
    assert exames[0]["status"] == "enviado"
    assert exames[0]["jornada"]["paciente"]["nome"] == "Carlos Lima"


def test_medico_ve_solicitacoes_vencidas_e_proximas(cliente, medico, jornada):
    vencida = criar_solicitacao(cliente, medico, jornada)
    definir_prazo(vencida["id"], timedelta(days=-2))
    proxima = criar_solicitacao(cliente, medico, jornada, dias=2)
    criar_solicitacao(cliente, medico, jornada, dias=10)  # longe do prazo: fora do painel
    cancelada = criar_solicitacao(cliente, medico, jornada, dias=1)
    cliente.patch(f"/requests/{cancelada['id']}/cancel", headers=medico["headers"])

    painel = _painel(cliente, medico)
    assert [s["id"] for s in painel["solicitacoes_vencidas"]] == [vencida["id"]]
    assert painel["solicitacoes_vencidas"][0]["vencida"] is True
    assert [s["id"] for s in painel["solicitacoes_proximas_do_prazo"]] == [proxima["id"]]


def test_prazo_proximo_segue_configuracao(cliente, medico, jornada, config_teste, monkeypatch):
    monkeypatch.setattr(config_teste, "dias_prazo_proximo", 15)
    criar_solicitacao(cliente, medico, jornada, dias=10)
    painel = _painel(cliente, medico)
    assert painel["dias_prazo_proximo"] == 15
    assert len(painel["solicitacoes_proximas_do_prazo"]) == 1


def test_mensagem_nao_respondida(cliente, medico, paciente, jornada):
    enviar_mensagem(cliente, paciente, jornada, "Doutora, estou com tontura.")
    pendentes = _painel(cliente, medico)["mensagens_nao_respondidas"]
    assert len(pendentes) == 1
    assert pendentes[0]["jornada"]["id"] == jornada["id"]
    assert pendentes[0]["ultima_mensagem"]["conteudo"] == "Doutora, estou com tontura."

    enviar_mensagem(cliente, medico, jornada, "Meça a pressão e me avise.")
    assert _painel(cliente, medico)["mensagens_nao_respondidas"] == []

    enviar_mensagem(cliente, paciente, jornada, "12x8.")
    pendentes = _painel(cliente, medico)["mensagens_nao_respondidas"]
    assert pendentes[0]["ultima_mensagem"]["conteudo"] == "12x8."


def test_paciente_ve_pendencias_e_consultas_extras(cliente, medico, paciente, jornada):
    vencida = criar_solicitacao(cliente, medico, jornada, tipo="exame")
    definir_prazo(vencida["id"], timedelta(days=-1))
    futura = criar_solicitacao(cliente, medico, jornada, tipo="orientacao_profissional", dias=20)
    consulta_extra = criar_solicitacao(cliente, medico, jornada, tipo="consulta_extra", dias=4)
    atendida = criar_solicitacao(cliente, medico, jornada, tipo="exame")
    enviar_exame(cliente, paciente, jornada, solicitacao_id=atendida["id"])

    painel = _painel(cliente, paciente)
    pendentes = painel["solicitacoes_pendentes"]
    # Todas as pendentes, com prazo, vencidas primeiro
    assert [s["id"] for s in pendentes] == [vencida["id"], futura["id"]]
    assert [s["vencida"] for s in pendentes] == [True, False]
    assert [s["id"] for s in painel["consultas_extras"]] == [consulta_extra["id"]]


def test_painel_do_medico_so_mostra_os_proprios_pacientes(
    cliente, medico, outro_medico, paciente, outro_paciente, jornada
):
    vincular(cliente, outro_medico, outro_paciente)
    outra_jornada = criar_jornada(cliente, outro_medico, outro_paciente)
    enviar_exame(cliente, outro_paciente, outra_jornada)
    enviar_mensagem(cliente, outro_paciente, outra_jornada, "Oi, doutor")

    painel = _painel(cliente, medico)
    assert painel["exames_aguardando_revisao"] == []
    assert painel["mensagens_nao_respondidas"] == []
    assert len(_painel(cliente, outro_medico)["exames_aguardando_revisao"]) == 1


def test_jornada_encerrada_ou_vinculo_inativo_sai_do_painel(cliente, medico, paciente, jornada):
    enviar_exame(cliente, paciente, jornada)
    criar_solicitacao(cliente, medico, jornada, dias=1)
    assert len(_painel(cliente, medico)["exames_aguardando_revisao"]) == 1

    cliente.patch(f"/journeys/{jornada['id']}/status", json={"status": "encerrada"}, headers=medico["headers"])
    assert _painel(cliente, medico)["exames_aguardando_revisao"] == []
    assert _painel(cliente, paciente)["solicitacoes_pendentes"] == []

    cliente.patch(f"/journeys/{jornada['id']}/status", json={"status": "ativa"}, headers=medico["headers"])
    vinculo_id = cliente.get("/links", headers=medico["headers"]).json()[0]["id"]
    cliente.patch(f"/links/{vinculo_id}", json={"ativo": False}, headers=medico["headers"])
    assert _painel(cliente, medico)["exames_aguardando_revisao"] == []
