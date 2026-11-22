# ai-model — verificação de qualidade de fotos de documentos

Componente de Inteligência Artificial do LifeScan (etapa de IA do Projeto
Integrador). Eixo: **Computação Visual**.

## O que ele faz

Antes de o paciente enviar a foto de um documento, o componente avalia a
imagem e responde se ela está:

| Classe | Significado |
|---|---|
| `boa` | nítida e com iluminação adequada |
| `borrada` | fora de foco (desfoque) |
| `iluminacao` | escura ou estourada de brilho |

O aviso é **orientativo** — não bloqueia o envio.

## Como funciona

Para cada foto o OpenCV calcula três indicadores:

| Indicador | Como é calculado | O que detecta |
|---|---|---|
| **nitidez** | variância do operador Laplaciano | foto fora de foco |
| **brilho** | média dos tons de cinza | foto escura/estourada |
| **contraste** | desvio-padrão dos tons de cinza | foto "apagada" |

As regras de decisão comparam esses valores com **limiares calibrados** no
conjunto de calibração (70% do dataset), maximizando o F1 macro. A confiança
de cada resposta vem da distância entre o indicador e o limiar.

O resultado da calibração fica em `models/limiares.json` — é esse arquivo
que o backend carrega em produção (o frontend nunca acessa o modelo).

## Dados

- **Origem:** dados sintéticos gerados pela própria equipe (não há dados de
  terceiros nem dados pessoais/sensíveis).
- **Como são gerados:** `scripts/gerar_dataset.py` desenha páginas de
  documento sintéticas (texto simulado, tabela, margem) e aplica degradações
  controladas — desfoque gaussiano para `borrada`, sub/superexposição para
  `iluminacao` — com semente fixa (`SEMENTE = 42`).
- **Tamanho:** 120 imagens (40 por classe), divididas em 70% calibração e
  30% teste, estratificadas por classe.
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

- `models/limiares.json` — limiares + métricas da execução
- `resultados/matriz_confusao.png` — matriz de confusão no teste
- `resultados/dispersao_indicadores.png` — separação das classes
- `resultados/histograma_nitidez.png` — distribuição da nitidez
- `resultados/exemplos_lado_a_lado.png` — entrada e saída por classe

## Avaliação

O script `calibrar.py` imprime no terminal:

- acurácia e F1 por classe no conjunto de teste;
- matriz de confusão;
- comparação com o **baseline** que responde sempre a classe mais frequente.

Os números obtidos na última execução ficam registrados em
`models/limiares.json` (campo `metricas`).

### Resultados obtidos (execução de 22/11/2026)

| Métrica | Componente | Baseline ("sempre boa") |
|---|---|---|
| Acurácia (teste, 36 fotos) | **97,2%** | 33,3% |
| F1 macro | **0,972** | 0,167 |
| F1 `boa` | 1,00 | — |
| F1 `borrada` | 0,96 | — |
| F1 `iluminação` | 0,96 | — |

Limiares calibrados: nitidez mínima `96,02`, brilho entre `132,08` e `231,45`.

**Interpretação:** o componente separa bem as três classes; o único erro do
teste foi uma foto **borrada classificada como iluminação** (a foto tinha
brilho fora da faixa, e a regra de iluminação é avaliada antes da nitidez).
O resultado é bom para o uso proposto — um aviso orientativo, em que o custo
de um falso alarme é baixo e o médico continua podendo abrir o documento.
Como o conjunto é **sintético e controlado**, os números tendem a ser
otimistas: com fotos reais de celular espera-se mais confusão entre classes,
principalmente em fotos escuras e borradas ao mesmo tempo. Recalibrar com as
fotos da equipe antes da entrega final.

## Limitações

- Fotos de tela (prints) podem parecer nítidas mesmo com baixa qualidade real.
- Papel sem textura e documentos muito claros reduzem a confiança.
- O componente avalia a **qualidade da captura**, não o conteúdo do documento
  (leitura do conteúdo seria OCR — evolução futura).
- A calibração atual usa dados sintéticos; com fotos reais da equipe os
  limiares devem ser recalibrados (mesmo comando).
