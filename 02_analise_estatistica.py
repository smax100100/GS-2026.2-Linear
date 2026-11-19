# -*- coding: utf-8 -*-
"""
GS 2026.2 - CitizenTech | Estatística aplicada em Python
Script 02 - Análise estatística (questões 02 a 06)

Base: acidentes em rodovias federais de SP em 2024 (PRF, agrupados por ocorrência).
Entrada : base_acidentes_prf_sp_2024.csv (gerada pelo script 01)
Saída   : pasta figuras/ (gráficos .png) e resultados.json (números do relatório)

Execução: python 02_analise_estatistica.py
"""
import json
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
from scipy import stats
from sklearn.metrics import (accuracy_score, confusion_matrix, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor

warnings.filterwarnings("ignore")

SEED = 42
PASTA = Path(__file__).resolve().parent
ARQUIVO_BASE = PASTA / "base_acidentes_prf_sp_2024.csv"
PASTA_FIG = PASTA / "figuras"
PASTA_FIG.mkdir(exist_ok=True)

AZUL, LARANJA, CINZA, VERMELHO = "#1f4e79", "#e07b00", "#6b7280", "#b42318"
sns.set_theme(style="whitegrid", font_scale=0.95)
plt.rcParams.update({"figure.dpi": 130, "savefig.dpi": 200, "axes.titleweight": "bold"})

resultados: dict = {}


def br(valor: float, casas: int = 2) -> str:
    """Número com vírgula decimal (padrão brasileiro) para rótulos dos gráficos."""
    return f"{valor:.{casas}f}".replace(".", ",")


def salvar_fig(nome: str) -> str:
    caminho = PASTA_FIG / nome
    plt.tight_layout()
    plt.savefig(caminho, bbox_inches="tight")
    plt.close()
    return f"figuras/{nome}"


# ---------------------------------------------------------------------------
# 0. Leitura e descrição geral da base
# ---------------------------------------------------------------------------
df = pd.read_csv(ARQUIVO_BASE)
N = len(df)

resultados["base"] = {
    "n": N,
    "uf": "SP",
    "ano": 2024,
    "periodo": f"{df['data_inversa'].min()} a {df['data_inversa'].max()}",
    "colunas": int(df.shape[1]),
    "mortos_total": int(df["mortos"].sum()),
    "feridos_total": int(df["feridos"].sum()),
    "pessoas_total": int(df["pessoas"].sum()),
    "acidentes_fatais": int(df["houve_morte"].sum()),
    "taxa_fatal": float(df["houve_morte"].mean()),
    "nulos": {c: int(v) for c, v in df.isna().sum().items() if v > 0},
    "linhas_soma_inconsistente": int(
        (df["pessoas"] < (df["mortos"] + df["feridos"] + df["ilesos"] + df["ignorados"])).sum()
    ),
}

VARIAVEIS = ["pessoas", "veiculos", "feridos", "mortos", "km", "hora"]
desc = df[VARIAVEIS].describe().T
desc["mediana"] = df[VARIAVEIS].median()
desc["assimetria"] = df[VARIAVEIS].apply(stats.skew)
resultados["descritiva"] = {
    v: {
        "media": float(desc.loc[v, "mean"]), "dp": float(desc.loc[v, "std"]),
        "min": float(desc.loc[v, "min"]), "q1": float(desc.loc[v, "25%"]),
        "mediana": float(desc.loc[v, "mediana"]), "q3": float(desc.loc[v, "75%"]),
        "max": float(desc.loc[v, "max"]), "assimetria": float(desc.loc[v, "assimetria"]),
    }
    for v in VARIAVEIS
}


def taxa_por(coluna: str, minimo: int = 100, topo: int | None = None) -> list[dict]:
    """Taxa de acidentes com morte por categoria (categorias com n >= minimo)."""
    t = df.groupby(coluna)["houve_morte"].agg(n="count", fatais="sum")
    t["taxa"] = t["fatais"] / t["n"]
    t = t[t["n"] >= minimo].sort_values("taxa", ascending=False)
    if topo:
        t = t.head(topo)
    return [{"categoria": str(i), "n": int(r.n), "fatais": int(r.fatais), "taxa": float(r.taxa)}
            for i, r in t.iterrows()]


resultados["letalidade"] = {
    "tipo_acidente": taxa_por("tipo_acidente"),
    "causa_acidente": taxa_por("causa_acidente", topo=8),
    "fase_dia": taxa_por("fase_dia"),
    "tipo_pista": taxa_por("tipo_pista"),
    "condicao_meteo": taxa_por("condicao_metereologica"),
    "dia_semana": taxa_por("dia_semana"),
    "br": taxa_por("br", minimo=200),
}
resultados["top_causas_volume"] = [
    {"categoria": k, "n": int(v), "pct": float(v / N)}
    for k, v in df["causa_acidente"].value_counts().head(5).items()
]

# --- Figuras descritivas ----------------------------------------------------
fig, ax = plt.subplots(figsize=(6.4, 3.4))
contagem_hora = df["hora"].astype(int).value_counts().sort_index()
ax.bar(contagem_hora.index, contagem_hora.values, color=AZUL)
ax.set_title("Acidentes por hora do dia (rodovias federais de SP, 2024)")
ax.set_xlabel("Hora do dia")
ax.set_ylabel("Número de acidentes")
ax.set_xticks(range(0, 24, 2))
resultados["fig_horas"] = salvar_fig("fig01_acidentes_por_hora.png")

tipo = pd.DataFrame(resultados["letalidade"]["tipo_acidente"]).sort_values("taxa")
fig, ax = plt.subplots(figsize=(6.4, 3.6))
cores = [VERMELHO if t > 0.1 else AZUL for t in tipo["taxa"]]
ax.barh(tipo["categoria"], tipo["taxa"] * 100, color=cores)
ax.axvline(resultados["base"]["taxa_fatal"] * 100, color=CINZA, ls="--", lw=1)
ax.text(resultados["base"]["taxa_fatal"] * 100 + 0.6, 0.1, "média geral", color=CINZA, fontsize=8)
ax.set_title("Acidentes com morte por tipo de acidente (n ≥ 100)")
ax.set_xlabel("% de acidentes com pelo menos 1 morto")
ax.set_ylabel("Tipo de acidente")
resultados["fig_letalidade_tipo"] = salvar_fig("fig02_letalidade_por_tipo.png")

fase = pd.DataFrame(resultados["letalidade"]["fase_dia"]).sort_values("taxa", ascending=False)
fig, ax = plt.subplots(figsize=(6.4, 3.0))
ax.bar(fase["categoria"], fase["taxa"] * 100, color=AZUL)
ax.axhline(resultados["base"]["taxa_fatal"] * 100, color=CINZA, ls="--", lw=1)
ax.set_title("Acidentes com morte por fase do dia")
ax.set_xlabel("Fase do dia")
ax.set_ylabel("% de acidentes com morte")
resultados["fig_letalidade_fase"] = salvar_fig("fig03_letalidade_por_fase_dia.png")

# ---------------------------------------------------------------------------
# Questão 02 - Probabilidades com a Distribuição Normal
# ---------------------------------------------------------------------------
VAR_Q2 = "pessoas"  # pessoas envolvidas por acidente
x = df[VAR_Q2].astype(float)
mu, sigma = x.mean(), x.std(ddof=0)  # parâmetros da normal (dp populacional)
mediana = x.median()


def classificar_evento(p: float) -> str:
    """Classificação do evento pelo resultado probabilístico."""
    if np.isclose(p, 0):
        return "Evento impossível"
    if np.isclose(p, 1):
        return "Evento certo"
    if np.isclose(p, 0.5):
        return "Evento equiprovável (50%)"
    return "Evento provável" if p > 0.5 else "Evento improvável"


p_a = float(stats.norm.cdf(mu, loc=mu, scale=sigma))            # P(X < média)
p_b = float(1 - stats.norm.cdf(mediana, loc=mu, scale=sigma))   # P(X > mediana)
z_med = float((mediana - mu) / sigma)

# curva normal sobre o histograma (apoio visual)
fig, ax = plt.subplots(figsize=(6.4, 3.4))
limite = int(np.ceil(x.quantile(0.995)))
ax.hist(x[x <= limite], bins=np.arange(0.5, limite + 1.5, 1), density=True, color=AZUL,
        alpha=0.85, label="Dados observados")
grade = np.linspace(0, limite, 300)
ax.plot(grade, stats.norm.pdf(grade, mu, sigma), color=LARANJA, lw=2, label="Normal ajustada (μ, σ)")
ax.axvline(mu, color=VERMELHO, ls="--", lw=1.2, label=f"Média = {br(mu)}")
ax.axvline(mediana, color=CINZA, ls=":", lw=1.5, label=f"Mediana = {br(mediana, 0)}")
ax.set_title("Pessoas envolvidas por acidente: dados × Normal ajustada")
ax.set_xlabel("Pessoas envolvidas por acidente")
ax.set_ylabel("Densidade")
ax.legend(fontsize=8)
resultados["fig_q2"] = salvar_fig("fig04_q2_normal_pessoas.png")

resultados["q2"] = {
    "variavel": VAR_Q2, "media": float(mu), "dp_pop": float(sigma), "mediana": float(mediana),
    "z_mediana": z_med, "p_menor_media": p_a, "classe_a": classificar_evento(p_a),
    "p_maior_mediana": p_b, "classe_b": classificar_evento(p_b),
    "assimetria": float(stats.skew(x)),
    # frequências observadas (para comparar com a hipótese de normalidade)
    "freq_menor_media": float((x < mu).mean()), "freq_maior_mediana": float((x > mediana).mean()),
}

# ---------------------------------------------------------------------------
# Questão 03 - Testes de hipóteses para a média (teste Z, σ conhecido)
# ---------------------------------------------------------------------------
rng = np.random.default_rng(SEED)


def teste_z(amostra: np.ndarray, alpha: float, cauda: str) -> dict:
    n = len(amostra)
    xbar = float(amostra.mean())
    erro_padrao = sigma / np.sqrt(n)
    z = (xbar - mu) / erro_padrao
    if cauda == "menor":
        zc, p_valor, rejeita = stats.norm.ppf(alpha), stats.norm.cdf(z), z < stats.norm.ppf(alpha)
    else:
        zc, p_valor, rejeita = (stats.norm.ppf(1 - alpha), 1 - stats.norm.cdf(z),
                                z > stats.norm.ppf(1 - alpha))
    return {"n": n, "alpha": alpha, "cauda": cauda, "xbar": xbar, "mu0": float(mu),
            "sigma": float(sigma), "erro_padrao": float(erro_padrao), "z": float(z),
            "z_critico": float(zc), "p_valor": float(p_valor), "rejeita_h0": bool(rejeita)}


def taxa_rejeicao_simulada(n: int, alpha: float, cauda: str, repeticoes: int = 5000) -> float:
    """Se H0 é verdadeira, a taxa de rejeição deveria ficar próxima de alpha."""
    rejeicoes = 0
    for _ in range(repeticoes):
        amostra = rng.choice(x.values, size=n, replace=False)
        rejeicoes += teste_z(amostra, alpha, cauda)["rejeita_h0"]
    return rejeicoes / repeticoes


amostra_a = rng.choice(x.values, size=20, replace=False)
amostra_b = rng.choice(x.values, size=25, replace=False)
q3a = teste_z(amostra_a, 0.06, "menor")
q3b = teste_z(amostra_b, 0.09, "maior")
q3a["rejeicao_simulada"] = taxa_rejeicao_simulada(20, 0.06, "menor")
q3b["rejeicao_simulada"] = taxa_rejeicao_simulada(25, 0.09, "maior")
resultados["q3"] = {"a": q3a, "b": q3b, "variavel": VAR_Q2, "semente": SEED}

# ---------------------------------------------------------------------------
# Questão 04 - Análise bivariada: veículos envolvidos (X) × pessoas envolvidas (Y)
# ---------------------------------------------------------------------------
X4, Y4 = "veiculos", "pessoas"
cov4 = float(np.cov(df[X4], df[Y4], ddof=1)[0, 1])
r4, p_r4 = stats.pearsonr(df[X4], df[Y4])
modelo4 = sm.OLS(df[Y4], sm.add_constant(df[[X4]])).fit()
b0, b1 = modelo4.params["const"], modelo4.params[X4]
bp4 = het_breuschpagan(modelo4.resid, modelo4.model.exog)

# a) dispersão + c) reta (jitter apenas visual: as variáveis são contagens inteiras)
jitter = np.random.default_rng(SEED)
fig, ax = plt.subplots(figsize=(6.4, 4.0))
ax.scatter(df[X4] + jitter.uniform(-0.18, 0.18, N), df[Y4] + jitter.uniform(-0.18, 0.18, N),
           s=9, alpha=0.25, color=AZUL, label="Acidentes (com pequeno desvio visual)")
grade_x = np.linspace(df[X4].min(), df[X4].max(), 100)
ax.plot(grade_x, b0 + b1 * grade_x, color=LARANJA, lw=2.2,
        label=f"Reta: Pessoas = {br(b0)} + {br(b1)} × Veículos")
ax.set_title("Veículos envolvidos × pessoas envolvidas por acidente")
ax.set_xlabel("Veículos envolvidos")
ax.set_ylabel("Pessoas envolvidas")
ax.legend(fontsize=8, loc="upper left")
resultados["fig_q4_disp"] = salvar_fig("fig05_q4_dispersao_reta.png")

# b) gráfico de correlação de Pearson
fig, ax = plt.subplots(figsize=(4.4, 3.5))
corr4 = df[[X4, Y4]].corr()
sns.heatmap(corr4, annot=corr4.map(lambda v: br(v, 3)).values, fmt="", cmap="RdBu_r", vmin=-1, vmax=1,
            square=True, cbar_kws={"label": "Correlação de Pearson"}, ax=ax)
ax.set_title("Correlação linear de Pearson")
resultados["fig_q4_corr"] = salvar_fig("fig06_q4_correlacao.png")

# resíduos (verificação do modelo)
fig, ax = plt.subplots(figsize=(6.4, 3.4))
ax.scatter(modelo4.fittedvalues + jitter.uniform(-0.05, 0.05, N), modelo4.resid, s=8,
           alpha=0.25, color=AZUL)
ax.axhline(0, color=LARANJA, lw=1.5)
ax.set_title("Resíduos × valores ajustados (regressão simples)")
ax.set_xlabel("Pessoas envolvidas ajustadas pelo modelo")
ax.set_ylabel("Resíduo")
resultados["fig_q4_res"] = salvar_fig("fig07_q4_residuos.png")

x_novo = 3
pred4 = modelo4.get_prediction(pd.DataFrame({"const": [1.0], X4: [x_novo]})).summary_frame(alpha=0.05)
resultados["q4"] = {
    "x": X4, "y": Y4, "covariancia": cov4, "pearson": float(r4), "p_pearson": float(p_r4),
    "b0": float(b0), "b1": float(b1), "ep_b1": float(modelo4.bse[X4]),
    "ic_b1": [float(v) for v in modelo4.conf_int().loc[X4]],
    "r2": float(modelo4.rsquared), "r2_aj": float(modelo4.rsquared_adj),
    "F": float(modelo4.fvalue), "p_F": float(modelo4.f_pvalue),
    "df_modelo": int(modelo4.df_model), "df_resid": int(modelo4.df_resid),
    "bp_p": float(bp4[1]),
    "previsao": {"x": x_novo, "y": float(pred4["mean"].iloc[0]),
                 "ic_inf": float(pred4["mean_ci_lower"].iloc[0]),
                 "ic_sup": float(pred4["mean_ci_upper"].iloc[0]),
                 "pi_inf": float(pred4["obs_ci_lower"].iloc[0]),
                 "pi_sup": float(pred4["obs_ci_upper"].iloc[0])},
}

# ---------------------------------------------------------------------------
# Questão 05 - Regressão linear múltipla: feridos ~ pessoas + veículos + km
# ---------------------------------------------------------------------------
Y5, X5 = "feridos", ["pessoas", "veiculos", "km"]
VARS5 = [Y5] + X5
cov5 = df[VARS5].cov()
corr5 = df[VARS5].corr()
modelo5 = sm.OLS(df[Y5], sm.add_constant(df[X5])).fit()
bp5 = het_breuschpagan(modelo5.resid, modelo5.model.exog)
# erros-padrão robustos à heterocedasticidade (HC3): conferem se a significância se mantém
p_robusto5 = dict(zip(modelo5.params.index, modelo5.get_robustcov_results(cov_type="HC3").pvalues))
robusto5 = modelo5.get_robustcov_results(cov_type="HC3")  # erros-padrão robustos à heterocedasticidade
p_robusto5 = dict(zip(["const"] + X5, [float(v) for v in robusto5.pvalues]))
exog5 = sm.add_constant(df[X5]).values
vif = {X5[i]: float(variance_inflation_factor(exog5, i + 1)) for i in range(len(X5))}

# a) matriz de dispersão
rotulos = {"feridos": "Feridos", "pessoas": "Pessoas", "veiculos": "Veículos", "km": "Km da rodovia"}
grade5 = sns.PairGrid(df[VARS5].rename(columns=rotulos), corner=False, height=1.7)
grade5.map_lower(sns.scatterplot, s=6, alpha=0.2, color=AZUL)
grade5.map_upper(sns.scatterplot, s=6, alpha=0.2, color=AZUL)
grade5.map_diag(sns.histplot, color=AZUL, bins=20)
grade5.figure.suptitle("Matriz de dispersão: feridos, pessoas, veículos e km", y=1.02,
                       fontweight="bold")
resultados["fig_q5_disp"] = "figuras/fig08_q5_matriz_dispersao.png"
grade5.savefig(PASTA / resultados["fig_q5_disp"], bbox_inches="tight", dpi=200)
plt.close("all")

# c) correlação
fig, ax = plt.subplots(figsize=(5.2, 4.2))
sns.heatmap(corr5.rename(index=rotulos, columns=rotulos),
            annot=corr5.map(lambda v: br(v, 3)).values, fmt="", cmap="RdBu_r",
            vmin=-1, vmax=1, square=True, cbar_kws={"label": "Correlação de Pearson"}, ax=ax)
ax.set_title("Matriz de correlação linear de Pearson")
resultados["fig_q5_corr"] = salvar_fig("fig09_q5_correlacao.png")

novo5 = {"const": 1.0, "pessoas": 4, "veiculos": 2, "km": 150}
pred5 = modelo5.get_prediction(pd.DataFrame([novo5])[["const"] + X5]).summary_frame(alpha=0.05)
resultados["q5"] = {
    "y": Y5, "x": X5,
    "cov": {a: {b: float(cov5.loc[a, b]) for b in VARS5} for a in VARS5},
    "corr": {a: {b: float(corr5.loc[a, b]) for b in VARS5} for a in VARS5},
    "coef": {k: float(v) for k, v in modelo5.params.items()},
    "ep": {k: float(v) for k, v in modelo5.bse.items()},
    "t": {k: float(v) for k, v in modelo5.tvalues.items()},
    "p": {k: float(v) for k, v in modelo5.pvalues.items()},
    "p_robusto": {k: float(v) for k, v in p_robusto5.items()},
    "r2": float(modelo5.rsquared), "r2_aj": float(modelo5.rsquared_adj),
    "F": float(modelo5.fvalue), "p_F": float(modelo5.f_pvalue),
    "df_modelo": int(modelo5.df_model), "df_resid": int(modelo5.df_resid),
    "vif": vif, "bp_p": float(bp5[1]), "p_robusto": p_robusto5,
    "previsao": {"entrada": {k: v for k, v in novo5.items() if k != "const"},
                 "y": float(pred5["mean"].iloc[0]),
                 "pi_inf": float(pred5["obs_ci_lower"].iloc[0]),
                 "pi_sup": float(pred5["obs_ci_upper"].iloc[0])},
}

# ---------------------------------------------------------------------------
# Questão 06 - Regressão logística binária: houve_morte ~ pessoas + veículos + km + hora
# ---------------------------------------------------------------------------
Y6, X6 = "houve_morte", ["pessoas", "veiculos", "km", "hora"]
X_tr, X_te, y_tr, y_te = train_test_split(df[X6], df[Y6], test_size=0.30, random_state=SEED,
                                          stratify=df[Y6])
modelo6 = sm.Logit(y_tr, sm.add_constant(X_tr)).fit(disp=0)
prob_te = modelo6.predict(sm.add_constant(X_te))
limiar_prev = float(y_tr.mean())  # limiar alternativo = prevalência do evento


def avaliar(limiar: float) -> dict:
    pred = (prob_te >= limiar).astype(int)
    vn, fp, fn, vp = confusion_matrix(y_te, pred, labels=[0, 1]).ravel()
    return {"limiar": float(limiar), "vn": int(vn), "fp": int(fp), "fn": int(fn), "vp": int(vp),
            "acuracia": float(accuracy_score(y_te, pred)),
            "sensibilidade": float(recall_score(y_te, pred, zero_division=0)),
            "especificidade": float(vn / (vn + fp)),
            "precisao": float(precision_score(y_te, pred, zero_division=0))}


aval_05, aval_prev = avaliar(0.5), avaliar(limiar_prev)

fig, eixos = plt.subplots(1, 2, figsize=(8.2, 3.6))
for eixo, aval, titulo in ((eixos[0], aval_05, f"Limiar 0,50 (acurácia {br(aval_05['acuracia'] * 100, 1)}%)"),
                           (eixos[1], aval_prev,
                            f"Limiar {br(limiar_prev, 3)} (acurácia {br(aval_prev['acuracia'] * 100, 1)}%)")):
    matriz = np.array([[aval["vn"], aval["fp"]], [aval["fn"], aval["vp"]]])
    sns.heatmap(matriz, annot=True, fmt="d", cmap="Blues", cbar=False, ax=eixo,
                xticklabels=["Sem morte", "Com morte"], yticklabels=["Sem morte", "Com morte"])
    eixo.set_title(titulo, fontsize=9)
    eixo.set_xlabel("Classe prevista")
    eixo.set_ylabel("Classe real")
fig.suptitle("Matriz de confusão (conjunto de teste, 30% da base)", fontweight="bold")
resultados["fig_q6_conf"] = salvar_fig("fig10_q6_matriz_confusao.png")

ci6 = modelo6.conf_int()
odds = {k: [float(np.exp(modelo6.params[k])), float(np.exp(ci6.loc[k, 0])),
            float(np.exp(ci6.loc[k, 1]))] for k in X6}
novo6 = {"pessoas": 4, "veiculos": 3, "km": 100, "hora": 22}
prob_novo = float(modelo6.predict(pd.DataFrame([{"const": 1.0, **novo6}])[["const"] + X6]).iloc[0])
resultados["q6"] = {
    "y": Y6, "x": X6, "n_treino": int(len(y_tr)), "n_teste": int(len(y_te)),
    "fatais_treino": int(y_tr.sum()), "fatais_teste": int(y_te.sum()),
    "coef": {k: float(v) for k, v in modelo6.params.items()},
    "ep": {k: float(v) for k, v in modelo6.bse.items()},
    "p": {k: float(v) for k, v in modelo6.pvalues.items()},
    "odds": odds, "pseudo_r2": float(modelo6.prsquared), "llr_p": float(modelo6.llr_pvalue),
    "aval_05": aval_05, "aval_prev": aval_prev,
    "acuracia_base": float(1 - y_te.mean()), "auc": float(roc_auc_score(y_te, prob_te)),
    "previsao": {"entrada": novo6, "prob": prob_novo,
                 "classe_05": "Com morte" if prob_novo >= 0.5 else "Sem morte",
                 "classe_prev": "Com morte" if prob_novo >= limiar_prev else "Sem morte"},
}

# ---------------------------------------------------------------------------
# Complemento - fonte B (equeiroz, 2007-2020): série histórica e teste de robustez
# ---------------------------------------------------------------------------
ARQ_SERIE = PASTA / "serie_historica_sp.csv"
ARQ_APOIO = PASTA / "base_apoio_sp_2018_2020.csv"
FONTE_A, FONTE_B = "Kaggle 2014-2024 (alinebertolani)", "Kaggle 2007-2020 (equeiroz)"

if ARQ_SERIE.exists():
    serie = pd.read_csv(ARQ_SERIE)
    sa = serie[serie["fonte"] == FONTE_A].set_index("ano")
    sb = serie[serie["fonte"] == FONTE_B].set_index("ano")

    fig, eixos = plt.subplots(1, 2, figsize=(8.4, 3.4))
    for eixo, coluna, titulo, rotulo in (
            (eixos[0], "acidentes", "Acidentes registrados", "Acidentes por ano"),
            (eixos[1], "taxa_fatal", "Acidentes com morte", "% de acidentes com morte")):
        fator = 100 if coluna == "taxa_fatal" else 1
        eixo.plot(sb.index, sb[coluna] * fator, "o-", color=LARANJA, ms=4, label="Fonte B (2007-2020)")
        eixo.plot(sa.index, sa[coluna] * fator, "s--", color=AZUL, ms=4, label="Fonte A (2014-2024)")
        eixo.set_title(titulo)
        eixo.set_xlabel("Ano")
        eixo.set_ylabel(rotulo)
    eixos[0].legend(fontsize=8)
    fig.suptitle("Rodovias federais de SP: série histórica (PRF)", fontweight="bold")
    fig_serie = salvar_fig("fig11_serie_historica_sp.png")

    comuns = sorted(set(sa.index) & set(sb.index))
    resultados["serie"] = {
        "fig": fig_serie,
        "anos_a": [int(i) for i in sa.index], "anos_b": [int(i) for i in sb.index],
        "acidentes_a": {int(i): int(sa.loc[i, "acidentes"]) for i in sa.index},
        "acidentes_b": {int(i): int(sb.loc[i, "acidentes"]) for i in sb.index},
        "taxa_a": {int(i): float(sa.loc[i, "taxa_fatal"]) for i in sa.index},
        "taxa_b": {int(i): float(sb.loc[i, "taxa_fatal"]) for i in sb.index},
        "sobreposicao": [{"ano": int(a), "n_a": int(sa.loc[a, "acidentes"]),
                          "n_b": int(sb.loc[a, "acidentes"]),
                          "dif_pct": float(sa.loc[a, "acidentes"] / sb.loc[a, "acidentes"] - 1)}
                         for a in comuns],
        "anos_so_b": [int(i) for i in sb.index if i not in sa.index],
        "anos_so_a": [int(i) for i in sa.index if i not in sb.index],
    }

if ARQ_APOIO.exists():
    apoio = pd.read_csv(ARQ_APOIO).dropna(subset=["km", "hora"])

    def ajustar_ano(dados: pd.DataFrame, rotulo: str, auc_externo: bool) -> dict:
        """Refaz a regressão simples (Q4) e a logística (Q6) em outro período."""
        ols = sm.OLS(dados["pessoas"], sm.add_constant(dados[["veiculos"]])).fit()
        logit = sm.Logit(dados[Y6], sm.add_constant(dados[X6])).fit(disp=0)
        linha = {
            "periodo": rotulo, "n": int(len(dados)), "taxa_fatal": float(dados[Y6].mean()),
            "r": float(dados["pessoas"].corr(dados["veiculos"])),
            "b1": float(ols.params["veiculos"]), "r2": float(ols.rsquared),
            "or_veiculos": float(np.exp(logit.params["veiculos"])),
            "p_veiculos": float(logit.pvalues["veiculos"]),
            "or_pessoas": float(np.exp(logit.params["pessoas"])),
            "p_pessoas": float(logit.pvalues["pessoas"]),
        }
        if auc_externo:  # modelo treinado só com 2024, aplicado ao outro período
            prob = modelo6.predict(sm.add_constant(dados[X6]))
            linha["auc_modelo_2024"] = float(roc_auc_score(dados[Y6], prob))
        else:
            linha["auc_modelo_2024"] = float(roc_auc_score(y_te, prob_te))
        return linha

    robustez = [ajustar_ano(apoio[apoio["ano"] == ano], f"SP {ano} (fonte B)", True)
                for ano in (2018, 2020)]
    robustez.append(ajustar_ano(df, "SP 2024 (fonte A, base do trabalho)", False))
    resultados["robustez"] = robustez

# ---------------------------------------------------------------------------
# Saída
# ---------------------------------------------------------------------------
with open(PASTA / "resultados.json", "w", encoding="utf-8") as arquivo:
    json.dump(resultados, arquivo, ensure_ascii=False, indent=2)

print("Análise concluída: figuras em ./figuras e números em resultados.json")
print(f"Q2: P(X<média)={p_a:.4f} | P(X>mediana)={p_b:.4f}")
print(f"Q3a: z={q3a['z']:.3f} (crítico {q3a['z_critico']:.3f}) rejeita H0? {q3a['rejeita_h0']}")
print(f"Q3b: z={q3b['z']:.3f} (crítico {q3b['z_critico']:.3f}) rejeita H0? {q3b['rejeita_h0']}")
print(f"Q4: r={r4:.3f} | R²={modelo4.rsquared:.3f} | pessoas = {b0:.3f} + {b1:.3f}·veiculos")
print(f"Q5: R²={modelo5.rsquared:.3f} | R² aj.={modelo5.rsquared_adj:.3f}")
print(f"Q6: acurácia(0,5)={aval_05['acuracia']:.3f} | sens={aval_05['sensibilidade']:.3f} "
      f"| AUC={resultados['q6']['auc']:.3f}")
