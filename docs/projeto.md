# LifeScan: especificação e decisões

O principal objetivo do LifeScan é **centralizar os dados do paciente para ajudar o trabalho
do médico**. O tratamento é organizado como uma jornada: consultas, prescrições, solicitações
com prazo, documentos e uma linha do tempo.

## Tipos de usuário

| Tipo | Como a conta é criada | O que faz |
|---|---|---|
| **Médico** | Por script, na instalação. Existe um único médico. | Administra tudo: cria contas, abre jornadas, registra consultas, cria solicitações, revisa documentos. |
| **Paciente** | Pelo médico, com o email informado na consulta. | Vê a própria jornada e as pendências, envia exames e documentos. |
| **Parceiro** | Pelo médico, com nome, email e profissão. | Profissional que colabora no tratamento (nutricionista, fisioterapeuta…): envia documentos da sua área. |

- **Não existe cadastro público.** Os dados de acesso seguem por email, com uma senha
  provisória; no primeiro login a pessoa define a própria senha.
- **O sistema não depende de o paciente (ou parceiro) aceitar o acesso.** Assim que a conta
  existe, o médico já trabalha na jornada.
- Uma única tabela `usuarios`, com `tipo_usuario`. A `profissao` é obrigatória para médico
  (fixa: "Médico") e parceiro, e não se aplica ao paciente.

## Requisitos funcionais

| Código | Descrição | Situação |
|---|---|---|
| RF01 | O médico é criado por script de instalação; não existe cadastro público. | Implementado |
| RF02 | Login de usuários ativos com email e senha. | Implementado |
| RF03 | O médico cria a conta de um paciente informando nome e email. | Implementado |
| RF04 | O médico cria a conta de um parceiro informando nome, email e profissão. | Implementado |
| RF05 | Os dados de acesso são enviados por email, com senha provisória que expira. | Implementado (email em modo console) |
| RF06 | No primeiro acesso, a troca da senha provisória é obrigatória. | Implementado |
| RF07 | O médico reenvia o acesso (nova senha provisória) e vê quem ainda não entrou. | Implementado |
| RF08 | O médico ativa e desativa contas; conta desativada não entra no sistema. | Implementado |
| RF09 | "Esqueci minha senha": nova senha provisória por email, sem invalidar a atual. | Implementado |
| RF10 | Qualquer usuário altera a própria senha. | Implementado |
| RF11 | Somente o médico abre a jornada de um paciente; cada paciente tem uma única jornada. | Implementado |
| RF12 | O médico altera o passo atual (`consulta`/`exame`/`retorno`) e encerra ou reabre a jornada. | Implementado |
| RF13 | O médico registra consultas e retornos com prescrições. | Implementado |
| RF14 | O médico cria solicitações com prazo. | Implementado (destinatário parceiro: pendente) |
| RF15 | O paciente vê as consultas extras marcadas pelo médico, como lembrete. | Implementado |
| RF16 | Médico, paciente e parceiro atribuído enviam exames e documentos. | Implementado (categorias: pendente) |
| RF17 | Documento vinculado a uma solicitação pendente marca a solicitação como atendida. | Implementado |
| RF18 | O médico revisa documentos (status + observação). | Implementado |
| RF19 | Linha do tempo unificada da jornada, em ordem cronológica e com filtro por tipo. | Implementado |
| RF20 | Painel de pendências por tipo de usuário. | Implementado (pendências do parceiro: pendente) |
| RF21 | O médico mantém a ficha do paciente (dados clínicos resumidos). | Implementado |
| RF22 | O médico atribui parceiros à jornada de um paciente. | Implementado |
| RF23 | O parceiro vê a ficha dos pacientes atribuídos, as solicitações destinadas a ele e os próprios envios. | Implementado (solicitações destinadas: pendente) |

Removidos em relação à primeira versão: cadastro público, vínculo médico-paciente por busca de
email e o chat entre médico e paciente.

## Requisitos não funcionais

| Código | Descrição |
|---|---|
| RNF01 | Uploads só de `pdf, png, jpg, jpeg, webp, dcm, txt`, até 30 MB, validados no backend e no frontend. |
| RNF02 | Persistência em MySQL, com migrações Alembic. |
| RNF03 | Controle de acesso por `tipo_usuario` (`medico` / `paciente` / `parceiro`). |
| RNF04 | Atualização das páginas por polling a cada 30 s, pausado com a aba oculta. |
| RNF05 | Backend em FastAPI; frontend em React + Vite. |
| RNF06 | CORS com origens vindas do `.env`. |
| RNF07 | Senhas com bcrypt; JWT HS256 com validade de 480 min. |
| RNF08 | Acesso à jornada: o médico e o paciente dono, com conta ativa; o parceiro atribuído, apenas à ficha e aos próprios envios. |
| RNF09 | Senha provisória gerada pelo sistema; no banco fica só o hash; expira em 7 dias (conta nova) ou 60 min (redefinição), configurável. |
| RNF10 | Envio de email configurável; em desenvolvimento, modo "console" (mostra o email no terminal da API). |
| RNF11 | "Esqueci minha senha" responde igual para email existente ou não. |
| RNF12 | Interface e mensagens de erro em português; código com nomes em português. |

