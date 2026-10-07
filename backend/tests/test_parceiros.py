"""Atribuição de parceiros à jornada e o que o parceiro pode (e não pode) ver."""

from tests.conftest import (
    atribuir_parceiro,
    criar_conta_ativa,
    criar_jornada,
    criar_solicitacao,
    enviar_documento,
)


def _url(jornada) -> str:
    return f"/journeys/{jornada['id']}/partners"


# --- Atribuição


def test_medico_atribui_parceiro(cliente, medico, parceiro, jornada):
    atribuicao = atribuir_parceiro(cliente, medico, jornada, parceiro)
    assert atribuicao["parceiro"] == {
        "id": parceiro["usuario"]["id"],
        "nome": "Marina Costa",
        "email": "marina@nutri.com",
        "profissao": "Nutricionista",
    }

    lista = cliente.get(_url(jornada), headers=medico["headers"]).json()
    assert [a["parceiro"]["nome"] for a in lista] == ["Marina Costa"]


def test_paciente_ve_os_parceiros_mas_nao_atribui(cliente, medico, paciente, parceiro_atribuido, jornada):
    lista = cliente.get(_url(jornada), headers=paciente["headers"])
    assert lista.status_code == 200
    assert lista.json()[0]["parceiro"]["profissao"] == "Nutricionista"

    resposta = cliente.post(
        _url(jornada), json={"parceiro_id": parceiro_atribuido["usuario"]["id"]}, headers=paciente["headers"]
    )
    assert resposta.status_code == 403


def test_atribuicao_repetida_retorna_409(cliente, medico, parceiro_atribuido, jornada):
    resposta = cliente.post(
        _url(jornada), json={"parceiro_id": parceiro_atribuido["usuario"]["id"]}, headers=medico["headers"]
    )
    assert resposta.status_code == 409


def test_so_parceiros_ativos_podem_ser_atribuidos(cliente, medico, paciente, outro_paciente, parceiro, jornada):
    for usuario_id in (outro_paciente["usuario"]["id"], medico["usuario"]["id"], 999):
        resposta = cliente.post(_url(jornada), json={"parceiro_id": usuario_id}, headers=medico["headers"])
        assert resposta.status_code == 404

    cliente.patch(f"/users/{parceiro['usuario']['id']}", json={"ativo": False}, headers=medico["headers"])
    resposta = cliente.post(
        _url(jornada), json={"parceiro_id": parceiro["usuario"]["id"]}, headers=medico["headers"]
    )
    assert resposta.status_code == 409


def test_parceiro_pode_ser_atribuido_antes_do_primeiro_acesso(cliente, medico, jornada):
    """Como o paciente, o parceiro não precisa ter entrado no sistema para o médico trabalhar."""
    from tests.conftest import criar_conta

    conta = criar_conta(cliente, medico, "parceiro", "Rui Prado", "rui@fisio.com", "Fisioterapeuta").json()
    assert conta["primeiro_acesso_pendente"] is True
    resposta = cliente.post(_url(jornada), json={"parceiro_id": conta["id"]}, headers=medico["headers"])
    assert resposta.status_code == 201


def test_medico_remove_parceiro_e_o_acesso_acaba(cliente, medico, parceiro_atribuido, jornada):
    parceiro_id = parceiro_atribuido["usuario"]["id"]
    assert cliente.get(f"/journeys/{jornada['id']}", headers=parceiro_atribuido["headers"]).status_code == 200

    resposta = cliente.delete(f"{_url(jornada)}/{parceiro_id}", headers=medico["headers"])
    assert resposta.status_code == 204
    assert cliente.get(_url(jornada), headers=medico["headers"]).json() == []
    assert cliente.get(f"/journeys/{jornada['id']}", headers=parceiro_atribuido["headers"]).status_code == 403
    assert cliente.get("/journeys", headers=parceiro_atribuido["headers"]).json() == []

    # Remover de novo: não está mais atribuído
    assert cliente.delete(f"{_url(jornada)}/{parceiro_id}", headers=medico["headers"]).status_code == 404


def test_nao_atribui_parceiro_em_jornada_encerrada(cliente, medico, parceiro, jornada):
    cliente.patch(f"/journeys/{jornada['id']}/status", json={"status": "encerrada"}, headers=medico["headers"])
    resposta = cliente.post(
        _url(jornada), json={"parceiro_id": parceiro["usuario"]["id"]}, headers=medico["headers"]
    )
    assert resposta.status_code == 409


# --- O que o parceiro vê


def test_parceiro_sem_atribuicao_nao_ve_nada(cliente, parceiro, jornada):
    assert cliente.get("/journeys", headers=parceiro["headers"]).json() == []
    assert cliente.get(f"/journeys/{jornada['id']}", headers=parceiro["headers"]).status_code == 403
    assert cliente.get(_url(jornada), headers=parceiro["headers"]).status_code == 403


def test_parceiro_lista_apenas_as_jornadas_atribuidas(cliente, medico, parceiro_atribuido, outro_paciente, jornada):
    criar_jornada(cliente, medico, outro_paciente, titulo="Reabilitação do joelho")

    jornadas = cliente.get("/journeys", headers=parceiro_atribuido["headers"]).json()
    assert [j["id"] for j in jornadas] == [jornada["id"]]
    assert jornadas[0]["paciente"]["nome"] == "Carlos Lima"


