# Dataset — fotos de documentos

Conteúdo gerado por `scripts/gerar_dataset.py` (semente fixa `42`):

- `fotos/treino/<classe>/` — 28 fotos por classe (70%), usadas na calibração
- `fotos/teste/<classe>/` — 12 fotos por classe (30%), usadas só na avaliação
- `rotulos.csv` — índice com `arquivo`, `classe` e `conjunto`

São **200 imagens**, com 40 por classe e divisão de 28 para treino e 12 para
teste por classe (140 para calibração e 60 para avaliação):

| Classe | Característica |
|---|---|
| `boa` | Página nítida, com variações leves de brilho e contraste |
| `borrada` | Desfoque gaussiano de raio variável |
| `iluminacao` | Subexposição ou superexposição |
| `baixa_resolucao` | Página reduzida a 300×400 px ou documento distante |
| `torta` | Página girada entre 10° e 25°, nos dois sentidos |

Na classe `baixa_resolucao`, o segundo caso usa uma página de 560×747 px,
centralizada em uma foto de 1600×2133 px: o documento ocupa 35% da largura.
A escolha entre os dois casos usa o gerador aleatório com semente `42`.
O fundo desse caso e as bordas de `torta` usam cinza-claro de intensidade
205, evitando que essas degradações sejam confundidas com foto escura.

## Origem

Dados **sintéticos**, desenhados pelo próprio projeto: páginas de documento
com texto simulado (sem conteúdo real) e degradações aplicadas por código —
desfoque gaussiano, sub/superexposição, redução de resolução, distância e
rotação. Nenhum dado
pessoal ou sensível, nenhuma imagem de terceiros.

## Como regenerar

```powershell
ai-model\.venv\Scripts\python ai-model\scripts\gerar_dataset.py
```

## Fotos reais (opcional)

A equipe pode acrescentar fotos próprias de documentos genéricos — sem
rostos e sem dados pessoais — seguindo a mesma divisão treino/teste e
atualizando `rotulos.csv`. Depois é só rodar `scripts/calibrar.py` de novo.

As imagens e o índice ficam versionados no repositório. O script recria as
fotos e o CSV; fotos acrescentadas manualmente devem ser preservadas fora
da pasta de saída antes de regenerar o conjunto.