## Decisões tomadas

### Convenções de código
- Nomes de classes, funções, variáveis, comentários, docstrings, tabelas, colunas e campos JSON em português.
- Termos técnicos sem boa tradução continuam em inglês (`router`, `schema`, `token`, `upload`), assim como nomes de pastas.
- **Rotas HTTP mantêm os caminhos em inglês** (`/auth/login`, `/journeys/{id}/timeline`...).
- Variáveis do `.env` em inglês (`DATABASE_URL`, `JWT_SECRET`...).
- Datas gravadas em UTC sem fuso, com microssegundos (`DATETIME(6)`); a API devolve com fuso explícito (`...Z`).

### Contas e senhas
- **Senha provisória por email** (escolha do projeto): o email leva o login e uma senha provisória;
  entrar com ela liga `deve_trocar_senha`, e o backend bloqueia todas as rotas exceto `/auth/me` e
  `/auth/change-password` até a troca.
- A senha provisória convive com a definitiva: pedir "esqueci minha senha" **não invalida a senha
  atual**, para que ninguém consiga trancar a conta de outra pessoa só sabendo o email.
- Uma nova senha provisória substitui a anterior.
- Conta desativada: o login é recusado e os tokens já emitidos deixam de valer.
- O médico não é administrado pelas rotas `/users`; a senha dele é redefinida por `scripts.criar_medico`.
- Envio real de email (Gmail/Outlook por SMTP) fica para depois; o ponto de troca é `app/services/email.py`.

### Jornadas
- **Um único médico** no sistema; sem tabela de vínculos. Preparar o sistema para vários médicos
  não é objetivo no momento.
- **Um paciente tem apenas uma jornada** (`jornadas.paciente_id` é único).
- A jornada pode ser aberta e usada antes do primeiro acesso do paciente.
- Paciente desativado perde o acesso; o médico continua vendo a jornada.
- Jornada `encerrada` é somente leitura (escritas retornam 409); o médico pode reabri-la.

### Ficha do paciente e parceiros
- A ficha é um resumo clínico mantido pelo médico, com todos os campos opcionais: nascimento, sexo,
  altura, peso, diagnósticos, alergias, medicamentos em uso, restrições, objetivos e observações.
  A idade é calculada. Salvar substitui a ficha inteira.
- Uma ficha por paciente (`fichas_paciente.paciente_id` é único), acessada pela jornada.
  Continua editável com a jornada encerrada, porque descreve o paciente e não o tratamento.
- O paciente lê a própria ficha; só o médico edita.
- O médico atribui parceiros à jornada (`jornada_parceiros`). Remover a atribuição apaga a linha e
  tira o acesso; os documentos que o parceiro enviou permanecem na jornada.
- **O parceiro atribuído vê** os dados básicos da jornada, a ficha do paciente e os próprios envios
  (com a revisão do médico). **Não vê** consultas, prescrições, solicitações, linha do tempo, a lista
  de parceiros nem os documentos de outras pessoas, e só baixa os arquivos que enviou.
- Paciente e parceiro podem ser trabalhados pelo médico antes do primeiro acesso deles.

### Solicitações e documentos
- **Consulta extra** é um lembrete do médico para o paciente: o paciente só visualiza.
  O médico marca a solicitação como atendida (`PATCH /requests/{id}/complete`) ou a cancela.
- Solicitações só podem ser criadas com prazo no futuro. Vencida = `pendente` com prazo no passado (calculado).
- "Próxima do prazo" = vence em até `DUE_SOON_DAYS` dias (padrão 3).
- Enviar um exame vinculado a uma solicitação `exame` ou `orientacao_profissional` marca a solicitação como `atendida`.
- A tabela `arquivos` guarda `jornada_id`, para o download verificar o acesso diretamente.
- Uploads gravados em blocos no disco; acima do limite retorna 413; extensão não permitida retorna 415.

### Linha do tempo e painel
- Linha do tempo: `{tipo, id, data, resumo, dados}`, com `tipo` em `consulta`, `exame`, `solicitacao`.
  A data de uma consulta é a data em que ela aconteceu; dos demais eventos, o momento da criação.
- O painel considera só jornadas ativas. Exames enviados pelo próprio médico não entram como
  "aguardando revisão". No painel do paciente, consultas extras aparecem em uma lista separada.

### Frontend
- React + Vite em JavaScript, React Router, Axios; estilos com CSS Modules.
- O hook de polling se chama `useAtualizacaoPeriodica(buscar, 30000)`.
- Downloads usam o token: o arquivo é baixado como blob e aberto ou salvo pelo navegador.
- A aba ativa da jornada fica na URL (`/jornadas/3?aba=exames`).

## Próximas fases

| Fase | Conteúdo |
|---|---|
| **8. Documentos** | `exames` vira `documentos` com categoria (exame, laudo, plano alimentar, plano de treino, orientação, outro). Solicitação com destinatário (paciente ou parceiro): o parceiro passa a ver e atender as solicitações destinadas a ele, e elas entram no painel dele. |
| **9. Endurecimento** | Limite de tentativas de login e de pedidos de senha, envio real de email por SMTP, testes cobrindo os três tipos de usuário. |
