"""Busca por nome ou email integrada aos filtros e à paginação de contas."""

import pytest

from tests.conftest import criar_conta


@pytest.mark.parametrize('busca', ['  LIMA  ', 'CARLOS@', 'exemplo.com'])
def test_busca_parcial_por_nome_ou_email(cliente, medico, busca):
    assert criar_conta(cliente, medico, 'paciente', 'Carlos Lima', 'carlos@exemplo.com').status_code == 201
    assert criar_conta(cliente, medico, 'paciente', 'Ana Souza', 'ana@outro.com').status_code == 201

    resposta = cliente.get('/users', params={'pagina': 1, 'busca': busca}, headers=medico['headers'])

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados['total'] == 1
    assert [conta['email'] for conta in dados['itens']] == ['carlos@exemplo.com']


def test_busca_respeita_tipo_e_situacao(cliente, medico):
    ativo = criar_conta(cliente, medico, 'paciente', 'Silva Ativo', 'ativo@exemplo.com').json()
    inativo = criar_conta(cliente, medico, 'paciente', 'Silva Inativo', 'inativo@exemplo.com').json()
    assert criar_conta(cliente, medico, 'parceiro', 'Silva Parceiro', 'parceiro@exemplo.com', 'Nutricionista').status_code == 201
    assert cliente.patch(f"/users/{inativo['id']}", json={'ativo': False}, headers=medico['headers']).status_code == 200

    for situacao, conta in ((True, ativo), (False, inativo)):
        resposta = cliente.get('/users', params={
            'pagina': 1, 'tipo': 'paciente', 'ativo': situacao, 'busca': 'silva',
        }, headers=medico['headers'])
        assert resposta.status_code == 200
        assert resposta.json()['total'] == 1
        assert [item['id'] for item in resposta.json()['itens']] == [conta['id']]


def test_busca_filtra_antes_de_paginar(cliente, medico):
    for numero in range(23):
        assert criar_conta(cliente, medico, 'paciente', f'Paciente {numero:02}', f'p{numero}@exemplo.com').status_code == 201
    alvo = criar_conta(cliente, medico, 'paciente', 'Zelia Encontrada', 'zelia@exemplo.com').json()
    pagina = cliente.get('/users', params={'pagina': 2}, headers=medico['headers']).json()
    assert alvo['id'] in [conta['id'] for conta in pagina['itens']]

    filtrada = cliente.get('/users', params={
        'pagina': 1, 'tamanho': 1, 'busca': 'encontrada',
    }, headers=medico['headers']).json()
    assert filtrada['total'] == 1
    assert filtrada['paginas'] == 1
    assert filtrada['itens'][0]['id'] == alvo['id']


def test_busca_vazia_inexistente_e_caracteres_literais(cliente, medico):
    conta = criar_conta(cliente, medico, 'paciente', 'Paciente 100% Teste', 'teste@exemplo.com').json()
    assert criar_conta(cliente, medico, 'paciente', 'Paciente Comum', 'comum@exemplo.com').status_code == 201
    for busca, quantidade in (('   ', 2), ('inexistente', 0), ('%', 1), ('_', 0)):
        resposta = cliente.get('/users', params={'pagina': 1, 'busca': busca}, headers=medico['headers'])
        assert resposta.status_code == 200
        assert resposta.json()['total'] == quantidade
        if busca == '%':
            assert resposta.json()['itens'][0]['id'] == conta['id']

    sem_paginacao = cliente.get('/users', params={'busca': '100%'}, headers=medico['headers'])
    assert sem_paginacao.status_code == 200
    assert [item['id'] for item in sem_paginacao.json()] == [conta['id']]


def test_busca_continua_restrita_ao_medico(cliente, paciente, parceiro):
    assert cliente.get('/users?busca=teste').status_code == 401
    for usuario in (paciente, parceiro):
        assert cliente.get('/users?busca=teste', headers=usuario['headers']).status_code == 403
