# Dataset — fotos de documentos

Conteúdo gerado por `scripts/gerar_dataset.py` (semente fixa `42`):

- `fotos/treino/<classe>/` — 28 fotos por classe (70%), usadas na calibração
- `fotos/teste/<classe>/` — 12 fotos por classe (30%), usadas só na avaliação
- `rotulos.csv` — índice com `arquivo`, `classe` e `conjunto`

Classes: `boa`, `borrada`, `iluminacao` (120 imagens no total).

## Origem

Dados **sintéticos**, desenhados pelo próprio projeto: páginas de documento
com texto simulado (sem conteúdo real) e degradações aplicadas por código —
desfoque gaussiano (borrada) e sub/superexposição (iluminação). Nenhum dado
pessoal ou sensível, nenhuma imagem de terceiros.

## Como regenerar

```powershell
ai-model\.venv\Scripts\python ai-model\scripts\gerar_dataset.py
```

## Fotos reais (opcional)

A equipe pode acrescentar fotos próprias de documentos genéricos — sem
rostos e sem dados pessoais — seguindo a mesma divisão treino/teste e
atualizando `rotulos.csv`. Depois é só rodar `scripts/calibrar.py` de novo.

O conjunto atual tem menos de 1 MB por pasta, então fica versionado no
repositório (o edital só pede instruções de download para bases > 50 MB).