def test_parceiro_nao_ve_consultas_nem_linha_do_tempo(cliente, medico, parceiro_atribuido, jornada):
    criar_solicitacao(cliente, medico, jornada)
    base = f"/journeys/{jornada['id']}"
    # As solicitações destinadas ao paciente não aparecem para o parceiro
    assert cliente.get(f"{base}/requests", headers=parceiro_atribuido["headers"]).json() == []
    for rota in ("consultations", "timeline", "partners"):
        resposta = cliente.get(f"{base}/{rota}", headers=parceiro_atribuido["headers"])
        assert resposta.status_code == 403, rota
        assert resposta.json()["detail"] == "Parceiros têm acesso apenas à ficha do paciente e aos próprios envios."


def test_parceiro_nao_altera_a_jornada(cliente, parceiro_atribuido, jornada):
    base = f"/journeys/{jornada['id']}"
    headers = parceiro_atribuido["headers"]
    assert cliente.patch(f"{base}/step", json={"passo_atual": "exame"}, headers=headers).status_code == 403
    assert cliente.patch(f"{base}/status", json={"status": "encerrada"}, headers=headers).status_code == 403
    consulta = cliente.post(
        f"{base}/consultations", json={"tipo": "consulta", "data": "2026-10-01T10:00:00Z"}, headers=headers
    )
    assert consulta.status_code == 403


# --- Envios do parceiro


def test_parceiro_envia_documento_e_ve_apenas_os_proprios_envios(
    cliente, medico, paciente, parceiro_atribuido, jornada
):
    enviar_documento(cliente, paciente, jornada, nome="hemograma.pdf")
    envio = enviar_documento(cliente, parceiro_atribuido, jornada, nome="plano_alimentar.pdf", conteudo=b"%PDF plano")
    assert envio.status_code == 201, envio.text
    assert envio.json()["enviado_por"]["nome"] == "Marina Costa"

    do_parceiro = cliente.get(f"/journeys/{jornada['id']}/documents", headers=parceiro_atribuido["headers"]).json()
    assert [e["arquivo"]["nome_original"] for e in do_parceiro] == ["plano_alimentar.pdf"]

    # Médico e paciente veem os dois
    for usuario in (medico, paciente):
        todos = cliente.get(f"/journeys/{jornada['id']}/documents", headers=usuario["headers"]).json()
        assert len(todos) == 2


def test_envio_do_parceiro_aparece_para_o_medico_revisar(cliente, medico, parceiro_atribuido, jornada):
    exame = enviar_documento(cliente, parceiro_atribuido, jornada, nome="plano.pdf").json()

    painel = cliente.get("/dashboard/pending", headers=medico["headers"]).json()
    assert [e["id"] for e in painel["documentos_aguardando_revisao"]] == [exame["id"]]

    revisao = cliente.patch(
        f"/documents/{exame['id']}/review", json={"observacao_revisao": "Plano aprovado."}, headers=medico["headers"]
    )
    assert revisao.status_code == 200
    # O parceiro vê a revisão do próprio envio, mas não pode revisar
    do_parceiro = cliente.get(f"/journeys/{jornada['id']}/documents", headers=parceiro_atribuido["headers"]).json()
    assert do_parceiro[0]["observacao_revisao"] == "Plano aprovado."
    assert cliente.patch(
        f"/documents/{exame['id']}/review", json={}, headers=parceiro_atribuido["headers"]
    ).status_code == 403


def test_parceiro_baixa_so_os_arquivos_que_enviou(cliente, medico, paciente, parceiro_atribuido, jornada):
    do_paciente = enviar_documento(cliente, paciente, jornada).json()
    do_parceiro = enviar_documento(cliente, parceiro_atribuido, jornada, nome="plano.pdf", conteudo=b"%PDF plano").json()
    headers = parceiro_atribuido["headers"]

    proprio = cliente.get(f"/files/{do_parceiro['arquivo']['id']}/download", headers=headers)
    assert proprio.status_code == 200
    assert proprio.content == b"%PDF plano"

    alheio = cliente.get(f"/files/{do_paciente['arquivo']['id']}/download", headers=headers)
    assert alheio.status_code == 403
    assert alheio.json()["detail"] == "Você só pode baixar os arquivos que enviou."

    # O médico e o paciente baixam o envio do parceiro normalmente
    for usuario in (medico, paciente):
        assert cliente.get(f"/files/{do_parceiro['arquivo']['id']}/download", headers=usuario["headers"]).status_code == 200


def test_parceiro_nao_atende_solicitacao_destinada_ao_paciente(cliente, medico, parceiro_atribuido, jornada):
    solicitacao = criar_solicitacao(cliente, medico, jornada, tipo="orientacao_profissional")
    resposta = enviar_documento(cliente, parceiro_atribuido, jornada, solicitacao_id=solicitacao["id"])
    # Para o parceiro, é como se a solicitação não existisse
    assert resposta.status_code == 404


def test_parceiro_nao_envia_sem_atribuicao_nem_em_jornada_encerrada(cliente, medico, parceiro, jornada):
    assert enviar_documento(cliente, parceiro, jornada).status_code == 403

    atribuir_parceiro(cliente, medico, jornada, parceiro)
    cliente.patch(f"/journeys/{jornada['id']}/status", json={"status": "encerrada"}, headers=medico["headers"])
    assert enviar_documento(cliente, parceiro, jornada).status_code == 409


def test_um_parceiro_nao_ve_os_envios_de_outro(cliente, medico, parceiro_atribuido, jornada):
    outro = criar_conta_ativa(cliente, medico, "parceiro", "Rui Prado", "rui@fisio.com", "Fisioterapeuta")
    atribuir_parceiro(cliente, medico, jornada, outro)
    envio = enviar_documento(cliente, parceiro_atribuido, jornada, nome="plano.pdf").json()

    assert cliente.get(f"/journeys/{jornada['id']}/documents", headers=outro["headers"]).json() == []
    assert cliente.get(f"/files/{envio['arquivo']['id']}/download", headers=outro["headers"]).status_code == 403
