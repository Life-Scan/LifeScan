# LifeScan: especificação e decisões

O principal objetivo do LifeScan é **centralizar os dados do paciente para ajudar o trabalho
do médico**. O tratamento é organizado como um acompanhamento: consultas, prescrições, solicitações
com prazo, documentos e uma linha do tempo.

## Tipos de usuário

| Tipo | Como a conta é criada | O que faz |
|---|---|---|
| **Médico** | Por script, na instalação. Existe um único médico. | Administra tudo: cria contas, abre acompanhamentos, registra consultas, cria solicitações, revisa documentos. |
| **Paciente** | Pelo médico, com o email informado na consulta. | Vê o próprio acompanhamento e as pendências, envia exames e documentos. |
| **Parceiro** | Pelo médico, com nome, email e profissão. | Profissional que colabora no tratamento (nutricionista, fisioterapeuta…): envia documentos da sua área. |

- **Não existe cadastro público.** Os dados de acesso seguem por email, com uma senha
  provisória; no primeiro login a pessoa define a própria senha.
- **O sistema não depende de o paciente (ou parceiro) aceitar o acesso.** Assim que a conta
  existe, o médico já trabalha no acompanhamento.
- Uma única tabela `usuarios`, com `tipo_usuario`. A `profissao` é obrigatória para médico
  (fixa: "Médico") e parceiro, e não se aplica ao paciente.

## Requisitos funcionais

| Código | Descrição | Situação |
|---|---|---|
| RF01 | O médico é criado por um script de instalação; não existe cadastro público. | Implementado |
| RF02 | Usuários com conta ativa entram com email e senha. | Implementado |
| RF03 | O médico cria a conta de um paciente informando nome e email. | Implementado |
| RF04 | O médico cria a conta de um parceiro informando nome, email e profissão. | Implementado |
| RF05 | Os dados de acesso são enviados por email, com uma senha provisória que expira. | Implementado |
| RF06 | No primeiro acesso, a pessoa define a própria senha antes de usar o sistema. | Implementado |
| RF07 | O médico reenvia o acesso (nova senha provisória) e vê quem ainda não entrou. | Implementado |
| RF08 | O médico altera o nome e o email das contas, e a profissão dos parceiros; o email continua único. | Implementado |
| RF09 | O médico ativa e desativa contas; uma conta desativada não entra no sistema. | Implementado |
| RF10 | O médico exclui definitivamente um paciente desativado que não tenha acompanhamento nem histórico, liberando o email. | Implementado |
| RF11 | "Esqueci minha senha" envia uma nova senha provisória por email, sem invalidar a senha atual. | Implementado |
| RF12 | Não há troca de senha dentro do sistema; quem quiser trocar usa "esqueci minha senha". | Implementado |
| RF13 | Só o médico abre o acompanhamento de um paciente, e cada paciente tem um único acompanhamento. | Implementado |
| RF14 | O médico altera o passo atual (`consulta` → `exame` → `retorno`). | Implementado |
| RF15 | O médico encerra e reabre o acompanhamento; encerrado, ele fica somente para leitura. | Implementado |
| RF16 | O médico mantém a anamnese do paciente (nascimento, sexo, altura, peso, diagnósticos, alergias, medicamentos, restrições, objetivos, observações); ela continua editável com o acompanhamento encerrado. | Implementado |
| RF17 | O médico atribui parceiros ao acompanhamento e os remove. | Implementado |
| RF18 | O médico registra consultas e retornos, com prescrições. | Implementado |
| RF19 | O médico cria solicitações com prazo (exame, consulta extra, orientação profissional, outro), destinadas ao paciente ou a um parceiro atribuído. | Implementado |
| RF20 | O médico marca uma solicitação como atendida ou a cancela. | Implementado |
| RF21 | O paciente vê as consultas extras marcadas pelo médico como lembrete. | Implementado |
| RF22 | O médico, o paciente e o parceiro atribuído enviam documentos com categoria (exame, laudo, plano alimentar, plano de treino, orientação, outro). | Implementado |
| RF23 | Quem tem acesso visualiza os documentos no navegador e baixa os arquivos. | Implementado |
| RF24 | Um documento vinculado a uma solicitação pendente marca a solicitação como atendida; cada pessoa só atende as solicitações destinadas a ela (o médico, qualquer uma). | Implementado |
| RF25 | O médico revisa documentos (status + observação) e pode revisar de novo. | Implementado |
| RF26 | O acompanhamento tem uma linha do tempo unificada, em ordem cronológica, com filtro por tipo e opção de inverter a ordem. | Implementado |
| RF27 | Cada tipo de usuário tem um painel de pendências; o do médico mostra as solicitações vencidas e as que vencem nos próximos dias. | Implementado |
| RF28 | A página do acompanhamento mostra nas abas a quantidade de pendências, contando para paciente e parceiro só o que cabe a eles. | Implementado |
| RF29 | O parceiro vê a anamnese dos pacientes atribuídos, as solicitações destinadas a ele e os próprios envios. | Implementado |
| RF30 | O paciente vê o próprio acompanhamento: anamnese, consultas, solicitações (inclusive as destinadas a parceiros), documentos e linha do tempo. | Implementado |

