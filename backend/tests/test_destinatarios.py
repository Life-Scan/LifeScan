"""Solicitações com destinatário (paciente ou parceiro) e categorias de documento."""

from datetime import datetime, timedelta, timezone

from tests.conftest import atribuir_parceiro, criar_solicitacao, definir_prazo, enviar_documento


def _solicitacoes(cliente, usuario, jornada) -> list[dict]:
    resposta = cliente.get(f"/journeys/{jornada['id']}/requests", headers=usuario["headers"])
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def _painel(cliente, usuario) -> dict:
    return cliente.get("/dashboard/pending", headers=usuario["headers"]).json()


# --- Destinatário


def test_sem_destinatario_a_solicitacao_vai_para_o_paciente(cliente, medico, paciente, jornada):
    solicitacao = criar_solicitacao(cliente, medico, jornada)
    assert solicitacao["destinatario"] == {
        "id": paciente["usuario"]["id"],
        "nome": "Carlos Lima",
        "tipo_usuario": "paciente",
        "profissao": None,
    }


def test_medico_destina_solicitacao_a_parceiro_atribuido(cliente, medico, parceiro_atribuido, jornada):
    solicitacao = criar_solicitacao(
        cliente, medico, jornada, tipo="orientacao_profissional", destinatario=parceiro_atribuido
    )
    assert solicitacao["destinatario"]["nome"] == "Marina Costa"
    assert solicitacao["destinatario"]["tipo_usuario"] == "parceiro"
    assert solicitacao["destinatario"]["profissao"] == "Nutricionista"


def test_destinatario_precisa_participar_da_jornada(cliente, medico, parceiro, outro_paciente, jornada):
    prazo = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    # Parceiro existente mas não atribuído, outro paciente, o médico e um id inexistente
    for destinatario_id in (parceiro["usuario"]["id"], outro_paciente["usuario"]["id"], medico["usuario"]["id"], 999):
        resposta = cliente.post(
            f"/journeys/{jornada['id']}/requests",
            json={"tipo": "outro", "descricao": "Teste", "prazo": prazo, "destinatario_id": destinatario_id},
            headers=medico["headers"],
        )
        assert resposta.status_code == 422, destinatario_id
        assert "destinatário precisa ser" in resposta.json()["detail"]


def test_consulta_extra_nao_pode_ir_para_parceiro(cliente, medico, parceiro_atribuido, jornada):
    prazo = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    resposta = cliente.post(
        f"/journeys/{jornada['id']}/requests",
        json={
            "tipo": "consulta_extra",
            "descricao": "Reavaliação",
            "prazo": prazo,
            "destinatario_id": parceiro_atribuido["usuario"]["id"],
        },
        headers=medico["headers"],
    )
    assert resposta.status_code == 422


def test_quem_ve_cada_solicitacao(cliente, medico, paciente, parceiro_atribuido, jornada):
    do_paciente = criar_solicitacao(cliente, medico, jornada, tipo="exame")
    do_parceiro = criar_solicitacao(
        cliente, medico, jornada, tipo="orientacao_profissional", destinatario=parceiro_atribuido
    )

    # Médico e paciente veem todas; o parceiro, só a dele
    for usuario in (medico, paciente):
        assert {s["id"] for s in _solicitacoes(cliente, usuario, jornada)} == {do_paciente["id"], do_parceiro["id"]}
    assert [s["id"] for s in _solicitacoes(cliente, parceiro_atribuido, jornada)] == [do_parceiro["id"]]


