"""Agenda de consultas: o médico e os colaboradores agendam; o paciente vê as próprias."""

from datetime import datetime, timedelta, timezone

import pytest

from app.models.agendamento import Agendamento
from tests.conftest import abrir_sessao, criar_acompanhamento


def _em(horas: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=horas)).isoformat()


def _registrar_consulta(cliente, medico, acompanhamento) -> None:
    resposta = cliente.post(
        f"/follow-ups/{acompanhamento['id']}/consultations",
        json={"tipo": "consulta", "data": _em(-24), "anotacoes": "Primeira consulta"},
        headers=medico["headers"],
    )
    assert resposta.status_code == 201, resposta.text


def _agendar(cliente, quem, paciente, horas: float, observacao: str | None = None):
    dados = {"paciente_id": paciente["usuario"]["id"], "data_hora": _em(horas)}
    if observacao is not None:
        dados["observacao"] = observacao
    return cliente.post("/appointments", json=dados, headers=quem["headers"])


def _mover_para_o_passado(agendamento_id: int, horas: float = 1) -> None:
    sessao = abrir_sessao()
    agendamento = sessao.get(Agendamento, agendamento_id)
    agendamento.data_hora = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=horas)
    sessao.commit()
    sessao.close()


@pytest.fixture
def paciente_atendido(cliente, medico, paciente, acompanhamento):
    """Paciente que já passou pela primeira consulta."""
    _registrar_consulta(cliente, medico, acompanhamento)
    return paciente


def test_colaborador_agenda_consulta(cliente, colaborador, paciente_atendido):
    resposta = _agendar(cliente, colaborador, paciente_atendido, 48, observacao="  Retorno  ")
    assert resposta.status_code == 201, resposta.text
    agendamento = resposta.json()
    assert agendamento["status"] == "agendada"
    assert agendamento["observacao"] == "Retorno"
    assert agendamento["paciente"] == {"id": paciente_atendido["usuario"]["id"], "nome": "Carlos Lima", "email": "carlos@email.com"}
    assert agendamento["criado_por"]["nome"] == "Juliana Rocha"


def test_medico_tambem_agenda(cliente, medico, paciente_atendido):
    assert _agendar(cliente, medico, paciente_atendido, 48).status_code == 201


def test_paciente_sem_conta_ativada_pode_ser_agendado(cliente, medico, colaborador):
    """O sistema não depende do paciente: basta ele ter passado pela primeira consulta."""
    criado = cliente.post(
        "/users", json={"tipo_usuario": "paciente", "nome": "Rita Dias", "email": "rita@email.com"}, headers=medico["headers"]
    ).json()
    assert criado["primeiro_acesso_pendente"] is True
    paciente = {"usuario": criado}
    _registrar_consulta(cliente, medico, criar_acompanhamento(cliente, medico, paciente))
    assert _agendar(cliente, colaborador, paciente, 48).status_code == 201


def test_paciente_sem_primeira_consulta_nao_pode_ser_agendado(cliente, colaborador, paciente, acompanhamento):
    resposta = _agendar(cliente, colaborador, paciente, 48)
    assert resposta.status_code == 422
    assert resposta.json()["detail"] == "Este paciente ainda não passou pela primeira consulta com o médico."


def test_paciente_sem_acompanhamento_nao_pode_ser_agendado(cliente, colaborador, paciente):
    assert _agendar(cliente, colaborador, paciente, 48).status_code == 422


def test_so_pacientes_podem_ser_agendados(cliente, colaborador, parceiro):
    assert _agendar(cliente, colaborador, parceiro, 48).status_code == 404
    assert cliente.post("/appointments", json={"paciente_id": 999, "data_hora": _em(48)}, headers=colaborador["headers"]).status_code == 404


def test_paciente_desativado_ou_acompanhamento_encerrado_nao_podem_ser_agendados(
    cliente, medico, colaborador, paciente_atendido, acompanhamento
):
    cliente.patch(f"/follow-ups/{acompanhamento['id']}/status", json={"status": "encerrado"}, headers=medico["headers"])
    assert "encerrado" in _agendar(cliente, colaborador, paciente_atendido, 48).json()["detail"]

    cliente.patch(f"/follow-ups/{acompanhamento['id']}/status", json={"status": "ativo"}, headers=medico["headers"])
    cliente.patch(f"/users/{paciente_atendido['usuario']['id']}", json={"ativo": False}, headers=medico["headers"])
    assert _agendar(cliente, colaborador, paciente_atendido, 48).json()["detail"] == "A conta deste paciente está desativada."


def test_horario_precisa_ser_futuro(cliente, colaborador, paciente_atendido):
    resposta = _agendar(cliente, colaborador, paciente_atendido, -1)
    assert resposta.status_code == 422
    assert resposta.json()["detail"] == "Escolha uma data e hora futuras."