Removidos em relação à primeira versão: cadastro público, vínculo médico-paciente por busca de
email e o chat entre médico e paciente.

## Requisitos não funcionais

| Código | Descrição |
|---|---|
| RNF01 | Uploads só de `pdf, png, jpg, jpeg, webp, dcm, txt`, até 30 MB (configurável), validados no backend e no frontend. |
| RNF02 | Persistência em MySQL 8, com migrações Alembic que preservam os dados. |
| RNF03 | Controle de acesso por `tipo_usuario` (`medico` / `paciente` / `parceiro`). |
| RNF04 | O acompanhamento só é acessado pelo médico e pelo paciente dono, com conta ativa; o parceiro atribuído acessa apenas a anamnese, as solicitações destinadas a ele e os próprios envios. |
| RNF05 | O download de arquivos é autenticado e verifica o acesso ao acompanhamento. |
| RNF06 | As páginas se atualizam por polling a cada 30 s, só no conteúdo aberto e com pausa quando a aba do navegador está oculta. |
| RNF07 | As listas principais são paginadas no servidor: 20 registros por página (até 100), com filtros e contagem aplicados no banco. |
| RNF08 | A página do acompanhamento carrega o cabeçalho e cada aba de forma independente; as requisições têm tempo limite de 20 s. |
| RNF09 | Backend em FastAPI e frontend em React + Vite. |
| RNF10 | CORS com as origens definidas no `.env`. |
| RNF11 | Senhas com bcrypt; JWT HS256 com validade de 480 min (configurável). |
| RNF12 | A senha provisória é gerada pelo sistema e só o hash fica no banco; ela expira em 7 dias (conta nova) ou 60 min (redefinição), configurável. |
| RNF13 | Envio de email configurável no `.env`: modo "console" (mostra o email no terminal da API) ou "smtp" (STARTTLS ou SSL, com autenticação). |
| RNF14 | "Esqueci minha senha" responde igual para email existente ou não. |
| RNF15 | Datas gravadas em UTC com microssegundos; a API devolve as datas com fuso explícito. |
| RNF16 | Interface, mensagens de erro, código, tabelas e JSON em português; caminhos HTTP e variáveis do `.env` em inglês. |

## Decisões tomadas

### Convenções de código
- Nomes de classes, funções, variáveis, comentários, docstrings, tabelas, colunas e campos JSON em português.
- Termos técnicos sem boa tradução continuam em inglês (`router`, `schema`, `token`, `upload`), assim como nomes de pastas.
- **Rotas HTTP mantêm os caminhos em inglês** (`/auth/login`, `/follow-ups/{id}/timeline`...).
- Variáveis do `.env` em inglês (`DATABASE_URL`, `JWT_SECRET`...).
- Datas gravadas em UTC sem fuso, com microssegundos (`DATETIME(6)`); a API devolve com fuso explícito (`...Z`).

### Contas e senhas
- **Senha provisória por email** (escolha do projeto): o email leva o login e uma senha provisória;
  entrar com ela liga `deve_trocar_senha`, e o backend bloqueia todas as rotas exceto `/auth/me` e
  `/auth/set-password` até a pessoa definir a senha.
- **Definir a senha só existe nesse momento** (`POST /auth/set-password`, apenas `nova_senha`): a
  pessoa acabou de provar que tem a provisória, então ela não é pedida de novo. Fora disso a rota
  responde 403. A opção "alterar senha" foi removida por não fazer sentido no fluxo; o caminho
  para trocar é "esqueci minha senha".
- A senha provisória convive com a definitiva: pedir "esqueci minha senha" **não invalida a senha
  atual**, para que ninguém consiga trancar a conta de outra pessoa só sabendo o email.
- Uma nova senha provisória substitui a anterior.
- Conta desativada: o login é recusado e os tokens já emitidos deixam de valer.
- O médico não é administrado pelas rotas `/users`; a senha dele é redefinida por `scripts.criar_medico`.
- O médico pode alterar o email de uma conta; se o email já pertence a outra conta, a alteração é recusada (409).
- **Excluir conta** existe só para paciente desativado sem acompanhamento, anamnese, envios ou solicitações
  vinculados; com histórico, o caminho é manter a conta desativada (ou reativá-la). A exclusão libera o email.
