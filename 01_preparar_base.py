# -*- coding: utf-8 -*-
"""
GS 2026.2 - CitizenTech | Estatística aplicada em Python
Script 01 - Preparação das bases de dados

FONTES (Kaggle, dados abertos da Polícia Rodoviária Federal - PRF, por OCORRÊNCIA):
  [A] "Federal Highway Accidents Dataset" (alinebertolani), 2014-2024
      arquivo: datatran20142024.csv                       -> base principal
  [B] "Acidentes rodovias federais Brasil Jan/07 a Dez/20" (equeiroz), 2007-2020
      arquivos: datatran2007.csv ... datatran2020.csv     -> base complementar

O QUE ESTE SCRIPT GERA (na mesma pasta do script):
  1. base_acidentes_prf_sp_2024.csv   BASE DO TRABALHO: rodovias federais de SP em 2024 [A],
                                      com as variáveis derivadas hora e houve_morte
  2. serie_historica_sp.csv           acidentes de SP por ano nas duas fontes (2007-2024)
  3. base_apoio_sp_2018_2020.csv      registros de SP de 2018 e 2020 [B], usados só no
                                      teste de robustez do modelo (período diferente)

Uso:
    python 01_preparar_base.py <datatran20142024.csv> [pasta_com_os_csv_da_fonte_B]
    python 01_preparar_base.py datatran20142024.csv ./equeiroz

Variáveis derivadas:
    hora         horário do acidente em horas decimais (18:30 -> 18.5)
    houve_morte  1 se o acidente teve pelo menos 1 morto; 0 caso contrário
"""
import re
import sys
from pathlib import Path

import pandas as pd

PASTA = Path(__file__).resolve().parent
UF, ANO_BASE = "SP", 2024
ANOS_APOIO = (2018, 2020)

COLUNAS_INT = ["br", "pessoas", "mortos", "feridos_leves", "feridos_graves",
               "ilesos", "ignorados", "feridos", "veiculos"]


def ler_csv(caminho: Path) -> pd.DataFrame:
    """Lê CSV da PRF tentando separador (; ou ,) e codificação (utf-8 ou latin-1)."""
    erro = None
    for codificacao in ("utf-8", "latin-1"):
        for separador in (",", ";"):
            try:
                df = pd.read_csv(caminho, sep=separador, encoding=codificacao,
                                 dtype=str, low_memory=False)
                if df.shape[1] > 5:
                    return df
            except Exception as e:  # noqa: BLE001
                erro = e
    raise ValueError(f"Não foi possível ler {caminho}: {erro}")


def parse_datas(serie: pd.Series) -> pd.Series:
    """Datas em 3 formatos que aparecem nos arquivos: AAAA-MM-DD, DD/MM/AAAA e DD/MM/AA."""
    datas = pd.to_datetime(serie, format="%Y-%m-%d", errors="coerce")
    for formato in ("%d/%m/%Y", "%d/%m/%y"):
        faltando = datas.isna()
        if faltando.any():
            datas[faltando] = pd.to_datetime(serie[faltando], format=formato, errors="coerce")
    return datas


def normalizar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    df["km"] = pd.to_numeric(df["km"].astype("string").str.replace(",", ".", regex=False),
                             errors="coerce")
    for coluna in COLUNAS_INT:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce").astype("Int64")
    df["id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")
    df["uf"] = df["uf"].str.strip().str.upper()
    df["data"] = parse_datas(df["data_inversa"])

    horario = pd.to_datetime(df["horario"].astype(str), format="%H:%M:%S", errors="coerce")
    df["hora"] = horario.dt.hour + horario.dt.minute / 60
    df["horario"] = horario.dt.strftime("%H:%M:%S")
    df["houve_morte"] = (df["mortos"] > 0).astype(int)
    return df


def resumo_anual(df: pd.DataFrame, fonte: str) -> pd.DataFrame:
    g = df.groupby("ano").agg(
        acidentes=("id", "size"), acidentes_fatais=("houve_morte", "sum"),
        mortos=("mortos", "sum"), feridos=("feridos", "sum"), pessoas=("pessoas", "sum"))
    g["taxa_fatal"] = g["acidentes_fatais"] / g["acidentes"]
    g.insert(0, "fonte", fonte)
    return g.reset_index()


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    arquivo_a = Path(sys.argv[1])
    pasta_b = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    # ------------------------------------------------------------- fonte A
    a = normalizar(ler_csv(arquivo_a))
    print(f"[A] {arquivo_a.name}: {len(a):,} linhas x {a.shape[1]} colunas")
    a["ano"] = a["data"].dt.year
    a_sp = a[a["uf"] == UF].copy()

    series = [resumo_anual(a_sp, "Kaggle 2014-2024 (alinebertolani)")]

    base = a_sp[a_sp["ano"] == ANO_BASE].copy()
    duplicados = int(base["id"].duplicated().sum())
    base = base.drop_duplicates(subset="id")
    base["data_inversa"] = base["data"].dt.strftime("%Y-%m-%d")
    base = base.drop(columns=[c for c in ("data", "ano", "latitude", "longitude")
                              if c in base.columns])
    saida = PASTA / f"base_acidentes_prf_{UF.lower()}_{ANO_BASE}.csv"
    base.to_csv(saida, index=False, encoding="utf-8")
    print(f"    -> {saida.name}: {len(base):,} ocorrências de {UF} em {ANO_BASE} "
          f"({duplicados} duplicadas removidas; {int(base['houve_morte'].sum())} com morte)")

    # ------------------------------------------------------------- fonte B
    apoio = []
    if pasta_b is not None and pasta_b.exists():
        resumos_b = []
        for arq in sorted(pasta_b.glob("datatran*.csv")):
            ano = int(re.search(r"(\d{4})", arq.name).group(1))
            b = normalizar(ler_csv(arq))
            b = b[b["uf"] == UF].copy()
            b["ano"] = ano  # cada arquivo corresponde a um ano
            resumos_b.append(resumo_anual(b, "Kaggle 2007-2020 (equeiroz)"))
            if ano in ANOS_APOIO:
                apoio.append(b[["ano", "id", "pessoas", "veiculos", "feridos", "mortos",
                                "km", "hora", "houve_morte"]])
            print(f"[B] {arq.name}: {len(b):,} ocorrências em {UF}")
        series += resumos_b
        pd.concat(apoio).to_csv(PASTA / "base_apoio_sp_2018_2020.csv", index=False)
    else:
        print("[B] pasta da fonte B não informada: série histórica terá só a fonte A")

    pd.concat(series, ignore_index=True).to_csv(PASTA / "serie_historica_sp.csv", index=False)
    print("Arquivos gerados em:", PASTA)


if __name__ == "__main__":
    main()