@pytest.mark.parametrize("diferenca, aceito", [(0, False), (1, False), (1.99, False), (-1.5, False), (2, True), (-2, True), (5, True)])
def test_consultas_precisam_de_duas_horas_de_distancia(cliente, colaborador, paciente_atendido, diferenca, aceito):
    base = _agendar(cliente, colaborador, paciente_atendido, 48)
    assert base.status_code == 201
    data_base = datetime.fromisoformat(base.json()["data_hora"])
    resposta = cliente.post(
        "/appointments",
        json={"paciente_id": paciente_atendido["usuario"]["id"], "data_hora": (data_base + timedelta(hours=diferenca)).isoformat()},
        headers=colaborador["headers"],
    )
    assert resposta.status_code == (201 if aceito else 409), resposta.text
    if not aceito:
        assert "a menos de 2 horas" in resposta.json()["detail"]


def test_consulta_cancelada_libera_o_horario(cliente, colaborador, paciente_atendido):
    primeira = _agendar(cliente, colaborador, paciente_atendido, 48).json()
    cliente.patch(f"/appointments/{primeira['id']}/status", json={"status": "cancelada"}, headers=colaborador["headers"])
    assert cliente.post(
        "/appointments",
        json={"paciente_id": paciente_atendido["usuario"]["id"], "data_hora": primeira["data_hora"]},
        headers=colaborador["headers"],
    ).status_code == 201


def test_intervalo_minimo_e_configuravel(cliente, colaborador, paciente_atendido, config_teste, monkeypatch):
    monkeypatch.setattr(config_teste, "horas_entre_agendamentos", 1)
    assert _agendar(cliente, colaborador, paciente_atendido, 48).status_code == 201
    assert _agendar(cliente, colaborador, paciente_atendido, 49).status_code == 201


def test_remarcar_valida_o_novo_horario_ignorando_a_propria_consulta(cliente, colaborador, paciente_atendido):
    primeira = _agendar(cliente, colaborador, paciente_atendido, 48).json()
    _agendar(cliente, colaborador, paciente_atendido, 60)
    # Mover 1 hora não conflita com ela mesma
    data = datetime.fromisoformat(primeira["data_hora"])
    remarcada = cliente.patch(
        f"/appointments/{primeira['id']}", json={"data_hora": (data + timedelta(hours=1)).isoformat()}, headers=colaborador["headers"]
    )
    assert remarcada.status_code == 200, remarcada.text
    assert datetime.fromisoformat(remarcada.json()["data_hora"]) == data + timedelta(hours=1)
    # Mas não pode ficar a menos de 2 horas da outra
    conflito = cliente.patch(f"/appointments/{primeira['id']}", json={"data_hora": _em(59)}, headers=colaborador["headers"])
    assert conflito.status_code == 409
    passado = cliente.patch(f"/appointments/{primeira['id']}", json={"data_hora": _em(-3)}, headers=colaborador["headers"])
    assert passado.status_code == 422


def test_editar_so_a_observacao(cliente, colaborador, paciente_atendido):
    agendamento = _agendar(cliente, colaborador, paciente_atendido, 48, observacao="Retorno").json()
    resposta = cliente.patch(f"/appointments/{agendamento['id']}", json={"observacao": ""}, headers=colaborador["headers"])
    assert resposta.json()["observacao"] is None
    assert resposta.json()["data_hora"] == agendamento["data_hora"]


def test_cancelar_a_qualquer_momento_e_nao_mexer_mais(cliente, colaborador, paciente_atendido):
    agendamento = _agendar(cliente, colaborador, paciente_atendido, 48).json()
    url = f"/appointments/{agendamento['id']}"
    assert cliente.patch(url + "/status", json={"status": "cancelada"}, headers=colaborador["headers"]).json()["status"] == "cancelada"
    assert cliente.patch(url + "/status", json={"status": "realizada"}, headers=colaborador["headers"]).status_code == 409
    assert cliente.patch(url, json={"data_hora": _em(72)}, headers=colaborador["headers"]).status_code == 409


@pytest.mark.parametrize("desfecho", ["realizada", "faltou"])
def test_realizada_ou_falta_so_depois_do_horario(cliente, medico, colaborador, paciente_atendido, desfecho):
    agendamento = _agendar(cliente, colaborador, paciente_atendido, 48).json()
    url = f"/appointments/{agendamento['id']}/status"
    antes = cliente.patch(url, json={"status": desfecho}, headers=colaborador["headers"])
    assert antes.status_code == 422
    _mover_para_o_passado(agendamento["id"])
    depois = cliente.patch(url, json={"status": desfecho}, headers=medico["headers"])
    assert depois.status_code == 200
    assert depois.json()["status"] == desfecho


