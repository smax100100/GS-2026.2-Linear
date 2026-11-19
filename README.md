# Acidentes em rodovias federais de SP (2024): análise estatística

Global Solution 2026.2 · Desafio CitizenTech · Projeto: chat despachante de trânsito

Análise estatística em Python de acidentes registrados pela Polícia Rodoviária Federal (PRF) nas
rodovias federais de São Paulo em 2024. Cobre probabilidade com a distribuição normal, testes de
hipóteses, regressão linear simples e múltipla, regressão logística e um relatório em PDF com
insights para um assistente digital de orientação em trânsito.

## Integrantes

Andrei Henrique Santos - RM 569440

Heitor Maxímus Mucha - RM 571407


## Estrutura do repositório

| Arquivo | Descrição |
|---|---|
| `01_preparar_base.py` | Lê os CSVs do Kaggle, faz o recorte SP/2024 e cria `hora` e `houve_morte` |
| `02_analise_estatistica.py` | Questões 02 a 06: gera as figuras (`figuras/`) e os números (`resultados.json`) |
| `03_gerar_relatorio.py` | Monta o relatório estatístico em PDF |
| `base_acidentes_prf_sp_2024.csv` | **Base do trabalho**: 4.883 acidentes, rodovias federais de SP, 2024 |
| `serie_historica_sp.csv` | Acidentes de SP por ano (2007–2024), nas duas fontes |
| `base_apoio_sp_2018_2020.csv` | Registros de SP de 2018 e 2020, usados no teste de robustez |
| `relatorio_estatistico_gs_2026_2.pdf` | Relatório final |

## Fontes dos dados

Registros reais de ocorrências da PRF, obtidos no Kaggle:

- **Fonte A (principal):** [Federal Highway Accidents Dataset](https://www.kaggle.com/datasets/alinebertolani/federal-highway-accidents-dataset), arquivo `datatran20142024.csv` (2014–2024).
- **Fonte B (complementar):** [Acidentes rodovias federais Brasil Jan/07 a Dez/20](https://www.kaggle.com/datasets/equeiroz/acidentes-rodovias-federais-brasil-jan07-a-jul19), arquivos `datatran2007.csv` a `datatran2020.csv`.

Os arquivos brutos são grandes (cerca de 220 MB e 400 MB) e **não estão neste repositório**. Para
refazer o recorte a partir deles, baixe os datasets no Kaggle.

## Como reproduzir

Requer Python 3.10 ou superior.

```bash
pip install -r requirements.txt

# Opção 1: usar os CSVs já incluídos neste repositório
python 02_analise_estatistica.py
python 03_gerar_relatorio.py

# Opção 2: refazer tudo a partir dos dados brutos do Kaggle
python 01_preparar_base.py datatran20142024.csv ./equeiroz
python 02_analise_estatistica.py
python 03_gerar_relatorio.py
```

Os scripts devem ser executados nesta ordem e a partir da pasta do projeto. O sorteio das amostras
usa semente fixa (42), então os resultados são reproduzíveis.

## Principais resultados

- 4.883 acidentes em 2024; 214 (4,4%) com pelo menos uma morte.
- Atropelamentos de pedestres são 4,5% dos acidentes e 40,2% dos acidentes fatais.
- Cada veículo adicional se associa a 0,88 pessoa a mais por acidente (r = 0,474; R² = 22,4%).
- A regressão logística tem AUC de 0,61 e não generaliza para 2018 e 2020; não serve de triagem
  automática.

## Observação

Trabalho acadêmico da FIAP. O assistente digital descrito no relatório não é canal oficial de
nenhum órgão de trânsito.