def test_parceiro_atende_a_propria_solicitacao_com_um_envio(cliente, medico, parceiro_atribuido, jornada):
    solicitacao = criar_solicitacao(
        cliente, medico, jornada, tipo="orientacao_profissional", destinatario=parceiro_atribuido
    )
    envio = enviar_documento(
        cliente,
        parceiro_atribuido,
        jornada,
        nome="plano_alimentar.pdf",
        solicitacao_id=solicitacao["id"],
        categoria="plano_alimentar",
    )
    assert envio.status_code == 201, envio.text
    assert envio.json()["categoria"] == "plano_alimentar"
    assert envio.json()["solicitacao_id"] == solicitacao["id"]

    assert _solicitacoes(cliente, parceiro_atribuido, jornada)[0]["status"] == "atendida"
    # Não dá para atender duas vezes
    repetido = enviar_documento(cliente, parceiro_atribuido, jornada, solicitacao_id=solicitacao["id"])
    assert repetido.status_code == 409


def test_cada_um_so_atende_as_proprias_solicitacoes(cliente, medico, paciente, parceiro_atribuido, jornada):
    do_paciente = criar_solicitacao(cliente, medico, jornada, tipo="exame")
    do_parceiro = criar_solicitacao(
        cliente, medico, jornada, tipo="orientacao_profissional", destinatario=parceiro_atribuido
    )

    resposta = enviar_documento(cliente, paciente, jornada, solicitacao_id=do_parceiro["id"])
    assert resposta.status_code == 403
    assert resposta.json()["detail"] == "Esta solicitação é destinada a outra pessoa."

    assert enviar_documento(cliente, parceiro_atribuido, jornada, solicitacao_id=do_paciente["id"]).status_code == 404

    # Nada foi marcado como atendido
    assert {s["status"] for s in _solicitacoes(cliente, medico, jornada)} == {"pendente"}


def test_medico_pode_atender_solicitacao_de_qualquer_destinatario(cliente, medico, parceiro_atribuido, jornada):
    """Ex.: o parceiro entregou o plano impresso na clínica e o médico anexa."""
    solicitacao = criar_solicitacao(
        cliente, medico, jornada, tipo="orientacao_profissional", destinatario=parceiro_atribuido
    )
    envio = enviar_documento(cliente, medico, jornada, solicitacao_id=solicitacao["id"], categoria="orientacao")
    assert envio.status_code == 201
    assert _solicitacoes(cliente, medico, jornada)[0]["status"] == "atendida"


# --- Painéis


def test_painel_do_parceiro_mostra_as_solicitacoes_dele(cliente, medico, paciente, parceiro_atribuido, jornada):
    criar_solicitacao(cliente, medico, jornada, tipo="exame")
    vencida = criar_solicitacao(
        cliente, medico, jornada, tipo="orientacao_profissional", destinatario=parceiro_atribuido
    )
    definir_prazo(vencida["id"], timedelta(days=-1))
    futura = criar_solicitacao(cliente, medico, jornada, tipo="outro", dias=10, destinatario=parceiro_atribuido)

    painel = _painel(cliente, parceiro_atribuido)
    assert painel["tipo_usuario"] == "parceiro"
    pendentes = painel["solicitacoes_pendentes"]
    assert [s["id"] for s in pendentes] == [vencida["id"], futura["id"]]
    assert [s["vencida"] for s in pendentes] == [True, False]
    assert pendentes[0]["jornada"]["paciente"]["nome"] == "Carlos Lima"


def test_painel_do_paciente_nao_inclui_solicitacoes_do_parceiro(cliente, medico, paciente, parceiro_atribuido, jornada):
    do_paciente = criar_solicitacao(cliente, medico, jornada, tipo="exame")
    criar_solicitacao(cliente, medico, jornada, tipo="orientacao_profissional", destinatario=parceiro_atribuido)

    pendentes = _painel(cliente, paciente)["solicitacoes_pendentes"]
    assert [s["id"] for s in pendentes] == [do_paciente["id"]]


def test_painel_do_medico_acompanha_todos_os_destinatarios(cliente, medico, parceiro_atribuido, jornada):
    criar_solicitacao(cliente, medico, jornada, tipo="exame", dias=1)
    criar_solicitacao(cliente, medico, jornada, tipo="orientacao_profissional", dias=2, destinatario=parceiro_atribuido)

    proximas = _painel(cliente, medico)["solicitacoes_proximas_do_prazo"]
    assert [s["destinatario"]["tipo_usuario"] for s in proximas] == ["paciente", "parceiro"]


