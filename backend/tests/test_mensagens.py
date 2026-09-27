def _enviar(cliente, usuario, jornada, conteudo=None, arquivo=None):
    return cliente.post(
        f"/journeys/{jornada['id']}/messages",
        data={"conteudo": conteudo} if conteudo is not None else {},
        files={"arquivo": arquivo} if arquivo else None,
        headers=usuario["headers"],
    )


def test_troca_de_mensagens_em_ordem_cronologica(cliente, medico, paciente, jornada):
    assert _enviar(cliente, paciente, jornada, "Doutora, a pressão baixou.").status_code == 201
    assert _enviar(cliente, medico, jornada, "Ótimo! Mantenha a medicação.").status_code == 201

    mensagens = cliente.get(f"/journeys/{jornada['id']}/messages", headers=paciente["headers"]).json()
    assert [m["remetente"]["id"] for m in mensagens] == [paciente["usuario"]["id"], medico["usuario"]["id"]]
    assert mensagens[1]["conteudo"] == "Ótimo! Mantenha a medicação."
    assert mensagens[0]["arquivo"] is None


def test_mensagem_com_anexo(cliente, medico, paciente, jornada):
    resposta = _enviar(
        cliente, paciente, jornada, "Orientação da nutricionista", ("dieta.pdf", b"%PDF dieta")
    )
    assert resposta.status_code == 201
    anexo = resposta.json()["arquivo"]
    assert anexo["nome_original"] == "dieta.pdf"

    download = cliente.get(f"/files/{anexo['id']}/download", headers=medico["headers"])
    assert download.content == b"%PDF dieta"


def test_mensagem_so_com_anexo(cliente, paciente, jornada):
    resposta = _enviar(cliente, paciente, jornada, arquivo=("foto.jpg", b"\xff\xd8\xff"))
    assert resposta.status_code == 201
    assert resposta.json()["conteudo"] is None


def test_mensagem_vazia_retorna_422(cliente, paciente, jornada):
    resposta = _enviar(cliente, paciente, jornada, "   ")
    assert resposta.status_code == 422
    assert resposta.json()["detail"] == "Escreva uma mensagem ou anexe um arquivo."


def test_anexo_com_extensao_proibida_retorna_415(cliente, paciente, jornada):
    resposta = _enviar(cliente, paciente, jornada, "Segue", ("programa.exe", b"MZ"))
    assert resposta.status_code == 415


def test_terceiros_nao_leem_nem_enviam_mensagens(cliente, outro_paciente, jornada):
    assert _enviar(cliente, outro_paciente, jornada, "Oi").status_code == 403
    assert cliente.get(f"/journeys/{jornada['id']}/messages", headers=outro_paciente["headers"]).status_code == 403


def test_jornada_encerrada_nao_aceita_mensagens(cliente, medico, paciente, jornada):
    _enviar(cliente, paciente, jornada, "Antes de encerrar")
    cliente.patch(f"/journeys/{jornada['id']}/status", json={"status": "encerrada"}, headers=medico["headers"])

    assert _enviar(cliente, paciente, jornada, "Depois de encerrar").status_code == 409
    mensagens = cliente.get(f"/journeys/{jornada['id']}/messages", headers=paciente["headers"])
    assert len(mensagens.json()) == 1
