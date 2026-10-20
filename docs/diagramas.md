# LifeScan: diagramas

Diagramas em [Mermaid](https://mermaid.js.org), refletindo o sistema como está implementado.
O GitHub mostra os diagramas desenhados; as mesmas figuras estão em imagem na pasta
[`diagramas/`](diagramas/).

## Diagrama de classes

No modelo conceitual, Médico, Paciente e Parceiro são especializações de Usuário. No banco,
as três ficam em uma única tabela (`usuarios`), diferenciadas por `tipo_usuario`.

- `senha_hash` fica vazio até o primeiro acesso; até lá vale a senha provisória enviada por email.
- `definirSenha` só existe logo depois de entrar com a senha provisória.

![Diagrama de classes](diagramas/classes.png)

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
        +entrar(email, senha)
        +definirSenha(nova_senha)
        +pedirSenhaProvisoria()
    }
    note for Usuario "profissao é obrigatória para médico e parceiro"

    class Medico {
        +criarConta(tipo, nome, email, profissao)
        +reenviarAcesso(usuario)
        +ativarOuDesativar(usuario)
        +abrirJornada(paciente)
        +alterarPasso(jornada, passo)
        +encerrarOuReabrir(jornada)
        +manterFicha(paciente)
        +atribuirParceiro(jornada, parceiro)
        +registrarConsulta(jornada, dados)
        +criarSolicitacao(jornada, destinatario)
        +concluirOuCancelar(solicitacao)
        +revisarDocumento(documento, observacao)
    }
    class Paciente {
        +verJornada()
        +verFicha()
        +verPendencias()
        +enviarDocumento(jornada, arquivo)
    }
    class Parceiro {
        +listarPacientesAtribuidos()
        +verFicha(paciente)
        +verSolicitacoesParaMim()
        +enviarDocumento(jornada, arquivo)
    }

    class FichaPaciente {
        +int id
        +date data_nascimento
        +Sexo sexo
        +int altura_cm
        +decimal peso_kg
        +str diagnosticos
        +str alergias
        +str medicamentos_em_uso
        +str restricoes
        +str objetivos
        +str observacoes
        +datetime atualizado_em
        +idade() int
    }
    class Jornada {
        +int id
        +str titulo
        +str descricao
        +PassoJornada passo_atual
        +StatusJornada status
        +datetime criado_em
        +datetime atualizado_em
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
        +datetime criado_em
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
        +datetime atendida_em
        +datetime criado_em
        +vencida() bool
    }
    class Documento {
        +int id
        +CategoriaDocumento categoria
        +str titulo
        +StatusDocumento status
        +str observacao_revisao
        +datetime revisado_em
        +datetime criado_em
    }
    class Arquivo {
        +int id
        +str nome_original
        +str nome_armazenado
        +str tipo_mime
        +int tamanho_bytes
        +datetime criado_em
    }

    class TipoUsuario {
        medico
        paciente
        parceiro
    }
    <<enumeration>> TipoUsuario

    class PassoJornada {
        consulta
        exame
        retorno
    }
    <<enumeration>> PassoJornada

    class TipoSolicitacao {
        exame
        consulta_extra
        orientacao_profissional
        outro
    }
    <<enumeration>> TipoSolicitacao

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
    Solicitacao "0..*" --> "1" Usuario : destinatário
    Documento "0..*" --> "0..1" Solicitacao : atende
    Documento "1" --> "1" Arquivo
    Documento "0..*" --> "1" Usuario : enviado por
