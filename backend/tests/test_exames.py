import pytest

from tests.conftest import criar_solicitacao, enviar_exame


def _arquivos_em_disco(config) -> list:
    pasta = config.pasta_uploads
    return list(pasta.iterdir()) if pasta.exists() else []


def test_paciente_envia_exame(cliente, paciente, jornada, config_teste):
    resposta = enviar_exame(cliente, paciente, jornada)
    assert resposta.status_code == 201, resposta.text
    exame = resposta.json()
    assert exame["status"] == "enviado"
    assert exame["enviado_por"]["id"] == paciente["usuario"]["id"]
    assert exame["arquivo"]["nome_original"] == "hemograma.pdf"
    assert exame["arquivo"]["tipo_mime"] == "application/pdf"
    assert exame["arquivo"]["tamanho_bytes"] == len(b"%PDF-1.4 conteudo de teste")

    # Gravado em disco com nome gerado, não com o nome original
    gravados = _arquivos_em_disco(config_teste)
    assert len(gravados) == 1
    assert gravados[0].name != "hemograma.pdf"
    assert gravados[0].suffix == ".pdf"


def test_medico_tambem_envia_arquivo(cliente, medico, jornada):
    resposta = enviar_exame(cliente, medico, jornada, nome="laudo.png", conteudo=b"\x89PNG...")
    assert resposta.status_code == 201
    assert resposta.json()["arquivo"]["tipo_mime"] == "image/png"


@pytest.mark.parametrize("nome", ["exame.pdf", "FOTO.JPG", "imagem.jpeg", "scan.webp", "tomografia.dcm", "notas.txt"])
def test_extensoes_permitidas(cliente, paciente, jornada, nome):
    assert enviar_exame(cliente, paciente, jornada, nome=nome).status_code == 201


@pytest.mark.parametrize("nome", ["virus.exe", "planilha.xlsx", "script.pdf.js", "sem_extensao", "documento.docx"])
def test_extensoes_proibidas_retornam_415(cliente, paciente, jornada, config_teste, nome):
    resposta = enviar_exame(cliente, paciente, jornada, nome=nome)
    assert resposta.status_code == 415
    assert "Formato de arquivo não permitido" in resposta.json()["detail"]
    assert _arquivos_em_disco(config_teste) == []


def test_arquivo_acima_do_limite_retorna_413(cliente, paciente, jornada, config_teste, monkeypatch):
    monkeypatch.setattr(config_teste, "tamanho_maximo_upload_mb", 1)
    grande = b"a" * (1024 * 1024 + 1)
    resposta = enviar_exame(cliente, paciente, jornada, conteudo=grande)
    assert resposta.status_code == 413
    assert resposta.json()["detail"] == "Arquivo muito grande. O tamanho máximo é 1 MB."
    # Nada fica em disco
    assert _arquivos_em_disco(config_teste) == []


def test_arquivo_exatamente_no_limite_e_aceito(cliente, paciente, jornada, config_teste, monkeypatch):
    monkeypatch.setattr(config_teste, "tamanho_maximo_upload_mb", 1)
    resposta = enviar_exame(cliente, paciente, jornada, conteudo=b"a" * (1024 * 1024))
    assert resposta.status_code == 201


def test_requisicao_muito_grande_e_recusada_antes_de_ler_o_corpo(cliente, paciente, jornada, config_teste, monkeypatch):
    monkeypatch.setattr(config_teste, "tamanho_maximo_upload_mb", 1)
    resposta = enviar_exame(cliente, paciente, jornada, conteudo=b"a" * (3 * 1024 * 1024))
    assert resposta.status_code == 413


def test_arquivo_vazio_retorna_422(cliente, paciente, jornada):
    resposta = enviar_exame(cliente, paciente, jornada, conteudo=b"")
    assert resposta.status_code == 422


def test_envio_vinculado_marca_solicitacao_como_atendida(cliente, medico, paciente, jornada):
    for tipo in ("exame", "orientacao_profissional"):
        solicitacao = criar_solicitacao(cliente, medico, jornada, tipo=tipo)
        resposta = enviar_exame(cliente, paciente, jornada, solicitacao_id=solicitacao["id"])
        assert resposta.status_code == 201
        assert resposta.json()["solicitacao_id"] == solicitacao["id"]

    solicitacoes = cliente.get(f"/journeys/{jornada['id']}/requests", headers=paciente["headers"]).json()
    assert {s["status"] for s in solicitacoes} == {"atendida"}


