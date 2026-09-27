from datetime import datetime, timedelta, timezone

from app.db.sessao import obter_sessao
from app.main import app
from app.models.solicitacao import Solicitacao
from tests.conftest import criar_solicitacao


def _vencer(solicitacao_id: int) -> None:
    """Coloca o prazo no passado direto no banco (a API não aceita prazos passados)."""
    sessao = next(app.dependency_overrides[obter_sessao]())
    solicitacao = sessao.get(Solicitacao, solicitacao_id)
    solicitacao.prazo = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
    sessao.commit()
    sessao.close()


def test_medico_cria_solicitacoes_de_todos_os_tipos(cliente, medico, jornada):
    for tipo in ("exame", "consulta_extra", "orientacao_profissional", "outro"):
        solicitacao = criar_solicitacao(cliente, medico, jornada, tipo=tipo)
        assert solicitacao["tipo"] == tipo
        assert solicitacao["status"] == "pendente"
        assert solicitacao["vencida"] is False


def test_prazo_no_passado_retorna_422(cliente, medico, jornada):
    ontem = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    resposta = cliente.post(
        f"/journeys/{jornada['id']}/requests",
        json={"tipo": "exame", "descricao": "Hemograma", "prazo": ontem},
        headers=medico["headers"],
    )
    assert resposta.status_code == 422
    assert resposta.json()["detail"] == "O prazo deve ser uma data futura."


def test_paciente_nao_cria_solicitacao(cliente, paciente, jornada):
    prazo = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    resposta = cliente.post(
        f"/journeys/{jornada['id']}/requests",
        json={"tipo": "exame", "descricao": "Hemograma", "prazo": prazo},
        headers=paciente["headers"],
    )
    assert resposta.status_code == 403


def test_vencida_e_calculada_e_nao_gravada(cliente, medico, paciente, jornada):
    solicitacao = criar_solicitacao(cliente, medico, jornada)
    _vencer(solicitacao["id"])

    lista = cliente.get(f"/journeys/{jornada['id']}/requests", headers=paciente["headers"]).json()
    assert lista[0]["status"] == "pendente"
    assert lista[0]["vencida"] is True


def test_paciente_ve_consulta_extra_mas_nao_age_sobre_ela(cliente, medico, paciente, jornada):
    consulta_extra = criar_solicitacao(cliente, medico, jornada, tipo="consulta_extra")

    lista = cliente.get(f"/journeys/{jornada['id']}/requests", headers=paciente["headers"]).json()
    assert [s["tipo"] for s in lista] == ["consulta_extra"]

    for acao in ("complete", "cancel"):
        resposta = cliente.patch(f"/requests/{consulta_extra['id']}/{acao}", headers=paciente["headers"])
        assert resposta.status_code == 403


def test_medico_conclui_e_cancela_solicitacoes(cliente, medico, jornada):
    consulta_extra = criar_solicitacao(cliente, medico, jornada, tipo="consulta_extra")
    outro = criar_solicitacao(cliente, medico, jornada, tipo="outro")

    concluida = cliente.patch(f"/requests/{consulta_extra['id']}/complete", headers=medico["headers"]).json()
    assert concluida["status"] == "atendida"
    assert concluida["atendida_em"] is not None

    cancelada = cliente.patch(f"/requests/{outro['id']}/cancel", headers=medico["headers"]).json()
    assert cancelada["status"] == "cancelada"
    assert cancelada["vencida"] is False

    # Já resolvidas não podem mudar de novo
    resposta = cliente.patch(f"/requests/{outro['id']}/complete", headers=medico["headers"])
    assert resposta.status_code == 409


def test_filtro_por_status(cliente, medico, jornada):
    primeira = criar_solicitacao(cliente, medico, jornada)
    criar_solicitacao(cliente, medico, jornada)
    cliente.patch(f"/requests/{primeira['id']}/cancel", headers=medico["headers"])

    pendentes = cliente.get(
        f"/journeys/{jornada['id']}/requests", params={"status": "pendente"}, headers=medico["headers"]
    ).json()
    assert len(pendentes) == 1


def test_outro_medico_nao_conclui_solicitacao(cliente, medico, outro_medico, jornada):
    solicitacao = criar_solicitacao(cliente, medico, jornada)
    resposta = cliente.patch(f"/requests/{solicitacao['id']}/complete", headers=outro_medico["headers"])
    assert resposta.status_code == 403
