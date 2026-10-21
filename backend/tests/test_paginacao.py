"""Listas grandes são limitadas no SQL e respeitam os filtros e permissões."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import event

from app.models.consulta import Consulta, TipoConsulta
from app.models.jornada import Jornada
from app.models.solicitacao import Solicitacao, TipoSolicitacao, StatusSolicitacao
from app.models.usuario import Usuario, TipoUsuario
from tests.conftest import abrir_sessao, enviar_documento


def test_contas_paginadas_com_filtro_e_pagina_fora_do_intervalo(cliente, medico):
    sessao = abrir_sessao()
    sessao.add_all([Usuario(tipo_usuario=TipoUsuario.paciente, nome=f"Paciente {i:03}", email=f"p{i}@email.com", ativo=i < 45) for i in range(60)])
    sessao.commit()
    primeira = cliente.get('/users', params={"pagina": 1, "tipo": "paciente", "ativo": True}, headers=medico["headers"]).json()
    segunda = cliente.get('/users', params={"pagina": 2, "tipo": "paciente", "ativo": True}, headers=medico["headers"]).json()
    ultima = cliente.get('/users', params={"pagina": 99, "tipo": "paciente", "ativo": True}, headers=medico["headers"]).json()
    assert primeira["total"] == segunda["total"] == 45
    assert primeira["paginas"] == 3
    assert len(primeira["itens"]) == len(segunda["itens"]) == 20
    assert len(ultima["itens"]) == 5 and ultima["pagina"] == 3
    assert set(c["id"] for c in primeira["itens"]).isdisjoint(c["id"] for c in segunda["itens"])
    inativos = cliente.get('/users', params={"pagina": 1, "ativo": False}, headers=medico["headers"]).json()
    assert inativos["total"] == 15
    assert all(not c["ativo"] for c in inativos["itens"])


@pytest.mark.parametrize("parametros", [{"pagina": 0}, {"pagina": -1}, {"pagina": 1, "tamanho": 101}, {"pagina": 1, "tamanho": 0}])
def test_rejeita_paginacao_invalida(cliente, medico, parametros):
    assert cliente.get('/users', params=parametros, headers=medico["headers"]).status_code == 422


def test_jornadas_paginadas_nao_mostram_outros_pacientes(cliente, medico, paciente, jornada):
    sessao = abrir_sessao()
    for i in range(25):
        pessoa = Usuario(tipo_usuario=TipoUsuario.paciente, nome=f"Pessoa {i}", email=f"pessoa{i}@email.com")
        sessao.add(pessoa)
        sessao.flush()
        sessao.add(Jornada(medico_id=medico["usuario"]["id"], paciente_id=pessoa.id, titulo=f"Jornada {i}"))
    sessao.commit()
    pagina = cliente.get('/journeys', params={"pagina": 1}, headers=medico["headers"]).json()
    assert pagina["total"] == 26 and len(pagina["itens"]) == 20
    pessoal = cliente.get('/journeys', params={"pagina": 1}, headers=paciente["headers"]).json()
    assert pessoal["total"] == 1 and pessoal["itens"][0]["id"] == jornada["id"]


@pytest.fixture
def historico_grande(cliente, jornada, paciente):
    sessao = abrir_sessao()
    data = datetime(2026, 1, 1, 12)
    sessao.add_all([Consulta(jornada_id=jornada["id"], tipo=TipoConsulta.consulta, data=data, anotacoes=f"Consulta {i}") for i in range(85)])
    sessao.add_all([Solicitacao(jornada_id=jornada["id"], destinatario_id=paciente["usuario"]["id"], tipo=TipoSolicitacao.exame, descricao=f"Solicitação {i}", prazo=data + timedelta(days=10), criado_em=data, status=StatusSolicitacao.pendente if i < 35 else StatusSolicitacao.atendida) for i in range(65)])
    sessao.commit()
    return jornada


def test_timeline_limita_registros_carregados_e_ordena_antes_de_paginar(cliente, medico, historico_grande):
    carregados = []
    def ao_carregar(registro, contexto):
        carregados.append(registro.id)
    event.listen(Consulta, 'load', ao_carregar)
    try:
        resposta = cliente.get(f"/journeys/{historico_grande['id']}/timeline", params={"pagina": 2}, headers=medico["headers"])
        assert resposta.status_code == 200, resposta.text
        pagina = resposta.json()
        assert pagina["total"] == 150 and len(pagina["itens"]) == 20
        assert len(carregados) == 20
        assert [item["id"] for item in pagina["itens"]] == sorted(carregados)
        assert all(item["tipo"] == 'consulta' for item in pagina["itens"])
    finally:
        event.remove(Consulta, 'load', ao_carregar)
    recente = cliente.get(f"/journeys/{historico_grande['id']}/timeline", params={"pagina": 1, "tipos": "solicitacao", "recentes": True}, headers=medico["headers"]).json()
    assert recente["total"] == 65 and len(recente["itens"]) == 20
    assert all(item["tipo"] == 'solicitacao' for item in recente["itens"])
    ids = [item["id"] for item in recente["itens"]]
    assert ids == sorted(ids, reverse=True)


def test_consultas_solicitacoes_e_contagens_globais(cliente, medico, paciente, historico_grande):
    base = f"/journeys/{historico_grande['id']}"
    consultas = cliente.get(base + '/consultations', params={"pagina": 5}, headers=medico["headers"]).json()
    assert consultas["total"] == 85 and len(consultas["itens"]) == 5
    solicitacoes = cliente.get(base + '/requests', params={"pagina": 2, "status": "pendente"}, headers=medico["headers"]).json()
    assert solicitacoes["total"] == 35 and len(solicitacoes["itens"]) == 15
    resumo = cliente.get(base + '/summary', headers=paciente["headers"]).json()
    assert resumo == {"solicitacoes": 35, "documentos": 0}


def test_paginacao_de_documentos_e_permissoes_de_parceiro(cliente, medico, paciente, parceiro_atribuido, jornada):
    for usuario in (paciente, parceiro_atribuido):
        for categoria in ('exame', 'laudo'):
            assert enviar_documento(cliente, usuario, jornada, categoria=categoria).status_code == 201
    url = f"/journeys/{jornada['id']}/documents"
    resposta = cliente.get(url, params={"pagina": 1, "tamanho": 1, "categoria": "laudo"}, headers=parceiro_atribuido["headers"])
    assert resposta.status_code == 200, resposta.text
    pagina = resposta.json()
    assert pagina["total"] == 1 and len(pagina["itens"]) == 1
    assert pagina["itens"][0]["enviado_por"]["id"] == parceiro_atribuido["usuario"]["id"]
    assert cliente.get(f"/journeys/{jornada['id']}/timeline?pagina=1", headers=parceiro_atribuido["headers"]).status_code == 403


def test_paginacao_vazia(cliente, medico):
    pagina = cliente.get('/users?pagina=1', headers=medico["headers"]).json()
    assert pagina == {"itens": [], "pagina": 1, "tamanho": 20, "total": 0, "paginas": 1}
