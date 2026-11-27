# ai-model — verificação de qualidade e legibilidade de fotos de documentos

Componente de Inteligência Artificial do LifeScan (etapa de IA do Projeto
Integrador). Eixo: **Computação Visual**.

## O que ele faz

Antes de o paciente enviar a foto de um documento, o componente avalia a
imagem e responde com uma das 5 classes do contrato:

| Classe | Significado |
|---|---|
| `boa` | nítida, iluminação adequada e texto legível |
| `torta` | legível, mas o documento está inclinado |
| `borrada` | fora de foco (desfoque) |
| `iluminacao` | escura ou estourada de brilho |
| `baixa_resolucao` | foto pequena ou documento longe demais |

O aviso é **orientativo** — não bloqueia o envio.

## Como funciona

Para cada foto o OpenCV calcula seis indicadores (com a mesma fórmula do backend):

| Indicador | Como é calculado | O que detecta |
|---|---|---|
| **nitidez** | variância do operador Laplaciano | foto fora de foco |
| **brilho** | média dos tons de cinza | foto escura/estourada |
| **contraste** | desvio-padrão dos tons de cinza | foto "apagada" |
| **resolucao_px** | menor lado da imagem original em pixels | foto de baixa resolução |
| **altura_texto_relativa** | mediana da altura das faixas de texto / altura | documento longe demais |
| **angulo** | mediana da inclinação das faixas de texto (graus) | documento inclinado |

As regras de decisão comparam esses valores com **6 limiares calibrados** por
busca coordenada no conjunto de treino, maximizando o F1 macro das 5 classes.
A confiança de cada resposta vem da distância entre o indicador e o limiar.

O resultado da calibração fica em `models/limiares.json` (`"versao": "2.0"`) —
é esse arquivo que o backend carrega em produção (o frontend nunca acessa o modelo).

## Dados

- **Origem:** dados sintéticos gerados pela própria equipe (não há dados de
  terceiros nem dados pessoais/sensíveis).
- **Como são gerados:** `scripts/gerar_dataset.py` desenha páginas de
  documento sintéticas (texto simulado, tabela, margem) e aplica degradações
  controladas com semente fixa (`SEMENTE = 42`).
- **Divisão:** 70% treino (calibração) e 30% teste, estratificadas por classe.
- **Licença:** geradas pelo projeto; uso livre dentro do PI.
- **Fotos reais:** a equipe pode adicionar fotos próprias de documentos
  genéricos (sem rostos e sem dados pessoais) para enriquecer o conjunto;
  o método de geração e a divisão continuam documentados aqui.

## Como executar

Requisitos: Python 3.11+.

```powershell
# 1. ambiente virtual próprio da IA
python -m venv ai-model/.venv
ai-model\.venv\Scripts\python -m pip install -r ai-model/requirements.txt

# 2. gerar o dataset sintético (reprodutível pela semente)
ai-model\.venv\Scripts\python ai-model\scripts\gerar_dataset.py

# 3. calibrar os limiares e avaliar o componente
ai-model\.venv\Scripts\python ai-model\scripts\calibrar.py
```

Saídas:

- `models/limiares.json` — limiares (`versao: "2.0"`) + métricas da execução
- `resultados/matriz_confusao.png` — matriz de confusão 5×5 no teste
- `resultados/dispersao_indicadores.png` — separação das classes
- `resultados/histograma_nitidez.png` — distribuição da nitidez
- `resultados/exemplos_lado_a_lado.png` — entrada e saída por classe

## Avaliação

O script `calibrar.py` imprime no terminal:

- acurácia e F1 por classe no conjunto de teste;
- matriz de confusão 5×5;
- comparação com o **baseline** que responde sempre a classe mais frequente.

Os números obtidos na última execução ficam registrados em
`models/limiares.json` (campo `metricas`).

### Resultados obtidos (execução de 27/11/2026 — modelo 2.0)

| Métrica | Componente | Baseline ("sempre boa") |
|---|---|---|
| Acurácia (teste, 36 fotos) | **100,0%** | 33,3% |
| F1 macro (5 classes) | **0,600** | 0,100 |
| F1 `boa` | 1,00 | — |
| F1 `torta` | 0,00 *(sem amostras no dataset atual)* | — |
| F1 `borrada` | 1,00 | — |
| F1 `iluminação` | 1,00 | — |
| F1 `baixa_resolucao` | 0,00 *(sem amostras no dataset atual)* | — |

Limiares calibrados: `nitidez_minima = 96,02`, `brilho_minimo = 132,08`,
`brilho_maximo = 231,64`, `resolucao_minima_px = 600`,
`altura_texto_relativa_minima = 0,0040`, `angulo_maximo = 8,00`.

**Interpretação:** nas 3 classes atualmente presentes no dataset (`boa`,
`borrada` e `iluminação`), o componente acertou 36 de 36 fotos no teste
(100,0% de acurácia, F1 = 1,00 em todas elas), sem classificar nenhuma foto boa
como `baixa_resolucao`. O F1 macro sobre as 5 classes ficou em **0,600**
(+0,500 sobre o baseline) porque `torta` e `baixa_resolucao` ainda não possuem
amostras no `rotulos.csv` atual — após o merge do dataset ampliado na
`develop`, basta rodar `calibrar.py` novamente para atualizar a calibração
final com as 5 classes.

## Limitações

- Fotos de tela (prints) podem parecer nítidas mesmo com baixa qualidade real.
- Papel sem textura e documentos muito claros reduzem a confiança.
- O componente avalia a **qualidade da captura**, não o conteúdo do documento
  (leitura do conteúdo seria OCR — evolução futura).
- A calibração atual usa dados sintéticos; com fotos reais da equipe os
  limiares devem ser recalibrados (mesmo comando).