def test_nao_vincula_envio_a_consulta_extra(cliente, medico, paciente, jornada):
    consulta_extra = criar_solicitacao(cliente, medico, jornada, tipo="consulta_extra")
    resposta = enviar_exame(cliente, paciente, jornada, solicitacao_id=consulta_extra["id"])
    assert resposta.status_code == 422


def test_nao_vincula_envio_a_solicitacao_ja_atendida(cliente, medico, paciente, jornada):
    solicitacao = criar_solicitacao(cliente, medico, jornada)
    enviar_exame(cliente, paciente, jornada, solicitacao_id=solicitacao["id"])
    resposta = enviar_exame(cliente, paciente, jornada, solicitacao_id=solicitacao["id"])
    assert resposta.status_code == 409


def test_terceiros_nao_enviam_exame(cliente, outro_paciente, jornada):
    assert enviar_exame(cliente, outro_paciente, jornada).status_code == 403


def test_medico_revisa_exame(cliente, medico, paciente, jornada):
    exame = enviar_exame(cliente, paciente, jornada).json()
    resposta = cliente.patch(
        f"/exams/{exame['id']}/review",
        json={"observacao_revisao": "Hemoglobina normal."},
        headers=medico["headers"],
    )
    assert resposta.status_code == 200
    revisado = resposta.json()
    assert revisado["status"] == "revisado"
    assert revisado["observacao_revisao"] == "Hemoglobina normal."
    assert revisado["revisado_em"] is not None


def test_paciente_nao_revisa_exame(cliente, paciente, jornada):
    exame = enviar_exame(cliente, paciente, jornada).json()
    resposta = cliente.patch(f"/exams/{exame['id']}/review", json={}, headers=paciente["headers"])
    assert resposta.status_code == 403


def test_outro_medico_nao_revisa_exame(cliente, outro_medico, paciente, jornada):
    exame = enviar_exame(cliente, paciente, jornada).json()
    resposta = cliente.patch(f"/exams/{exame['id']}/review", json={}, headers=outro_medico["headers"])
    assert resposta.status_code == 403


def test_download_do_arquivo(cliente, medico, paciente, jornada):
    exame = enviar_exame(cliente, paciente, jornada).json()
    url = f"/files/{exame['arquivo']['id']}/download"

    resposta = cliente.get(url, headers=medico["headers"])
    assert resposta.status_code == 200
    assert resposta.content == b"%PDF-1.4 conteudo de teste"
    assert resposta.headers["content-type"] == "application/pdf"
    assert "attachment" in resposta.headers["content-disposition"]
    assert "hemograma.pdf" in resposta.headers["content-disposition"]

    inline = cliente.get(url, params={"inline": True}, headers=paciente["headers"])
    assert inline.headers["content-disposition"].startswith("inline")


def test_download_exige_acesso_a_jornada(cliente, outro_medico, paciente, jornada):
    exame = enviar_exame(cliente, paciente, jornada).json()
    url = f"/files/{exame['arquivo']['id']}/download"
    assert cliente.get(url).status_code == 401
    assert cliente.get(url, headers=outro_medico["headers"]).status_code == 403
    assert cliente.get("/files/999/download", headers=paciente["headers"]).status_code == 404


def test_pasta_de_uploads_nao_e_publica(cliente, paciente, jornada, config_teste):
    enviar_exame(cliente, paciente, jornada)
    nome = next(config_teste.pasta_uploads.iterdir()).name
    for url in (f"/uploads/{nome}", f"/static/{nome}", f"/{nome}"):
        assert cliente.get(url).status_code == 404


def test_limite_tambem_e_verificado_durante_a_gravacao(config_teste, monkeypatch):
    """Sem o tamanho informado pelo upload, o limite é checado bloco a bloco ao gravar."""
    import io

    from fastapi import HTTPException, UploadFile

    from app.services.armazenamento import salvar_upload

    monkeypatch.setattr(config_teste, "tamanho_maximo_upload_mb", 1)
    upload = UploadFile(file=io.BytesIO(b"a" * (2 * 1024 * 1024)), filename="grande.pdf")
    assert upload.size is None

    with pytest.raises(HTTPException) as erro:
        salvar_upload(upload, jornada_id=1, usuario_id=1)
    assert erro.value.status_code == 413
    assert _arquivos_em_disco(config_teste) == []
