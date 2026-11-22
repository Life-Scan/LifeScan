# Evidências — Checkpoint 2 (22/11/2026)

Resultado da execução de `scripts/calibrar.py` sobre o dataset sintético
(120 imagens, 36 no conjunto de teste):

| Métrica | Componente | Baseline ("sempre boa") |
|---|---|---|
| Acurácia | **97,2%** | 33,3% |
| F1 macro | **0,972** | 0,167 |

| Classe | Precisão | Recall | F1 | Suporte |
|---|---|---|---|---|
| boa | 1,00 | 1,00 | 1,00 | 12 |
| borrada | 1,00 | 0,92 | 0,96 | 12 |
| iluminação | 0,92 | 1,00 | 0,96 | 12 |

Matriz de confusão (linhas = real, colunas = previsto):

```
            previsto
real         boa  borrada  iluminação
boa           12      0        0
borrada        0     11        1
iluminação     0      0       12
```

Limiares calibrados: nitidez mínima `96,02`; brilho entre `132,08` e `231,45`.

## Figuras

| Arquivo | O que mostra |
|---|---|
| `matriz_confusao.png` | acertos e o único erro (borrada → iluminação) |
| `dispersao_indicadores.png` | separação das classes por nitidez × brilho |
| `histograma_nitidez.png` | distribuição da nitidez e o limiar calibrado |
| `exemplos_lado_a_lado.png` | entrada e saída do componente, um exemplo por classe |

## Leitura dos resultados

- O componente acerta 35 de 36 fotos do teste; o único erro é uma foto
  borrada cujo brilho também estava fora da faixa (a regra de iluminação é
  avaliada antes da nitidez).
- Ganho de **+0,806 de F1 macro** sobre o baseline — evidência de que as
  regras e os limiares capturam o problema.
- **Ressalva:** o conjunto é sintético e controlado; os números são
  otimistas. A próxima etapa é acrescentar fotos reais da equipe e
  recalibrar (mesmo comando), antes da integração ao sistema.
