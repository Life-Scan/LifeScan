"""Edição (título e categoria) e exclusão de documentos.

Regras: o médico altera qualquer documento; o parceiro atribuído, só os próprios envios;
paciente e colaborador não alteram. Acompanhamento encerrado é somente leitura.
"""

from app.models.solicitacao import Solicitacao, StatusSolicitacao
from tests.conftest import abrir_sessao, criar_solicitacao, enviar_documento


def _status_solicitacao(solicitacao_id: int) -> str:
    sessao = abrir_sessao()
    try:
        return sessao.get(Solicitacao, solicitacao_id).status.value
    finally:
        sessao.close()


def _arquivos_em_disco(config) -> list:
    pasta = config.pasta_uploads
    return list(pasta.iterdir()) if pasta.exists() else []


def _encerrar(cliente, medico, acompanhamento):
    resposta = cliente.patch(
        f"/follow-ups/{acompanhamento['id']}/status", json={"status": "encerrado"}, headers=medico["headers"]
    )
    assert resposta.status_code == 200, resposta.text


# --- Edição ---------------------------------------------------------------------------------


def test_medico_edita_documento_de_outra_pessoa(cliente, medico, paciente, acompanhamento):
    documento = enviar_documento(cliente, paciente, acompanhamento).json()
    resposta = cliente.patch(
        f"/documents/{documento['id']}",
        json={"titulo": "  Hemograma de novembro  ", "categoria": "laudo"},
        headers=medico["headers"],
    )
    assert resposta.status_code == 200, resposta.text
    editado = resposta.json()
    assert editado["titulo"] == "Hemograma de novembro"
    assert editado["categoria"] == "laudo"
    # Arquivo, autor e status não mudam
    assert editado["arquivo"]["id"] == documento["arquivo"]["id"]
    assert editado["enviado_por"]["id"] == paciente["usuario"]["id"]
    assert editado["status"] == "enviado"


def test_edicao_parcial_mantem_o_resto(cliente, medico, acompanhamento):
    documento = enviar_documento(cliente, medico, acompanhamento, categoria="laudo").json()
    resposta = cliente.patch(f"/documents/{documento['id']}", json={"titulo": "Laudo final"}, headers=medico["headers"])
    assert resposta.status_code == 200
    assert resposta.json()["categoria"] == "laudo"


def test_edicao_mantem_a_revisao(cliente, medico, paciente, acompanhamento):
    documento = enviar_documento(cliente, paciente, acompanhamento).json()
    cliente.patch(f"/documents/{documento['id']}/review", json={"observacao_revisao": "Ok"}, headers=medico["headers"])
    resposta = cliente.patch(f"/documents/{documento['id']}", json={"titulo": "Outro título"}, headers=medico["headers"])
    assert resposta.json()["status"] == "revisado"
    assert resposta.json()["observacao_revisao"] == "Ok"


def test_titulo_invalido_retorna_422(cliente, medico, acompanhamento):
    documento = enviar_documento(cliente, medico, acompanhamento).json()
    url = f"/documents/{documento['id']}"
    assert cliente.patch(url, json={"titulo": "  a  "}, headers=medico["headers"]).status_code == 422
    assert cliente.patch(url, json={"titulo": "x" * 151}, headers=medico["headers"]).status_code == 422
    assert cliente.patch(url, json={"categoria": "receita"}, headers=medico["headers"]).status_code == 422


def test_parceiro_edita_o_proprio_envio(cliente, parceiro_atribuido, acompanhamento):
    documento = enviar_documento(cliente, parceiro_atribuido, acompanhamento, categoria="plano_alimentar").json()
    resposta = cliente.patch(
        f"/documents/{documento['id']}", json={"titulo": "Plano alimentar v2"}, headers=parceiro_atribuido["headers"]
    )
    assert resposta.status_code == 200
    assert resposta.json()["titulo"] == "Plano alimentar v2"


def test_parceiro_nao_edita_documento_de_outra_pessoa(cliente, paciente, parceiro_atribuido, acompanhamento):
    documento = enviar_documento(cliente, paciente, acompanhamento).json()
    resposta = cliente.patch(f"/documents/{documento['id']}", json={"titulo": "Mudado"}, headers=parceiro_atribuido["headers"])
    # 404: o parceiro nem enxerga os documentos de outras pessoas
    assert resposta.status_code == 404


def test_paciente_nao_edita_nem_o_proprio_envio(cliente, paciente, acompanhamento):
    documento = enviar_documento(cliente, paciente, acompanhamento).json()
    resposta = cliente.patch(f"/documents/{documento['id']}", json={"titulo": "Mudado"}, headers=paciente["headers"])
    assert resposta.status_code == 403


def test_colaborador_e_estranhos_nao_editam(cliente, medico, colaborador, outro_paciente, acompanhamento):
    documento = enviar_documento(cliente, medico, acompanhamento).json()
    url = f"/documents/{documento['id']}"
    assert cliente.patch(url, json={"titulo": "Mudado"}, headers=colaborador["headers"]).status_code == 403
    assert cliente.patch(url, json={"titulo": "Mudado"}, headers=outro_paciente["headers"]).status_code == 403
    assert cliente.patch(url, json={"titulo": "Mudado"}).status_code == 401