def test_status_agendada_nao_e_um_desfecho(cliente, colaborador, paciente_atendido):
    agendamento = _agendar(cliente, colaborador, paciente_atendido, 48).json()
    resposta = cliente.patch(f"/appointments/{agendamento['id']}/status", json={"status": "agendada"}, headers=colaborador["headers"])
    assert resposta.status_code == 422


def test_agendamento_inexistente(cliente, colaborador):
    assert cliente.patch("/appointments/999", json={"observacao": "x"}, headers=colaborador["headers"]).status_code == 404
    assert cliente.patch("/appointments/999/status", json={"status": "cancelada"}, headers=colaborador["headers"]).status_code == 404


def test_listagem_com_filtros_e_ordem(cliente, colaborador, paciente_atendido):
    ids = [_agendar(cliente, colaborador, paciente_atendido, horas).json()["id"] for horas in (72, 24, 48)]
    lista = cliente.get("/appointments", headers=colaborador["headers"]).json()
    assert [a["id"] for a in lista] == [ids[1], ids[2], ids[0]]

    recentes = cliente.get("/appointments", params={"ordem": "desc"}, headers=colaborador["headers"]).json()
    assert [a["id"] for a in recentes] == [ids[0], ids[2], ids[1]]

    janela = cliente.get("/appointments", params={"inicio": _em(30), "fim": _em(60)}, headers=colaborador["headers"]).json()
    assert [a["id"] for a in janela] == [ids[2]]

    cliente.patch(f"/appointments/{ids[0]}/status", json={"status": "cancelada"}, headers=colaborador["headers"])
    canceladas = cliente.get("/appointments", params={"status": "cancelada"}, headers=colaborador["headers"]).json()
    assert [a["id"] for a in canceladas] == [ids[0]]

    pagina = cliente.get("/appointments", params={"pagina": 1, "tamanho": 2}, headers=colaborador["headers"]).json()
    assert pagina["total"] == 3 and len(pagina["itens"]) == 2


def test_paciente_ve_so_as_proprias_e_nao_agenda(cliente, medico, colaborador, paciente_atendido, outro_paciente):
    _registrar_consulta(cliente, medico, criar_acompanhamento(cliente, medico, outro_paciente, "Outro"))
    meu = _agendar(cliente, colaborador, paciente_atendido, 48).json()
    _agendar(cliente, colaborador, outro_paciente, 72)

    minhas = cliente.get("/appointments", headers=paciente_atendido["headers"]).json()
    assert [a["id"] for a in minhas] == [meu["id"]]
    assert _agendar(cliente, paciente_atendido, paciente_atendido, 96).status_code == 403
    assert cliente.patch(f"/appointments/{meu['id']}/status", json={"status": "cancelada"}, headers=paciente_atendido["headers"]).status_code == 403
    assert cliente.get("/appointments/patients", headers=paciente_atendido["headers"]).status_code == 403


def test_parceiro_nao_acessa_a_agenda(cliente, parceiro):
    assert cliente.get("/appointments", headers=parceiro["headers"]).status_code == 403
    assert cliente.get("/appointments/patients", headers=parceiro["headers"]).status_code == 403
    assert cliente.get("/appointments").status_code == 401


def test_pacientes_agendaveis(cliente, medico, colaborador, paciente_atendido, outro_paciente):
    # outro_paciente tem acompanhamento mas ainda não teve a primeira consulta
    criar_acompanhamento(cliente, medico, outro_paciente, "Outro")
    lista = cliente.get("/appointments/patients", headers=colaborador["headers"]).json()
    assert lista == [{"id": paciente_atendido["usuario"]["id"], "nome": "Carlos Lima", "email": "carlos@email.com"}]
    assert cliente.get("/appointments/patients", params={"busca": "mar"}, headers=colaborador["headers"]).json() == []

    cliente.patch(f"/users/{paciente_atendido['usuario']['id']}", json={"ativo": False}, headers=medico["headers"])
    assert cliente.get("/appointments/patients", headers=medico["headers"]).json() == []


def test_paineis_mostram_as_consultas(cliente, colaborador, paciente_atendido):
    passada = _agendar(cliente, colaborador, paciente_atendido, 24).json()
    _mover_para_o_passado(passada["id"])
    proxima = _agendar(cliente, colaborador, paciente_atendido, 48).json()
    cancelada = _agendar(cliente, colaborador, paciente_atendido, 72).json()
    cliente.patch(f"/appointments/{cancelada['id']}/status", json={"status": "cancelada"}, headers=colaborador["headers"])

    painel = cliente.get("/dashboard/pending", headers=colaborador["headers"]).json()
    assert [a["id"] for a in painel["aguardando_desfecho"]] == [passada["id"]]
    assert [a["id"] for a in painel["proximas_consultas"]] == [proxima["id"]]

    painel_paciente = cliente.get("/dashboard/pending", headers=paciente_atendido["headers"]).json()
    assert [a["id"] for a in painel_paciente["proximas_consultas"]] == [proxima["id"]]
