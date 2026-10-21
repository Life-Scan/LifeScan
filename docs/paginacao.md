# Paginação e carregamento do acompanhamento

## Problema corrigido

Antes, abrir o acompanhamento executava até sete buscas em paralelo e aguardava todas terminarem para mostrar qualquer conteúdo. A linha do tempo consultava e montava todos os registros, mesmo quando a pessoa só queria consultar a ficha.

Agora, o cabeçalho carrega independentemente e cada aba busca somente o próprio conteúdo. A atualização de 30 segundos mantém os dados já exibidos durante a atualização; abas fechadas não fazem polling. As requisições têm tempo limite de 20 segundos, e uma falha inicial no conteúdo oferece nova tentativa sem bloquear o restante do acompanhamento.

## Listas paginadas

As telas de contas (pacientes e parceiros, ativos e desativados), acompanhamentos, consultas, solicitações, documentos e linha do tempo usam páginas de 20 registros. Anterior e Próxima permitem acessar todos os registros.

As rotas de listagem aceitam `pagina` (a partir de 1) e `tamanho` (1 a 100; padrão 20). Quando `pagina` é informada, a resposta é:

```json
{
  "itens": [],
  "pagina": 1,
  "tamanho": 20,
  "total": 0,
  "paginas": 1
}
```

A contagem e os limites são aplicados no banco. Uma página além do fim retorna a última página válida, inclusive depois da desativação de uma conta. Sem `pagina`, o formato de lista anterior continua disponível para compatibilidade com seletores existentes e integrações.

Os filtros de situação e tipo de conta, categoria de documento e tipo e ordem dos eventos são aplicados antes da paginação. A linha do tempo usa `UNION ALL` de identificadores e datas no SQL e carrega os registros e relacionamentos completos apenas da página selecionada. A ordenação inclui identificadores para desempatar datas iguais.

`GET /follow-ups/{id}/summary` fornece as contagens globais de pendências usando agregações, sem baixar o histórico. O resumo respeita o tipo do usuário: parceiros e pacientes recebem somente a quantidade de solicitações destinadas a eles.

## Validação e limites

Os testes automatizados usam SQLite em memória com listas maiores que uma página, histórico com 150 eventos, filtros, ordenação, permissões e página vazia. Um teste verifica que apenas 20 consultas são materializadas ao pedir uma página do histórico. Os testes de interface usam API simulada para conferir histórico lento, erro isolado à aba, filtros e navegação.

Isso limita o volume das listas principais, mas não é uma medição da capacidade de produção do MySQL. Seletores auxiliares (paciente para novo acompanhamento, parceiros e solicitações pendentes para envio) e o painel ainda usam suas consultas específicas; com volumes muito grandes, devem ser avaliados também. Para dimensionar a instalação, medir latência, planos de consulta e concorrência no ambiente de destino. Nenhum teste de carga foi executado no banco real.