def test_parceiro_removido_deixa_de_ver_as_solicitacoes(cliente, medico, parceiro_atribuido, jornada):
    criar_solicitacao(cliente, medico, jornada, tipo="outro", destinatario=parceiro_atribuido)
    assert len(_painel(cliente, parceiro_atribuido)["solicitacoes_pendentes"]) == 1

    cliente.delete(
        f"/journeys/{jornada['id']}/partners/{parceiro_atribuido['usuario']['id']}", headers=medico["headers"]
    )
    assert _painel(cliente, parceiro_atribuido)["solicitacoes_pendentes"] == []
    assert cliente.get(f"/journeys/{jornada['id']}/requests", headers=parceiro_atribuido["headers"]).status_code == 403
    # A solicitação continua visível para o médico, que pode cancelá-la
    assert len(_solicitacoes(cliente, medico, jornada)) == 1


def test_linha_do_tempo_menciona_o_destinatario_parceiro(cliente, medico, paciente, parceiro, jornada):
    atribuir_parceiro(cliente, medico, jornada, parceiro)
    criar_solicitacao(cliente, medico, jornada, tipo="exame")
    criar_solicitacao(cliente, medico, jornada, tipo="orientacao_profissional", destinatario=parceiro)

    resumos = [e["resumo"] for e in cliente.get(f"/journeys/{jornada['id']}/timeline", headers=paciente["headers"]).json()]
    assert resumos[0].startswith("Solicitação de exame: ")
    assert resumos[1].startswith("Solicitação de orientação de outro profissional para Marina Costa: ")


# --- Categorias de documento


def test_categoria_padrao_e_exame(cliente, paciente, jornada):
    assert enviar_documento(cliente, paciente, jornada).json()["categoria"] == "exame"


def test_todas_as_categorias_sao_aceitas(cliente, paciente, jornada):
    for categoria in ("exame", "laudo", "plano_alimentar", "plano_treino", "orientacao", "outro"):
        resposta = enviar_documento(cliente, paciente, jornada, categoria=categoria)
        assert resposta.status_code == 201, categoria
        assert resposta.json()["categoria"] == categoria


def test_categoria_invalida_retorna_422(cliente, paciente, jornada):
    assert enviar_documento(cliente, paciente, jornada, categoria="receita").status_code == 422


def test_filtro_por_categoria(cliente, medico, paciente, jornada):
    enviar_documento(cliente, paciente, jornada, categoria="exame")
    enviar_documento(cliente, paciente, jornada, categoria="laudo")
    enviar_documento(cliente, paciente, jornada, categoria="laudo")

    url = f"/journeys/{jornada['id']}/documents"
    laudos = cliente.get(url, params={"categoria": "laudo"}, headers=medico["headers"]).json()
    assert len(laudos) == 2
    assert len(cliente.get(url, headers=medico["headers"]).json()) == 3


def test_linha_do_tempo_mostra_a_categoria_do_documento(cliente, medico, parceiro_atribuido, jornada):
    enviar_documento(cliente, parceiro_atribuido, jornada, nome="treino.pdf", categoria="plano_treino")
    evento = cliente.get(f"/journeys/{jornada['id']}/timeline", headers=medico["headers"]).json()[0]
    assert evento["tipo"] == "documento"
    assert evento["resumo"] == "Marina Costa enviou plano de treino: Hemograma completo"
    assert evento["dados"]["categoria"] == "plano_treino"


def test_rotas_antigas_de_exames_nao_existem_mais(cliente, medico, jornada):
    assert cliente.get(f"/journeys/{jornada['id']}/exams", headers=medico["headers"]).status_code == 404
