# LifeScan: diagramas

Diagramas em [Mermaid](https://mermaid.js.org). O GitHub mostra os diagramas desenhados; também
dá para colar o código em <https://mermaid.live>.

Os diagramas refletem o modelo implementado.

## Diagrama de classes

No modelo conceitual, Médico, Paciente e Parceiro são especializações de Usuário. No banco,
as três ficam em uma única tabela (`usuarios`), diferenciadas por `tipo_usuario`.

```mermaid
classDiagram
    direction LR

    class Usuario {
        +int id
        +TipoUsuario tipo_usuario
        +str nome
        +str email
        +str profissao
        +str senha_hash
        +str senha_provisoria_hash
        +datetime senha_provisoria_expira_em
        +bool deve_trocar_senha
        +bool ativo
        +datetime ultimo_login_em
        +datetime criado_em
        +autenticar(senha) bool
        +trocarSenha(atual, nova)
    }
    note for Usuario "profissao: obrigatória para médico e parceiro\nsenha_hash: vazio até o primeiro acesso"

    class Medico {
        +criarConta(tipo, nome, email, profissao)
        +reenviarAcesso(usuario)
        +ativarOuDesativar(usuario)
        +abrirJornada(paciente)
        +manterFicha(paciente)
        +atribuirParceiro(jornada, parceiro)
        +alterarPasso(jornada, passo)
        +registrarConsulta(jornada, dados)
        +criarSolicitacao(jornada, dados)
        +revisarDocumento(documento, observacao)
    }
    class Paciente {
        +verJornada()
        +verPendencias()
        +enviarDocumento(jornada, arquivo)
    }
    class Parceiro {
        +listarPacientesAtribuidos()
        +verFicha(paciente)
        +enviarDocumento(jornada, arquivo)
    }

    class FichaPaciente {
        +int id
        +date data_nascimento
        +str sexo
        +int altura_cm
        +decimal peso_kg
        +str diagnosticos
        +str alergias
        +str medicamentos_em_uso
        +str restricoes
        +str objetivos
        +str observacoes
        +datetime atualizado_em
    }
    class Jornada {
        +int id
        +str titulo
        +str descricao
        +PassoJornada passo_atual
        +StatusJornada status
        +datetime criado_em
    }
    class AtribuicaoParceiro {
        +int id
        +datetime criado_em
    }
    class Consulta {
        +int id
        +TipoConsulta tipo
        +datetime data
        +str anotacoes
    }
    class Prescricao {
        +int id
        +str descricao
        +str dosagem
        +str instrucoes
    }
    class Solicitacao {
        +int id
        +TipoSolicitacao tipo
        +str descricao
        +datetime prazo
        +StatusSolicitacao status
        +vencida() bool
    }
    class Documento {
        +int id
        +CategoriaDocumento categoria
        +str titulo
        +StatusDocumento status
        +str observacao_revisao
        +datetime revisado_em
    }
    class Arquivo {
        +int id
        +str nome_original
        +str nome_armazenado
        +str tipo_mime
        +int tamanho_bytes
    }

    class TipoUsuario {
        medico
        paciente
        parceiro
    }
    <<enumeration>> TipoUsuario

    class CategoriaDocumento {
        exame
        laudo
        plano_alimentar
        plano_treino
        orientacao
        outro
    }
    <<enumeration>> CategoriaDocumento

    Usuario <|-- Medico
    Usuario <|-- Paciente
    Usuario <|-- Parceiro

    Medico "1" --> "0..*" Usuario : cria a conta
    Paciente "1" --> "0..1" FichaPaciente : tem
    Medico "1" --> "0..*" Jornada : conduz
    Paciente "1" --> "0..1" Jornada : acompanhado em
    Jornada "1" *-- "0..*" AtribuicaoParceiro
    Parceiro "1" --> "0..*" AtribuicaoParceiro : atua em
    Jornada "1" *-- "0..*" Consulta
    Consulta "1" *-- "0..*" Prescricao
    Jornada "1" *-- "0..*" Solicitacao
    Jornada "1" *-- "0..*" Documento
    Documento "0..*" --> "0..1" Solicitacao : atende
    Documento "1" --> "1" Arquivo
    Usuario "1" --> "0..*" Documento : envia
    Usuario "1" --> "0..*" Solicitacao : destinatário
```

## Diagrama ER

```mermaid
erDiagram
    USUARIOS {
        int id PK
        enum tipo_usuario "medico | paciente | parceiro"
        varchar nome
        varchar email UK
        varchar profissao "NULL permitido só para paciente (CHECK)"
        varchar senha_hash "NULL até o primeiro acesso"
        varchar senha_provisoria_hash "NULL"
        datetime senha_provisoria_expira_em "NULL"
        boolean deve_trocar_senha
        boolean ativo
        datetime ultimo_login_em "NULL"
        datetime criado_em
    }
    FICHAS_PACIENTE {
        int id PK
        int paciente_id FK,UK "uma ficha por paciente"
        date data_nascimento
        enum sexo "masculino | feminino | outro"
        int altura_cm
        decimal peso_kg
        text diagnosticos
        text alergias
        text medicamentos_em_uso
        text restricoes
        text objetivos
        text observacoes
        datetime atualizado_em
    }
    JORNADAS {
        int id PK
        int medico_id FK
        int paciente_id FK,UK "uma jornada por paciente"
        varchar titulo
        text descricao
        enum passo_atual "consulta | exame | retorno"
        enum status "ativa | encerrada"
        datetime criado_em
        datetime atualizado_em
    }
    JORNADA_PARCEIROS {
        int id PK
        int jornada_id FK "UK junto com parceiro_id"
        int parceiro_id FK
        datetime criado_em
    }
    CONSULTAS {
        int id PK
        int jornada_id FK
        enum tipo "consulta | retorno"
        datetime data
        text anotacoes
        datetime criado_em
    }
    PRESCRICOES {
        int id PK
        int consulta_id FK
        varchar descricao
        varchar dosagem
        text instrucoes
    }
    SOLICITACOES {
        int id PK
        int jornada_id FK
        int destinatario_id FK "paciente ou parceiro atribuído"
        enum tipo "exame | consulta_extra | orientacao_profissional | outro"
        text descricao
        datetime prazo
        enum status "pendente | atendida | cancelada"
        datetime atendida_em
        datetime criado_em
    }
    DOCUMENTOS {
        int id PK
        int jornada_id FK
        int solicitacao_id FK "NULL"
        int enviado_por_id FK
        int arquivo_id FK
        enum categoria "exame | laudo | plano_alimentar | plano_treino | orientacao | outro"
        varchar titulo
        enum status "enviado | revisado"
        text observacao_revisao
        datetime revisado_em
        datetime criado_em
    }
    ARQUIVOS {
        int id PK
        int jornada_id FK
        varchar nome_original
        varchar nome_armazenado UK
        varchar tipo_mime
        bigint tamanho_bytes
        int enviado_por_id FK
        datetime criado_em
    }

    USUARIOS ||--o| FICHAS_PACIENTE : "tem (paciente)"
    USUARIOS ||--o{ JORNADAS : "conduz (médico)"
    USUARIOS ||--o| JORNADAS : "é acompanhado (paciente)"
    JORNADAS ||--o{ JORNADA_PARCEIROS : "tem"
    USUARIOS ||--o{ JORNADA_PARCEIROS : "atua (parceiro)"
    JORNADAS ||--o{ CONSULTAS : "tem"
    CONSULTAS ||--o{ PRESCRICOES : "tem"
    JORNADAS ||--o{ SOLICITACOES : "tem"
    USUARIOS ||--o{ SOLICITACOES : "é destinatário"
    JORNADAS ||--o{ DOCUMENTOS : "tem"
    SOLICITACOES |o--o{ DOCUMENTOS : "é atendida por"
    USUARIOS ||--o{ DOCUMENTOS : "envia"
    ARQUIVOS ||--|| DOCUMENTOS : "conteúdo"
```

## Diagrama de casos de uso

O Mermaid não tem um tipo próprio para casos de uso; o fluxograma abaixo segue o mesmo formato.

```mermaid
flowchart LR
    M["👤 Médico"]
    P["👤 Paciente"]
    R["👤 Parceiro"]
    E["✉️ Serviço de email"]

    subgraph LifeScan
        direction TB
        UC01(["UC01 Entrar no sistema"])
        UC02(["UC02 Definir senha no primeiro acesso"])
        UC03(["UC03 Recuperar senha esquecida"])
        UC04(["UC04 Alterar a própria senha"])

        UC05(["UC05 Criar conta de paciente"])
        UC06(["UC06 Criar conta de parceiro"])
        UC07(["UC07 Reenviar acesso"])
        UC08(["UC08 Ativar / desativar conta"])
        UC09(["UC09 Abrir jornada"])
        UC10(["UC10 Manter ficha do paciente"])
        UC11(["UC11 Atribuir parceiro à jornada"])
        UC12(["UC12 Alterar passo / encerrar jornada"])
        UC13(["UC13 Registrar consulta e prescrições"])
        UC14(["UC14 Criar solicitação com prazo"])
        UC15(["UC15 Revisar documento"])

        UC16(["UC16 Ver jornada e linha do tempo"])
        UC17(["UC17 Enviar documento"])
        UC18(["UC18 Ver painel de pendências"])
        UC19(["UC19 Ver pacientes atribuídos e suas fichas"])

        UC20(["Enviar email com a senha provisória"])
    end

    M --- UC01 & UC04 & UC05 & UC06 & UC07 & UC08 & UC09 & UC10 & UC11 & UC12 & UC13 & UC14 & UC15 & UC16 & UC17 & UC18
    P --- UC01 & UC02 & UC03 & UC04 & UC16 & UC17 & UC18
    R --- UC01 & UC02 & UC03 & UC04 & UC17 & UC18 & UC19

    UC05 -.->|include| UC20
    UC06 -.->|include| UC20
    UC07 -.->|include| UC20
    UC03 -.->|include| UC20
    UC20 --- E
```