```

## Diagrama ER

Corresponde às tabelas criadas pelas migrações do Alembic.

![Diagrama ER](diagramas/er.png)

```mermaid
erDiagram
    USUARIOS {
        int id PK
        enum tipo_usuario "medico | paciente | parceiro"
        varchar nome
        varchar email UK
        varchar profissao "NULL só para paciente (CHECK)"
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
        date data_nascimento "NULL"
        enum sexo "masculino | feminino | outro"
        int altura_cm "NULL"
        decimal peso_kg "NULL"
        text diagnosticos "NULL"
        text alergias "NULL"
        text medicamentos_em_uso "NULL"
        text restricoes "NULL"
        text objetivos "NULL"
        text observacoes "NULL"
        datetime atualizado_em
    }
    JORNADAS {
        int id PK
        int medico_id FK
        int paciente_id FK,UK "uma jornada por paciente"
        varchar titulo
        text descricao "NULL"
        enum passo_atual "consulta | exame | retorno"
        enum status "ativa | encerrada"
        datetime criado_em
        datetime atualizado_em
    }
    JORNADA_PARCEIROS {
        int id PK
        int jornada_id FK "único junto com parceiro_id"
        int parceiro_id FK
        datetime criado_em
    }
    CONSULTAS {
        int id PK
        int jornada_id FK
        enum tipo "consulta | retorno"
        datetime data
        text anotacoes "NULL"
        datetime criado_em
    }
    PRESCRICOES {
        int id PK
        int consulta_id FK
        varchar descricao
        varchar dosagem "NULL"
        text instrucoes "NULL"
    }
    SOLICITACOES {
        int id PK
        int jornada_id FK
        int destinatario_id FK "paciente ou parceiro atribuído"
        enum tipo "exame | consulta_extra | orientacao_profissional | outro"
        text descricao
        datetime prazo
        enum status "pendente | atendida | cancelada"
        datetime atendida_em "NULL"
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
        text observacao_revisao "NULL"
        datetime revisado_em "NULL"
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
    JORNADAS ||--o{ ARQUIVOS : "guarda"
```

## Diagrama de casos de uso

O Mermaid não tem um tipo próprio para casos de uso; o fluxograma abaixo segue o mesmo formato.
O médico fica à esquerda; paciente e parceiro, à direita. O paciente não tem o UC20, e o parceiro
não tem o UC15 (ele não vê a linha do tempo, as consultas nem os documentos de outras pessoas).

![Diagrama de casos de uso](diagramas/casos-de-uso.png)

```mermaid
flowchart LR
    M["👤 Médico"]

    subgraph LifeScan
        direction TB

        subgraph Gestao["Gestão do tratamento (só o médico)"]
            direction TB
            UC04(["UC04 Criar conta de paciente ou parceiro"])
            UC05(["UC05 Reenviar acesso"])
            UC06(["UC06 Ativar / desativar conta"])
            UC07(["UC07 Abrir jornada"])
            UC08(["UC08 Alterar passo / encerrar jornada"])
            UC09(["UC09 Manter ficha do paciente"])
            UC10(["UC10 Atribuir parceiro à jornada"])
            UC11(["UC11 Registrar consulta e prescrições"])
            UC12(["UC12 Criar solicitação com prazo"])
            UC13(["UC13 Concluir / cancelar solicitação"])
            UC14(["UC14 Revisar documento"])
        end

        subgraph Comum["Uso do dia a dia"]
            direction TB
            UC01(["UC01 Entrar no sistema"])
            UC15(["UC15 Ver jornada e linha do tempo"])
            UC16(["UC16 Ver ficha do paciente"])
            UC17(["UC17 Enviar documento"])
            UC18(["UC18 Atender solicitação com um envio"])
            UC19(["UC19 Ver painel de pendências"])
            UC20(["UC20 Ver pacientes atribuídos"])
        end

        subgraph Senha["Primeiro acesso e senha"]
            direction TB
            UC02(["UC02 Definir senha no primeiro acesso"])
            UC03(["UC03 Recuperar senha esquecida"])
        end

        UC21(["Enviar email com a senha provisória"])
    end

    P["👤 Paciente"]
    R["👤 Parceiro"]
    E["✉️ Serviço de email"]

    M --- UC04 & UC05 & UC06 & UC07 & UC08 & UC09 & UC10 & UC11 & UC12 & UC13 & UC14
    M --- UC01 & UC15 & UC16 & UC17 & UC18 & UC19

    UC01 & UC15 & UC16 & UC17 & UC18 & UC19 --- P
    UC01 & UC16 & UC17 & UC18 & UC19 & UC20 --- R
    UC02 & UC03 --- P
    UC02 & UC03 --- R

    UC04 -.->|include| UC21
    UC05 -.->|include| UC21
    UC03 -.->|include| UC21
    UC21 --- E
```
