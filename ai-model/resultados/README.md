# Evidências — Modelo 2.0 (27/11/2026)

Resultado da execução de `scripts/calibrar.py` sobre o dataset sintético
atual (120 imagens, 36 no conjunto de teste), já com as 5 classes do contrato
e os 6 indicadores idênticos ao backend:

| Métrica | Componente | Baseline ("sempre boa") |
|---|---|---|
| Acurácia | **100,0%** | 33,3% |
| F1 macro (5 classes) | **0,600** | 0,100 |

| Classe | Precisão | Recall | F1 | Suporte |
|---|---|---|---|---|
| boa | 1,00 | 1,00 | 1,00 | 12 |
| torta | 0,00 | 0,00 | 0,00 | 0 |
| borrada | 1,00 | 1,00 | 1,00 | 12 |
| iluminação | 1,00 | 1,00 | 1,00 | 12 |
| baixa resolução | 0,00 | 0,00 | 0,00 | 0 |

Matriz de confusão 5×5 (linhas = real, colunas = previsto):

```
                 previsto
real              boa  torta  borrada  iluminação  baixa_resolucao
boa                12      0        0           0                0
torta               0      0        0           0                0
borrada             0      0       12           0                0
iluminação          0      0        0          12                0
baixa_resolucao     0      0        0           0                0
```

Limiares calibrados: `nitidez_minima = 96,02`, `brilho_minimo = 132,08`,
`brilho_maximo = 231,64`, `resolucao_minima_px = 600`,
`altura_texto_relativa_minima = 0,0040`, `angulo_maximo = 8,00`.

## Figuras

| Arquivo | O que mostra |
|---|---|
| `matriz_confusao.png` | matriz de confusão 5×5 no conjunto de teste |
| `dispersao_indicadores.png` | separação das classes por nitidez × brilho |
| `histograma_nitidez.png` | distribuição da nitidez e o limiar calibrado |
| `exemplos_lado_a_lado.png` | entrada e saída do componente por classe disponível |

## Leitura dos resultados

- O componente acerta 36 de 36 fotos do teste nas 3 classes presentes no
  dataset atual (`boa`, `borrada` e `iluminação`), sem falso positivo de
  `baixa_resolucao` nas fotos boas.
- Ganho de **+0,500 de F1 macro** sobre o baseline (0,600 vs 0,100).
- `torta` e `baixa_resolucao` têm suporte 0 neste conjunto; após a entrada do
  dataset ampliado na `develop`, executar `calibrar.py` novamente gera as
  métricas completas das 5 classes.