- Envio de email em `app/services/email.py`: modo `console` em desenvolvimento e modo `smtp` para envio real
  (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_TLS`, `SMTP_SSL`); `scripts/testar_smtp.py` testa a configuração.

### Acompanhamentos
- **Um único médico** no sistema; sem tabela de vínculos. Preparar o sistema para vários médicos
  não é objetivo no momento.
- **Um paciente tem apenas um acompanhamento** (`acompanhamentos.paciente_id` é único).
- O acompanhamento pode ser aberto e usado antes do primeiro acesso do paciente.
- Paciente desativado perde o acesso; o médico continua vendo o acompanhamento.
- Acompanhamento `encerrado` é somente leitura (escritas retornam 409); o médico pode reabri-lo.

### Anamnese do paciente e parceiros
- A anamnese é um resumo clínico mantido pelo médico, com todos os campos opcionais: nascimento, sexo,
  altura, peso, diagnósticos, alergias, medicamentos em uso, restrições, objetivos e observações.
  A idade é calculada. Salvar substitui a anamnese inteira.
- Uma anamnese por paciente (`anamneses.paciente_id` é único), acessada pelo acompanhamento.
  Continua editável com o acompanhamento encerrado, porque descreve o paciente e não o tratamento.
- O paciente lê a própria anamnese; só o médico edita.
- O médico atribui parceiros ao acompanhamento (`acompanhamento_parceiros`). Remover a atribuição apaga a linha e
  tira o acesso; os documentos que o parceiro enviou permanecem no acompanhamento.
- **O parceiro atribuído vê** os dados básicos do acompanhamento, a anamnese do paciente, as solicitações
  destinadas a ele e os próprios envios (com a revisão do médico). **Não vê** consultas, prescrições,
  solicitações de outras pessoas, linha do tempo, a lista de parceiros nem os documentos de outras
  pessoas, e só baixa os arquivos que enviou.
- Paciente e parceiro podem ser trabalhados pelo médico antes do primeiro acesso deles.

### Solicitações e documentos
- **Consulta extra** é um lembrete do médico para o paciente: o paciente só visualiza.
  O médico marca a solicitação como atendida (`PATCH /requests/{id}/complete`) ou a cancela.
- Solicitações só podem ser criadas com prazo no futuro. Vencida = `pendente` com prazo no passado (calculado).
- "Próxima do prazo" = vence em até `DUE_SOON_DAYS` dias (padrão 3).
- Os envios se chamam **documentos** e têm categoria: `exame`, `laudo`, `plano_alimentar`,
  `plano_treino`, `orientacao`, `outro` (as rotas são `/documents`).
- Toda solicitação tem um **destinatário**: o paciente do acompanhamento (padrão) ou um parceiro atribuído.
  A consulta extra só pode ser destinada ao paciente.
- Enviar um documento vinculado a uma solicitação `exame` ou `orientacao_profissional` marca a
  solicitação como `atendida`. Paciente e parceiro só atendem as solicitações destinadas a eles;
  o médico pode atender qualquer uma (ex.: recebeu o documento em mãos).
- O paciente vê todas as solicitações do próprio acompanhamento, inclusive as destinadas a parceiros, mas o
  painel dele só conta as que cabem a ele. O painel do médico acompanha todas.
- Se um parceiro é removido do acompanhamento, as solicitações destinadas a ele continuam visíveis ao médico,
  que pode cancelá-las.
- A tabela `arquivos` guarda `acompanhamento_id`, para o download verificar o acesso diretamente.
- Uploads gravados em blocos no disco; acima do limite retorna 413; extensão não permitida retorna 415.

### Linha do tempo e painel
- Linha do tempo: `{tipo, id, data, resumo, dados}`, com `tipo` em `consulta`, `documento`, `solicitacao`.
  A data de uma consulta é a data em que ela aconteceu; dos demais eventos, o momento da criação.
- O painel considera só acompanhamentos ativos. Documentos enviados pelo próprio médico não entram como
  "aguardando revisão". No painel do paciente, consultas extras aparecem em uma lista separada.

### Frontend
- React + Vite em JavaScript, React Router, Axios; estilos com CSS Modules; ícones `lucide-react`.
- Menu lateral em telas largas e barra no topo em telas estreitas.
- **Pacientes e parceiros ficam em uma única tela** (`/usuarios`): o tipo é escolhido no formulário
  e as listas aparecem em seções separadas.
- Confirmações (desativar conta, encerrar acompanhamento, cancelar solicitação, remover parceiro) usam uma
  janela própria (`useConfirmar`), não o `window.confirm` do navegador.
- A linha do tempo é montada a partir de `dados` de cada evento, com etiquetas de status.
- O hook de polling se chama `useAtualizacaoPeriodica(buscar, 30000)`.
- O acompanhamento carrega o cabeçalho independentemente e busca apenas a aba selecionada; o polling atualiza somente o conteúdo aberto.
- As listas principais usam paginação no servidor, com 20 registros por página. Filtros de histórico e categoria são aplicados antes de limitar os resultados. Detalhes em [paginacao.md](paginacao.md).
- Downloads usam o token: o arquivo é baixado como blob e aberto ou salvo pelo navegador.
- A aba ativa do acompanhamento fica na URL (`/acompanhamentos/3?aba=documentos`).

## Próximas fases

| Fase | Conteúdo |
|---|---|
| **9. Endurecimento** | Limite de tentativas de login e de pedidos de senha, testes cobrindo os três tipos de usuário. |