def test_parceiro_removido_nao_edita_mais(cliente, medico, parceiro_atribuido, acompanhamento):
    documento = enviar_documento(cliente, parceiro_atribuido, acompanhamento).json()
    remocao = cliente.delete(
        f"/follow-ups/{acompanhamento['id']}/partners/{parceiro_atribuido['usuario']['id']}", headers=medico["headers"]
    )
    assert remocao.status_code == 204
    resposta = cliente.patch(f"/documents/{documento['id']}", json={"titulo": "Mudado"}, headers=parceiro_atribuido["headers"])
    assert resposta.status_code == 403


def test_documento_inexistente_retorna_404(cliente, medico):
    assert cliente.patch("/documents/999", json={"titulo": "Mudado"}, headers=medico["headers"]).status_code == 404
    assert cliente.delete("/documents/999", headers=medico["headers"]).status_code == 404


def test_acompanhamento_encerrado_nao_permite_editar_nem_excluir(cliente, medico, acompanhamento):
    documento = enviar_documento(cliente, medico, acompanhamento).json()
    _encerrar(cliente, medico, acompanhamento)
    url = f"/documents/{documento['id']}"
    assert cliente.patch(url, json={"titulo": "Mudado"}, headers=medico["headers"]).status_code == 409
    assert cliente.delete(url, headers=medico["headers"]).status_code == 409


# --- Exclusão -------------------------------------------------------------------------------


def test_medico_exclui_documento_e_o_arquivo_some(cliente, medico, paciente, acompanhamento, config_teste):
    documento = enviar_documento(cliente, paciente, acompanhamento).json()
    assert len(_arquivos_em_disco(config_teste)) == 1

    resposta = cliente.delete(f"/documents/{documento['id']}", headers=medico["headers"])
    assert resposta.status_code == 204

    assert _arquivos_em_disco(config_teste) == []
    lista = cliente.get(f"/follow-ups/{acompanhamento['id']}/documents", headers=medico["headers"]).json()
    itens = lista["itens"] if isinstance(lista, dict) else lista
    assert itens == []
    assert cliente.get(f"/files/{documento['arquivo']['id']}/download", headers=medico["headers"]).status_code == 404


def test_parceiro_exclui_so_o_proprio_envio(cliente, paciente, parceiro_atribuido, acompanhamento):
    proprio = enviar_documento(cliente, parceiro_atribuido, acompanhamento).json()
    alheio = enviar_documento(cliente, paciente, acompanhamento).json()
    assert cliente.delete(f"/documents/{alheio['id']}", headers=parceiro_atribuido["headers"]).status_code == 404
    assert cliente.delete(f"/documents/{proprio['id']}", headers=parceiro_atribuido["headers"]).status_code == 204


def test_paciente_e_colaborador_nao_excluem(cliente, medico, paciente, colaborador, acompanhamento, config_teste):
    documento = enviar_documento(cliente, paciente, acompanhamento).json()
    assert cliente.delete(f"/documents/{documento['id']}", headers=paciente["headers"]).status_code == 403
    assert cliente.delete(f"/documents/{documento['id']}", headers=colaborador["headers"]).status_code == 403
    assert len(_arquivos_em_disco(config_teste)) == 1


def test_excluir_documento_reabre_a_solicitacao_atendida(cliente, medico, paciente, acompanhamento):
    solicitacao = criar_solicitacao(cliente, medico, acompanhamento, tipo="exame")
    documento = enviar_documento(cliente, paciente, acompanhamento, solicitacao_id=solicitacao["id"]).json()
    assert _status_solicitacao(solicitacao["id"]) == "atendida"

    assert cliente.delete(f"/documents/{documento['id']}", headers=medico["headers"]).status_code == 204
    assert _status_solicitacao(solicitacao["id"]) == "pendente"


def test_solicitacao_continua_atendida_se_outro_documento_a_atende(cliente, medico, paciente, acompanhamento):
    """A API só vincula envio a solicitação pendente, então o segundo vínculo é preparado no banco."""
    from app.models.documento import Documento

    solicitacao = criar_solicitacao(cliente, medico, acompanhamento, tipo="exame")
    primeiro = enviar_documento(cliente, paciente, acompanhamento, solicitacao_id=solicitacao["id"]).json()
    segundo = enviar_documento(cliente, paciente, acompanhamento).json()
    sessao = abrir_sessao()
    try:
        sessao.get(Documento, segundo["id"]).solicitacao_id = solicitacao["id"]
        sessao.commit()
    finally:
        sessao.close()

    assert cliente.delete(f"/documents/{primeiro['id']}", headers=medico["headers"]).status_code == 204
    assert _status_solicitacao(solicitacao["id"]) == "atendida"


def test_excluir_nao_reabre_solicitacao_cancelada(cliente, medico, paciente, acompanhamento):
    solicitacao = criar_solicitacao(cliente, medico, acompanhamento, tipo="exame")
    documento = enviar_documento(cliente, paciente, acompanhamento, solicitacao_id=solicitacao["id"]).json()
    sessao = abrir_sessao()
    try:
        sessao.get(Solicitacao, solicitacao["id"]).status = StatusSolicitacao.cancelada
        sessao.commit()
    finally:
        sessao.close()

    assert cliente.delete(f"/documents/{documento['id']}", headers=medico["headers"]).status_code == 204
    assert _status_solicitacao(solicitacao["id"]) == "cancelada"
