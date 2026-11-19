# -*- coding: utf-8 -*-
"""
GS 2026.2 - CitizenTech | Estatística aplicada em Python
Script 03 - Geração do relatório estatístico em PDF (questão 07)

Entrada : resultados.json e figuras/ (gerados pelo script 02)
Saída   : relatorio_estatistico_gs_2026_2.pdf

Execução: python 03_gerar_relatorio.py
"""
import json
import platform
from importlib.metadata import version
from pathlib import Path

import matplotlib
from PIL import Image as PilImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (CondPageBreak, Image, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

PASTA = Path(__file__).resolve().parent
ARQUIVO_PDF = PASTA / "relatorio_estatistico_gs_2026_2.pdf"
r = json.loads((PASTA / "resultados.json").read_text(encoding="utf-8"))

# ------------------------------------------------------------------ fontes e estilos
# fonte DejaVu que já vem dentro do matplotlib (funciona em Windows, macOS e Linux)
DEJAVU = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
pdfmetrics.registerFont(TTFont("Corpo", str(DEJAVU / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("Corpo-Bold", str(DEJAVU / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("Corpo-Italic", str(DEJAVU / "DejaVuSans-Oblique.ttf")))
pdfmetrics.registerFont(TTFont("Corpo-BoldItalic", str(DEJAVU / "DejaVuSans-BoldOblique.ttf")))
pdfmetrics.registerFontFamily("Corpo", normal="Corpo", bold="Corpo-Bold",
                              italic="Corpo-Italic", boldItalic="Corpo-BoldItalic")

AZUL = colors.HexColor("#1f4e79")
CINZA_CLARO = colors.HexColor("#eef2f7")
CINZA = colors.HexColor("#6b7280")

corpo = ParagraphStyle("corpo", fontName="Corpo", fontSize=9.2, leading=13.4, alignment=TA_JUSTIFY,
                       spaceAfter=5)
h1 = ParagraphStyle("h1", fontName="Corpo-Bold", fontSize=14, leading=18, textColor=AZUL,
                    spaceBefore=10, spaceAfter=6, keepWithNext=1)
h2 = ParagraphStyle("h2", fontName="Corpo-Bold", fontSize=10.5, leading=14, textColor=AZUL,
                    spaceBefore=8, spaceAfter=3, keepWithNext=1)
legenda = ParagraphStyle("legenda", fontName="Corpo-Italic", fontSize=7.8, leading=10.5,
                         textColor=CINZA, alignment=TA_CENTER, spaceAfter=7)
celula = ParagraphStyle("celula", fontName="Corpo", fontSize=7.8, leading=10)
celula_b = ParagraphStyle("celula_b", parent=celula, fontName="Corpo-Bold")
topico = ParagraphStyle("topico", parent=corpo, leftIndent=12, bulletIndent=2, spaceAfter=3)
nota = ParagraphStyle("nota", parent=corpo, fontSize=8, leading=11, textColor=CINZA)
destaque = ParagraphStyle("destaque", parent=corpo, backColor=CINZA_CLARO, borderPadding=6,
                          spaceBefore=4, spaceAfter=9)


# ------------------------------------------------------------------ formatação (padrão BR)
def n(x: float, casas: int = 2) -> str:
    """Número com vírgula decimal e ponto de milhar."""
    texto = f"{x:,.{casas}f}"
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def pct(x: float, casas: int = 1) -> str:
    return n(x * 100, casas) + "%"


def pv(p: float) -> str:
    return "< 0,001" if p < 0.001 else n(p, 3)


contador = {"fig": 0, "tab": 0}
E: list = []  # elementos do documento


def P(texto: str, estilo=corpo):
    E.append(Paragraph(texto, estilo))


def T(texto: str):
    E.append(CondPageBreak(7 * cm))  # evita título no pé da página
    P(f"<b>{texto}</b>", h1)


def S(texto: str, espaco_cm: float = 6.5):
    E.append(CondPageBreak(espaco_cm * cm))  # reserva espaço para o conteúdo que vem junto
    P(texto, h2)


def topicos(itens: list[str]):
    for item in itens:
        E.append(Paragraph(item, topico, bulletText="•"))


def figura(caminho: str, largura_cm: float, texto: str):
    contador["fig"] += 1
    arq = PASTA / caminho
    w, h = PilImage.open(arq).size
    largura = largura_cm * cm
    E.append(KeepTogether([
        Image(str(arq), width=largura, height=largura * h / w),
        Paragraph(f"Figura {contador['fig']} – {texto}", legenda)]))


def tabela(linhas: list[list], larguras_cm: list[float], texto: str, cabecalho: bool = True,
           alinhar_direita_a_partir: int = 1):
    """Tabela com legenda. Células de texto viram Paragraph para quebrar linha."""
    contador["tab"] += 1
    dados = []
    for i, linha in enumerate(linhas):
        novo = []
        for j, c in enumerate(linha):
            est = celula_b if (i == 0 and cabecalho) else celula
            if j >= alinhar_direita_a_partir:
                est = ParagraphStyle("d", parent=est, alignment=2)
            novo.append(Paragraph(str(c), est))
        dados.append(novo)
    t = Table(dados, colWidths=[w * cm for w in larguras_cm], repeatRows=1 if cabecalho else 0)
    estilo = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
              ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#d0d5dd")),
              ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
              ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
    if cabecalho:
        estilo += [("BACKGROUND", (0, 0), (-1, 0), CINZA_CLARO),
                   ("LINEBELOW", (0, 0), (-1, 0), 0.8, AZUL)]
    t.setStyle(TableStyle(estilo))
    E.append(KeepTogether([Paragraph(f"Tabela {contador['tab']} – {texto}", legenda), t,
                           Spacer(1, 7)]))


# ------------------------------------------------------------------ atalhos de dados
base, q2, q3, q4, q5, q6 = r["base"], r["q2"], r["q3"], r["q4"], r["q5"], r["q6"]
desc, let = r["descritiva"], r["letalidade"]
N = base["n"]
FATAIS = base["acidentes_fatais"]


def achar(lista: list[dict], inicio: str) -> dict:
    return next(x for x in lista if x["categoria"].startswith(inicio))


atrop = achar(let["tipo_acidente"], "Atropelamento de Pedestre")
noite = achar(let["fase_dia"], "Plena Noite")
dia = achar(let["fase_dia"], "Pleno dia")
br381 = achar(let["br"], "381")
br116 = achar(let["br"], "116")
acessar = achar(let["causa_acidente"], "Acessar a via")
causas_vol = r["top_causas_volume"]

# ====================================================================== CAPA
E.append(Spacer(1, 3.2 * cm))
E.append(Paragraph("GLOBAL SOLUTION 2026.2 · DESAFIO CITIZENTECH",
                   ParagraphStyle("c0", fontName="Corpo-Bold", fontSize=10, textColor=CINZA,
                                  alignment=TA_CENTER, spaceAfter=14)))
E.append(Paragraph("Relatório estatístico",
                   ParagraphStyle("c1", fontName="Corpo-Bold", fontSize=26, leading=31,
                                  textColor=AZUL, alignment=TA_CENTER, spaceAfter=8)))
E.append(Paragraph("Acidentes nas rodovias federais de São Paulo em 2024: evidências para um "
                   "assistente digital de orientação em trânsito",
                   ParagraphStyle("c2", fontName="Corpo", fontSize=13, leading=18,
                                  alignment=TA_CENTER, spaceAfter=40)))
E.append(Paragraph("Projeto: chat despachante de trânsito (assistente digital introdutório)",
                   ParagraphStyle("c3", fontName="Corpo", fontSize=10, alignment=TA_CENTER,
                                  spaceAfter=40)))
integrantes = Table(
    [[Paragraph("<b>Integrantes (nome completo e matrícula)</b>", celula)],
     [Paragraph("[Nome completo do integrante 1] – RM [número]", celula)],
     [Paragraph("[Nome completo do integrante 2] – RM [número]", celula)],
     [Paragraph("[Nome completo do integrante 3] – RM [número, se houver]", celula)]],
    colWidths=[11 * cm])
integrantes.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), CINZA_CLARO),
                                 ("BOX", (0, 0), (-1, -1), 0.5, CINZA),
                                 ("TOPPADDING", (0, 0), (-1, -1), 5),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
E.append(integrantes)
E.append(Spacer(1, 2.6 * cm))
E.append(Paragraph("Base de dados: Polícia Rodoviária Federal (PRF), via Kaggle<br/>"
                   "Ferramentas: Python (pandas, SciPy, statsmodels, scikit-learn)<br/><br/>"
                   "São Paulo, 18 de novembro de 2026",
                   ParagraphStyle("c4", fontName="Corpo", fontSize=9, leading=14,
                                  alignment=TA_CENTER, textColor=CINZA)))
E.append(PageBreak())

# ====================================================================== SUMÁRIO EXECUTIVO
T("Sumário executivo")
P(f"Este relatório analisa os <b>{n(N, 0)} acidentes</b> registrados pela PRF nas rodovias "
  f"federais do estado de São Paulo em 2024, para apoiar o desenho de um assistente digital que "
  f"orienta cidadãos sobre trânsito. Principais achados:")
topicos([
    f"<b>Pedestres concentram a gravidade.</b> Atropelamentos de pedestres são só "
    f"{pct(atrop['n'] / N)} dos acidentes, mas respondem por {pct(atrop['fatais'] / FATAIS)} dos "
    f"acidentes com morte. A letalidade é de {pct(atrop['taxa'])}, cerca de "
    f"{n(atrop['taxa'] / base['taxa_fatal'], 0)} vezes a média geral ({pct(base['taxa_fatal'])}).",
    f"<b>A noite é mais grave.</b> A fase “plena noite” reúne {pct(noite['n'] / N)} dos acidentes e "
    f"{pct(noite['fatais'] / FATAIS)} dos acidentes fatais; a letalidade é de {pct(noite['taxa'])}, "
    f"contra {pct(dia['taxa'])} em pleno dia.",
    f"<b>Mais veículos, mais pessoas envolvidas.</b> Cada veículo adicional associa-se a "
    f"{n(q4['b1'])} pessoa a mais por acidente (r = {n(q4['pearson'], 3)}; R² = "
    f"{pct(q4['r2'])}). A relação se repete em 2018 e 2020 (fonte complementar).",
    f"<b>Prever mortes só com números é difícil.</b> A regressão logística tem AUC de "
    f"{n(q6['auc'], 2)} e acurácia de {pct(q6['aval_05']['acuracia'])}, igual ao palpite “nunca há "
    f"morte”. O modelo não generaliza para 2018 e 2020. Ele não deve servir de triagem automática.",
    f"<b>Hipóteses.</b> Com os níveis de significância pedidos (6% e 9%), as duas amostras não "
    f"rejeitam a média de referência, como esperado para amostras tiradas da própria base.",
])
P("<b>Implicação para o assistente:</b> priorizar conteúdos de orientação sobre pedestres e "
  "condução noturna, e sobre as causas mais frequentes (reação tardia, ausência de reação, "
  "distância do veículo da frente). O assistente deve informar, citar fontes e avisar que não é "
  "canal oficial, em vez de “prever” riscos individuais.", destaque)

# ====================================================================== 1. CONTEXTO
T("1. Contexto e objetivo")
P("O desafio CitizenTech pede soluções tecnológicas que melhorem concretamente a vida das "
  "pessoas, com foco aqui em <b>mobilidade e segurança viária</b>. O projeto da equipe é um "
  "<i>chat despachante de trânsito</i>: um assistente digital introdutório que organiza "
  "informações verificáveis (serviços, documentos, direitos e orientações), responde perguntas "
  "com referências e avisos de limitação, trata entradas inválidas, evita coletar dados pessoais "
  "desnecessários e não se apresenta como canal oficial.")
P("A análise estatística responde a duas perguntas de negócio: <b>(1)</b> quais situações de "
  "trânsito concentram os acidentes graves, para decidir quais orientações o assistente deve "
  "priorizar; e <b>(2)</b> quais relações numéricas entre as variáveis dos acidentes são "
  "robustas o bastante para sustentar mensagens e indicadores do protótipo.")

# ====================================================================== 2. DADOS E MÉTODO
T("2. Dados e método")
S("2.1 Fontes")
P("Os dados são registros reais de acidentes em rodovias federais, publicados como dados abertos "
  "da Polícia Rodoviária Federal (PRF) e obtidos por duas bases públicas do Kaggle, ambas com um "
  "registro por <b>ocorrência</b>:")
topicos([
    "<b>Fonte A (base principal):</b> <i>Federal Highway Accidents Dataset</i> (alinebertolani), "
    "arquivo <i>datatran20142024.csv</i>, com 947.863 registros e 30 colunas, de 2014 a 2024. "
    "https://www.kaggle.com/datasets/alinebertolani/federal-highway-accidents-dataset",
    "<b>Fonte B (complementar):</b> <i>Acidentes rodovias federais Brasil Jan/07 a Dez/20</i> "
    "(equeiroz), arquivos <i>datatran2007.csv</i> a <i>datatran2020.csv</i>. Usada para a série "
    "histórica (2007–2013, que a fonte A não cobre) e para o teste de robustez (2018 e 2020). "
    "https://www.kaggle.com/datasets/equeiroz/acidentes-rodovias-federais-brasil-jan07-a-jul19",
])
S("2.2 Recorte e tratamento")
P(f"A base do trabalho é o recorte <b>SP, 2024</b> da fonte A: {n(N, 0)} ocorrências, de "
  f"{base['periodo'].replace(' a ', ' a ')}, sem registros duplicados. O recorte reduz o arquivo "
  f"de 220 MB para cerca de 1,2 MB e mantém coerência com o tema (orientação a motoristas e "
  f"pedestres paulistas). Tratamentos aplicados:")
topicos([
    "criação de <b>hora</b> (horário em horas decimais) e de <b>houve_morte</b> (1 se o acidente "
    "teve ao menos 1 morto; 0 caso contrário);",
    "remoção de <i>latitude</i> e <i>longitude</i>, que não são usadas na análise;",
    "conversão de datas (três formatos nos arquivos) e de decimais com vírgula;",
    f"conferência de qualidade: {n(base['linhas_soma_inconsistente'], 0)} registros "
    f"({pct(base['linhas_soma_inconsistente'] / N)}) têm “pessoas” menor que a soma de mortos, "
    f"feridos, ilesos e ignorados. Foram mantidos, pois as variáveis usadas nos modelos não "
    f"dependem dessa soma; há apenas {base['nulos'].get('uop', 0)} valores ausentes (coluna "
    f"<i>uop</i>, não utilizada).",
])
S("2.3 Variáveis quantitativas")
linhas = [["Variável", "Média", "Desvio padrão", "Mín.", "Q1", "Mediana", "Q3", "Máx.", "Assimetria"]]
nomes = {"pessoas": "Pessoas envolvidas", "veiculos": "Veículos envolvidos", "feridos": "Feridos",
         "mortos": "Mortos", "km": "Km da rodovia", "hora": "Hora do dia"}
for v, nome in nomes.items():
    d = desc[v]
    linhas.append([nome, n(d["media"]), n(d["dp"]), n(d["min"], 1), n(d["q1"], 1),
                   n(d["mediana"], 1), n(d["q3"], 1), n(d["max"], 1), n(d["assimetria"])])
tabela(linhas, [3.5, 1.5, 2.2, 1.3, 1.3, 1.8, 1.3, 1.4, 2.2],
       f"Estatísticas descritivas das variáveis quantitativas (n = {n(N, 0)}).")
P("As contagens (pessoas, feridos, mortos) são fortemente assimétricas à direita: a maioria dos "
  "acidentes envolve poucas pessoas, e poucos casos extremos (ônibus, por exemplo) chegam a "
  "dezenas. Isso importa para a hipótese de normalidade das questões 2 e 3.")

# ====================================================================== 3. EXPLORATÓRIA
T("3. Análise exploratória")
P(f"Em 2024 houve <b>{n(base['mortos_total'], 0)} mortos</b> e "
  f"<b>{n(base['feridos_total'], 0)} feridos</b> em {n(base['pessoas_total'], 0)} pessoas "
  f"envolvidas. {n(FATAIS, 0)} acidentes ({pct(base['taxa_fatal'])}) tiveram ao menos uma morte.")
figura(r["fig_horas"], 11.5, "Número de acidentes por hora do dia.")
P("Há um pico de acidentes pela manhã (por volta das 7h) e outro no fim da tarde (16h às 19h), "
  "horários de maior movimento. A gravidade, porém, se concentra na noite, como mostram as "
  "figuras seguintes.")
figura(r["fig_letalidade_tipo"], 12.5, "Percentual de acidentes com morte por tipo de acidente "
       "(categorias com pelo menos 100 casos).")
tipos = let["tipo_acidente"]
P(f"O <b>atropelamento de pedestre</b> se destaca: {n(atrop['fatais'], 0)} dos {n(atrop['n'], 0)} "
  f"casos tiveram morte ({pct(atrop['taxa'])}). Nos demais tipos a letalidade fica entre 0% e "
  f"{pct(tipos[1]['taxa'])}. Colisão traseira é o tipo mais frequente ({n(achar(tipos, 'Colisão traseira')['n'], 0)} "
  f"casos), mas com letalidade de {pct(achar(tipos, 'Colisão traseira')['taxa'])}.")
figura(r["fig_letalidade_fase"], 11.5, "Percentual de acidentes com morte por fase do dia.")
P(f"A fase <b>plena noite</b> tem letalidade de {pct(noite['taxa'])}, "
  f"{n(noite['taxa'] / dia['taxa'], 1)} vez a de pleno dia ({pct(dia['taxa'])}). Por rodovia (com ao "
  f"menos 200 acidentes), a BR-381 tem letalidade de {pct(br381['taxa'])} contra "
  f"{pct(br116['taxa'])} na BR-116, a de maior volume.")
linhas = [["Causa do acidente (n ≥ 100)", "Acidentes", "Com morte", "Letalidade"]]
for c in let["causa_acidente"][:6]:
    linhas.append([c["categoria"], n(c["n"], 0), n(c["fatais"], 0), pct(c["taxa"])])
tabela(linhas, [8.4, 2.2, 2.2, 2.2], "Causas com maior letalidade (categorias com pelo menos 100 casos).")
P(f"Em volume, as causas mais registradas são “{causas_vol[0]['categoria']}” "
  f"({pct(causas_vol[0]['pct'])}) e “{causas_vol[1]['categoria']}” ({pct(causas_vol[1]['pct'])}), "
  f"juntas com {pct(causas_vol[0]['pct'] + causas_vol[1]['pct'])} dos acidentes. A causa com maior "
  f"letalidade é “Acessar a via sem observar a presença dos outros veículos” "
  f"({pct(acessar['taxa'])}). A baixa letalidade de “ingestão de álcool” "
  f"({pct(achar(let['causa_acidente'], 'Ingestão')['taxa'])}) deve ser lida com cautela, pois "
  f"a causa só é registrada quando a PRF consegue constatá-la.")

# ====================================================================== 4. Q2
T("4. Probabilidades com a distribuição normal (questão 02)")
P(f"<b>Variável escolhida:</b> pessoas envolvidas por acidente. Sob a hipótese de normalidade "
  f"pedida no enunciado, usamos X ~ N(μ = {n(q2['media'], 3)}; σ = {n(q2['dp_pop'], 3)}), com "
  f"média e desvio padrão populacional calculados sobre os {n(N, 0)} registros. A mediana dos "
  f"registros é {n(q2['mediana'], 0)}.")
P("<b>Critério de classificação do evento:</b> P = 0, impossível; 0 &lt; P &lt; 0,5, improvável; "
  "P = 0,5, equiprovável (50% de chance); 0,5 &lt; P &lt; 1, provável; P = 1, certo.")
tabela([["Item", "Cálculo", "Probabilidade", "Classificação"],
        ["a) P(X &lt; média)", "Φ((μ − μ)/σ) = Φ(0)", n(q2["p_menor_media"], 4), q2["classe_a"]],
        ["b) P(X &gt; mediana)",
         f"1 − Φ(({n(q2['mediana'], 0)} − {n(q2['media'], 3)})/{n(q2['dp_pop'], 3)}) = 1 − Φ({n(q2['z_mediana'], 3)})",
         n(q2["p_maior_mediana"], 4), q2["classe_b"]]],
       [3.2, 7.0, 2.6, 3.6], "Probabilidades sob a distribuição normal.", alinhar_direita_a_partir=2)
figura(r["fig_q2"], 11.5, "Histograma de pessoas por acidente e curva normal ajustada.")
P(f"<b>Interpretação.</b> Na normal, a média é o ponto central, então P(X &lt; média) é exatamente "
  f"50%. Já a mediana ({n(q2['mediana'], 0)}) fica abaixo da média ({n(q2['media'], 2)}), o que dá "
  f"P(X &gt; mediana) = {pct(q2['p_maior_mediana'])}: evento <b>provável</b>. "
  f"<b>Limitação importante:</b> os dados reais são muito assimétricos (assimetria = "
  f"{n(q2['assimetria'], 1)}), e a hipótese de normalidade não se sustenta. Nos dados, "
  f"{pct(q2['freq_menor_media'])} dos acidentes têm menos pessoas que a média (a normal prevê 50%) e "
  f"apenas {pct(q2['freq_maior_mediana'])} têm mais pessoas que a mediana (a normal prevê "
  f"{pct(q2['p_maior_mediana'])}). Os resultados valem como exercício sob a hipótese pedida, não "
  f"como descrição fiel da variável.")

# ====================================================================== 5. Q3
T("5. Testes de hipóteses para a média (questão 03)")
P(f"Variável: pessoas envolvidas por acidente. Média populacional de referência μ₀ = "
  f"{n(q3['a']['mu0'], 3)} e desvio padrão populacional σ = {n(q3['a']['sigma'], 3)} (calculados "
  f"sobre toda a base). Como σ é conhecido, usa-se o <b>teste Z</b>: Z = (x̄ − μ₀) / (σ/√n). As "
  f"amostras foram sorteadas sem reposição da base, com semente {q3['semente']} (reprodutível).")
a, b = q3["a"], q3["b"]
linhas = [["Item", "a)", "b)"],
          ["Hipóteses", "H₀: μ = μ₀  ×  H₁: μ &lt; μ₀ (unilateral à esquerda)",
           "H₀: μ = μ₀  ×  H₁: μ &gt; μ₀ (unilateral à direita)"],
          ["Nível de significância α", pct(a["alpha"], 0), pct(b["alpha"], 0)],
          ["Tamanho da amostra n", n(a["n"], 0), n(b["n"], 0)],
          ["Média amostral x̄", n(a["xbar"], 3), n(b["xbar"], 3)],
          ["Erro padrão σ/√n", n(a["erro_padrao"], 4), n(b["erro_padrao"], 4)],
          ["Estatística Z calculada", n(a["z"], 3), n(b["z"], 3)],
          ["Z crítico", n(a["z_critico"], 3), n(b["z_critico"], 3)],
          ["p-valor", n(a["p_valor"], 4), n(b["p_valor"], 4)],
          ["Decisão", "Não rejeita H₀" if not a["rejeita_h0"] else "Rejeita H₀",
           "Não rejeita H₀" if not b["rejeita_h0"] else "Rejeita H₀"]]
tabela(linhas, [4.6, 6.4, 6.4], "Testes Z para a média de pessoas por acidente.")
P(f"<b>Interpretação.</b> Em (a), Z = {n(a['z'], 3)} não é menor que o valor crítico "
  f"{n(a['z_critico'], 3)} (p = {n(a['p_valor'], 3)} &gt; α): não há evidência, ao nível de "
  f"{pct(a['alpha'], 0)}, de que a média seja menor que a de referência. Em (b), Z = {n(b['z'], 3)} "
  f"não supera {n(b['z_critico'], 3)} (p = {n(b['p_valor'], 3)} &gt; α): não há evidência, ao nível "
  f"de {pct(b['alpha'], 0)}, de que seja maior. O resultado era esperado: as amostras vêm da "
  f"própria base cuja média é a referência, então H₀ é verdadeira. A decisão vale para esta amostra "
  f"específica.")
P(f"<b>Verificação de rigor.</b> Repetindo o teste em 5.000 amostras aleatórias, a taxa de "
  f"rejeição de H₀ (que deveria ser próxima de α) foi de {pct(a['rejeicao_simulada'])} em (a) "
  f"(nominal: {pct(a['alpha'], 0)}) e {pct(b['rejeicao_simulada'])} em (b) (nominal: "
  f"{pct(b['alpha'], 0)}). O teste da cauda esquerda fica muito conservador porque a variável é "
  f"assimétrica à direita e as amostras são pequenas. Isso reforça a cautela sobre a hipótese de "
  f"normalidade.", nota)

# ====================================================================== 6. Q4
T("6. Análise bivariada (questão 04)")
P(f"<b>Variáveis:</b> X = veículos envolvidos (explicativa) e Y = pessoas envolvidas (resposta). "
  f"A pergunta prática é: quantas pessoas, em média, o acidente envolve conforme o número de "
  f"veículos, informação útil para dimensionar o atendimento.")
S("a) Gráfico de dispersão", 10.5)
figura(r["fig_q4_disp"], 12.5, "Dispersão entre veículos e pessoas envolvidas, com a reta de "
       "regressão. Como as variáveis são contagens inteiras, os pontos têm um pequeno desvio "
       "apenas visual; o cálculo usa os valores originais.")
P("<b>Interpretação.</b> A nuvem tem inclinação positiva: acidentes com mais veículos tendem a "
  "envolver mais pessoas. A maior parte dos casos está entre 1 e 4 veículos. Há pontos isolados "
  "no alto do gráfico, com 30 a 45 pessoas em 1 a 3 veículos, compatíveis com acidentes com "
  "ônibus. Eles puxam a reta para cima e explicam parte da dispersão.")
S("b) Covariância e correlação linear de Pearson")
tabela([["Medida", "Valor"],
        ["Covariância amostral (veículos, pessoas)", n(q4["covariancia"], 4)],
        ["Correlação linear de Pearson (r)", n(q4["pearson"], 4)],
        ["p-valor do teste de correlação", pv(q4["p_pearson"])]],
       [9, 3.5], "Covariância e correlação entre veículos e pessoas envolvidas.")
P(f"<b>Interpretação.</b> A covariância positiva ({n(q4['covariancia'], 3)}) confirma que as "
  f"variáveis crescem juntas, mas seu valor depende das unidades. O coeficiente r = "
  f"{n(q4['pearson'], 3)} indica correlação linear <b>positiva e moderada</b> e é "
  f"estatisticamente significativo (p {pv(q4['p_pearson'])}).")
S("c) Gráfico da correlação linear de Pearson", 9)
figura(r["fig_q4_corr"], 7.2, "Mapa de calor da correlação de Pearson.")
P(f"<b>Interpretação.</b> O mapa mostra r = {n(q4['pearson'], 3)} entre as duas variáveis (a "
  f"diagonal é 1 por definição). A cor intermediária indica relação moderada, e não forte.")
S("d) Reta de regressão linear simples")
P(f"A reta ajustada pelo método dos mínimos quadrados aparece na Figura 5. A equação é:")
P(f"<b>Pessoas = {n(q4['b0'], 4)} + {n(q4['b1'], 4)} × Veículos</b>", destaque)
P(f"O coeficiente angular indica que, em média, <b>cada veículo adicional se associa a "
  f"{n(q4['b1'], 2)} pessoa a mais</b> no acidente (IC 95%: {n(q4['ic_b1'][0], 3)} a "
  f"{n(q4['ic_b1'][1], 3)}). O intercepto ({n(q4['b0'], 2)}) é o valor esperado com zero veículo, "
  f"sem significado prático; o mínimo observado é 1 veículo.")
S("e) Adequação do modelo (R² e teste F)")
tabela([["Medida", "Valor"],
        ["R²", pct(q4["r2"], 2)], ["R² ajustado", pct(q4["r2_aj"], 2)],
        [f"Estatística F (gl = {q4['df_modelo']}; {n(q4['df_resid'], 0)})", n(q4["F"], 1)],
        ["p-valor do teste F", pv(q4["p_F"])],
        ["p-valor do teste de Breusch–Pagan (variância dos resíduos)", n(q4["bp_p"], 3)]],
       [10, 3.5], "Adequação do modelo de regressão simples.")
P(f"<b>Interpretação.</b> O teste F tem hipótese nula de que o coeficiente angular é zero. Com "
  f"F = {n(q4['F'], 1)} e p {pv(q4['p_F'])}, rejeitamos H₀: o modelo é <b>significativo</b>. O "
  f"R² de {pct(q4['r2'])} mostra que os veículos explicam cerca de um quinto da variação de "
  f"pessoas; o restante depende de outros fatores (tipo de veículo, ocupação). O teste de "
  f"Breusch–Pagan (p = {n(q4['bp_p'], 2)}) não indica problema de variância dos resíduos.")
figura(r["fig_q4_res"], 11.0, "Resíduos × valores ajustados.")
S("f) Previsão")
pr = q4["previsao"]
P(f"Para um acidente com <b>{pr['x']} veículos</b>, o modelo prevê "
  f"<b>{n(pr['y'], 2)} pessoas envolvidas</b>. O intervalo de confiança de 95% para a média é "
  f"{n(pr['ic_inf'], 2)} a {n(pr['ic_sup'], 2)}. Para um acidente individual, o intervalo de "
  f"previsão é de 0 a {n(pr['pi_sup'], 1)} (o limite inferior calculado, {n(pr['pi_inf'], 3)}, é "
  f"truncado em zero, pois não existe número negativo de pessoas). Em termos práticos, um "
  f"acidente com 3 veículos envolve em média cerca de 3 a 4 pessoas.")

# ====================================================================== 7. Q5
T("7. Análise multivariada: regressão linear múltipla (questão 05)")
P(f"<b>Variáveis:</b> Y = feridos (resposta) e X = pessoas envolvidas, veículos envolvidos e km da "
  f"rodovia. Uso prático: estimar o número de feridos a partir do que se sabe no início da "
  f"ocorrência, para dimensionar socorro. <b>Atenção:</b> feridos fazem parte das pessoas "
  f"envolvidas, então parte da relação é mecânica; o modelo serve para estimativa, não para "
  f"explicação causal.")
S("a) Gráfico de dispersão", 14.5)
figura(r["fig_q5_disp"], 12.5, "Matriz de dispersão entre feridos, pessoas, veículos e km.")
P("<b>Interpretação.</b> A única relação visível é entre feridos e pessoas (os pontos formam uma "
  "“escada”, pois feridos nunca superam pessoas). Veículos e pessoas também crescem juntos. O km "
  "da rodovia não mostra padrão com nenhuma variável; os dois blocos de km (até cerca de 230 e "
  "acima de 280) refletem as rodovias diferentes do estado.")
S("b) Matrizes de covariância e de correlação")
vars5 = ["feridos", "pessoas", "veiculos", "km"]
rot5 = {"feridos": "Feridos", "pessoas": "Pessoas", "veiculos": "Veículos", "km": "Km"}
cov_l = [[""] + [rot5[v] for v in vars5]] + [[rot5[a_]] + [n(q5["cov"][a_][b_], 3) for b_ in vars5]
                                             for a_ in vars5]
cor_l = [[""] + [rot5[v] for v in vars5]] + [[rot5[a_]] + [n(q5["corr"][a_][b_], 3) for b_ in vars5]
                                             for a_ in vars5]
tabela(cov_l, [3.0, 2.6, 2.6, 2.6, 2.8], "Matriz de covariância amostral.")
tabela(cor_l, [3.0, 2.6, 2.6, 2.6, 2.8], "Matriz de correlação linear de Pearson.")
c = q5["corr"]
P(f"<b>Interpretação.</b> As correlações mais fortes são feridos–pessoas (r = "
  f"{n(c['feridos']['pessoas'], 3)}) e pessoas–veículos (r = {n(c['pessoas']['veiculos'], 3)}). "
  f"Feridos e veículos quase não se correlacionam (r = {n(c['feridos']['veiculos'], 3)}). O km tem "
  f"correlação praticamente nula com todas as variáveis (|r| ≤ 0,03). Como o km é medido "
  f"separadamente em cada rodovia, a comparação direta entre rodovias não tem significado físico, e "
  f"a covariância do km é grande apenas pela escala (centenas de km).")
S("c) Gráfico da correlação linear de Pearson", 9)
figura(r["fig_q5_corr"], 8.2, "Mapa de calor da matriz de correlação.")
P("<b>Interpretação.</b> O mapa confirma o que a matriz mostra: apenas as relações entre "
  "contagens (feridos, pessoas, veículos) têm intensidade moderada. Não há risco de "
  "multicolinearidade forte entre as explicativas.")
S("d) Equação da regressão linear múltipla")
co = q5["coef"]
sinal = lambda v: "+" if v >= 0 else "−"  # noqa: E731
P(f"<b>Feridos = {n(co['const'], 4)} {sinal(co['pessoas'])} {n(abs(co['pessoas']), 4)} × Pessoas "
  f"{sinal(co['veiculos'])} {n(abs(co['veiculos']), 4)} × Veículos {sinal(co['km'])} "
  f"{n(abs(co['km']), 4)} × Km</b>", destaque)
linhas = [["Termo", "Coeficiente", "Erro padrão", "t", "p-valor", "p-valor robusto (HC3)", "VIF"]]
for k, nome in (("const", "Intercepto"), ("pessoas", "Pessoas"), ("veiculos", "Veículos"), ("km", "Km")):
    linhas.append([nome, n(q5["coef"][k], 4), n(q5["ep"][k], 4), n(q5["t"][k], 2), pv(q5["p"][k]),
                   pv(q5["p_robusto"][k]), n(q5["vif"][k], 2) if k in q5["vif"] else "–"])
tabela(linhas, [2.6, 2.4, 2.4, 1.6, 2.2, 3.6, 1.6], "Coeficientes da regressão múltipla.")
P(f"<b>Interpretação.</b> Mantidas as demais variáveis constantes: cada pessoa adicional "
  f"associa-se a <b>{n(co['pessoas'], 2)} ferido a mais</b>; cada veículo adicional, a "
  f"<b>{n(abs(co['veiculos']), 2)} ferido a menos</b> (com o mesmo número de pessoas, mais veículos "
  f"significam mais ocupantes ilesos); o efeito do km é praticamente nulo ("
  f"{n(co['km'] * 100, 3)} ferido a cada 100 km, apesar de significativo). O fator de inflação da "
  f"variância (VIF ≤ {n(max(q5['vif'].values()), 2)}) mostra ausência de multicolinearidade.")
S("e) Adequação do modelo (R² e teste F)")
tabela([["Medida", "Valor"], ["R²", pct(q5["r2"], 2)], ["R² ajustado", pct(q5["r2_aj"], 2)],
        [f"Estatística F (gl = {q5['df_modelo']}; {n(q5['df_resid'], 0)})", n(q5["F"], 1)],
        ["p-valor do teste F", pv(q5["p_F"])],
        ["p-valor do teste de Breusch–Pagan", pv(q5["bp_p"])]],
       [10, 3.5], "Adequação do modelo de regressão múltipla.")
P(f"<b>Interpretação.</b> O teste F rejeita a hipótese de que todos os coeficientes são nulos "
  f"(F = {n(q5['F'], 1)}; p {pv(q5['p_F'])}): o modelo é <b>globalmente significativo</b>. O R² "
  f"ajustado de {pct(q5['r2_aj'])} indica poder explicativo modesto, e o modelo não deve ser "
  f"usado para previsões precisas. O teste de Breusch–Pagan acusa <b>heterocedasticidade</b> "
  f"(variância dos resíduos não constante), o que é esperado em contagens. Por isso conferimos os "
  f"p-valores com erros-padrão robustos (HC3): todos os coeficientes seguem significativos.")
S("f) Previsão com duas ou mais variáveis explicativas")
pr5 = q5["previsao"]
e5 = pr5["entrada"]
P(f"Para um acidente com <b>{e5['pessoas']} pessoas</b>, <b>{e5['veiculos']} veículos</b> no "
  f"<b>km {e5['km']}</b>, o modelo prevê <b>{n(pr5['y'], 2)} feridos</b>. O intervalo de previsão "
  f"de 95% vai de 0 a {n(pr5['pi_sup'], 1)} feridos (o limite inferior calculado, "
  f"{n(pr5['pi_inf'], 2)}, é truncado em zero). A amplitude do intervalo confirma a incerteza do "
  f"modelo para casos individuais.")

# ====================================================================== 8. Q6
T("8. Regressão logística binária (questão 06)")
P(f"<b>Variável resposta:</b> houve_morte (1 = acidente com pelo menos 1 morto; 0 = sem morte). "
  f"<b>Explicativas:</b> pessoas, veículos, km e hora do dia. A base foi dividida em treino "
  f"({n(q6['n_treino'], 0)} acidentes, {n(q6['fatais_treino'], 0)} com morte) e teste "
  f"({n(q6['n_teste'], 0)} acidentes, {n(q6['fatais_teste'], 0)} com morte), com divisão "
  f"estratificada e semente 42. O evento é raro ({pct(base['taxa_fatal'])}), o que condiciona toda "
  f"a avaliação.")
S("a) Equação da regressão logística")
cf = q6["coef"]
P(f"<b>ln( p / (1 − p) ) = {n(cf['const'], 4)} + {n(cf['pessoas'], 4)} × Pessoas + "
  f"{n(cf['veiculos'], 4)} × Veículos + {n(cf['km'], 5)} × Km {sinal(cf['hora'])} "
  f"{n(abs(cf['hora']), 4)} × Hora</b>", destaque)
P("em que p é a probabilidade de o acidente ter morte, ou seja, p = 1 / (1 + e<super>−z</super>), "
  "com z igual ao lado direito da equação.")
linhas = [["Variável", "Coeficiente", "p-valor", "Razão de chances", "IC 95% da razão"]]
for k, nome in (("pessoas", "Pessoas"), ("veiculos", "Veículos"), ("km", "Km"), ("hora", "Hora")):
    o = q6["odds"][k]
    linhas.append([nome, n(cf[k], 5), pv(q6["p"][k]), n(o[0], 3), f"{n(o[1], 3)} a {n(o[2], 3)}"])
tabela(linhas, [3.0, 2.8, 2.4, 3.4, 3.8], "Coeficientes e razões de chances do modelo logístico (treino).")
o = q6["odds"]
P(f"<b>Interpretação.</b> Cada veículo adicional multiplica a chance de morte por "
  f"<b>{n(o['veiculos'][0], 2)}</b> (aumento de {n((o['veiculos'][0] - 1) * 100, 0)}%), e cada "
  f"pessoa adicional por <b>{n(o['pessoas'][0], 2)}</b> (aumento de "
  f"{n((o['pessoas'][0] - 1) * 100, 0)}%); ambos significativos. Km e hora do dia não são "
  f"significativos (p = {n(q6['p']['km'], 2)} e {n(q6['p']['hora'], 2)}). O pseudo-R² de McFadden é "
  f"de apenas {n(q6['pseudo_r2'], 3)}: o modelo é melhor que um modelo sem variáveis "
  f"(p {pv(q6['llr_p'])}), mas explica muito pouco.")
S("b) Matriz de confusão e acurácia", 9)
figura(r["fig_q6_conf"], 14.0, "Matrizes de confusão no conjunto de teste, com dois limiares de "
       "classificação.")
a5, ap = q6["aval_05"], q6["aval_prev"]
tabela([["Medida", "Limiar 0,50", f"Limiar {n(ap['limiar'], 3)} (prevalência)"],
        ["Verdadeiros negativos", n(a5["vn"], 0), n(ap["vn"], 0)],
        ["Falsos positivos", n(a5["fp"], 0), n(ap["fp"], 0)],
        ["Falsos negativos", n(a5["fn"], 0), n(ap["fn"], 0)],
        ["Verdadeiros positivos", n(a5["vp"], 0), n(ap["vp"], 0)],
        ["Acurácia", pct(a5["acuracia"], 2), pct(ap["acuracia"], 2)],
        ["Sensibilidade (acerta os fatais)", pct(a5["sensibilidade"], 1), pct(ap["sensibilidade"], 1)],
        ["Especificidade", pct(a5["especificidade"], 1), pct(ap["especificidade"], 1)],
        ["Precisão (dos alertas, quantos são fatais)", pct(a5["precisao"], 1), pct(ap["precisao"], 1)]],
       [7.4, 3.6, 5.0], "Desempenho do modelo no conjunto de teste.")
P(f"<b>Interpretação.</b> Com o limiar-padrão de 0,50, a acurácia é de <b>{pct(a5['acuracia'], 1)}</b>, "
  f"mas isso é enganoso: o modelo nunca prevê morte (sensibilidade de {pct(a5['sensibilidade'], 0)}), "
  f"e a acurácia é igual à do palpite “nenhum acidente tem morte” "
  f"({pct(q6['acuracia_base'], 1)}). É a armadilha de classes desbalanceadas. Com o limiar igual à "
  f"prevalência ({n(ap['limiar'], 3)}), o modelo identifica {pct(ap['sensibilidade'], 0)} dos "
  f"acidentes fatais, mas a acurácia cai para {pct(ap['acuracia'], 1)} e só "
  f"{pct(ap['precisao'], 1)} dos alertas são realmente fatais. A AUC de {n(q6['auc'], 2)} (0,5 = "
  f"acaso; 1,0 = perfeito) confirma <b>capacidade discriminatória fraca</b>.")
S("c) Classificação com duas ou mais variáveis explicativas")
pv6 = q6["previsao"]
e6 = pv6["entrada"]
P(f"Para um acidente com <b>{e6['pessoas']} pessoas</b>, <b>{e6['veiculos']} veículos</b>, "
  f"<b>km {e6['km']}</b> às <b>{e6['hora']} h</b>, o modelo estima probabilidade de morte de "
  f"<b>{pct(pv6['prob'], 2)}</b>. Com o limiar 0,50, a classe é <b>“{pv6['classe_05']}”</b>; com "
  f"o limiar de prevalência ({n(ap['limiar'], 3)}), seria “{pv6['classe_prev']}”, por margem "
  f"mínima. A decisão depende do limiar, e um alerta desse tipo teria precisão baixa. Por isso o "
  f"modelo não é recomendado como triagem automática.")

# ====================================================================== 9. FONTE B
T("9. Série histórica e robustez (fonte complementar)")
S("9.1 Série histórica de São Paulo (2007–2024)")
figura(r["serie"]["fig"], 13.0, "Acidentes registrados e percentual com morte por ano, rodovias "
       "federais de SP, nas duas fontes.")
sr = r["serie"]
P(f"A fonte B estende a série para trás: em 2007–2013 foram registrados entre "
  f"{n(min(sr['acidentes_b'][str(a_)] for a_ in range(2007, 2014)), 0)} e "
  f"{n(max(sr['acidentes_b'][str(a_)] for a_ in range(2007, 2014)), 0)} acidentes por ano em SP, "
  f"contra {n(sr['acidentes_a']['2024'], 0)} em 2024. A queda forte entre 2014 e 2018 pode refletir "
  f"mudanças nos critérios e sistemas de registro da PRF, além de mudanças reais no trânsito; "
  f"este trabalho não separa os dois efeitos. Por isso a <b>letalidade</b> (de "
  f"{pct(sr['taxa_b']['2013'])} em 2013 para {pct(sr['taxa_b']['2020'])} em 2020 e "
  f"{pct(sr['taxa_a']['2024'])} em 2024) deve ser lida com cuidado: o denominador mudou.")
linhas = [["Ano", "Acidentes (fonte A)", "Acidentes (fonte B)", "Diferença"]]
for s_ in sr["sobreposicao"]:
    linhas.append([s_["ano"], n(s_["n_a"], 0), n(s_["n_b"], 0), pct(s_["dif_pct"], 2)])
tabela(linhas, [2.4, 4.2, 4.2, 3.0], "Conferência entre as duas fontes nos anos em comum (SP).")
P(f"As fontes coincidem exatamente em 2014, 2015, 2016 e 2020, e diferem em até "
  f"{pct(max(abs(s_['dif_pct']) for s_ in sr['sobreposicao']), 2)} em 2017 e 2018 (provável "
  f"atualização posterior dos dados na fonte A). Os pacotes não são totalmente iguais: o arquivo "
  f"da fonte B enviado não inclui 2019, e a fonte A não cobre 2007–2013.")
S("9.2 Robustez dos modelos em outros períodos")
linhas = [["Período", "n", "% com morte", "r", "Inclinação", "R²", "RC veículos (p)",
           "RC pessoas (p)", "AUC (modelo 2024)"]]
for x_ in r["robustez"]:
    linhas.append([x_["periodo"].replace(" (fonte A, base do trabalho)", " (base)")
                   .replace(" (fonte B)", " (B)"), n(x_["n"], 0), pct(x_["taxa_fatal"]),
                   n(x_["r"], 3), n(x_["b1"], 2), pct(x_["r2"]),
                   f"{n(x_['or_veiculos'], 2)} ({pv(x_['p_veiculos'])})",
                   f"{n(x_['or_pessoas'], 2)} ({pv(x_['p_pessoas'])})", n(x_["auc_modelo_2024"], 2)])
tabela(linhas, [2.6, 1.2, 1.5, 1.2, 1.9, 1.3, 2.6, 2.6, 1.9],
       "Os mesmos modelos em SP 2018 e 2020 (fonte B) e em 2024. r e inclinação: veículos × pessoas; RC = razão de chances.")
P("<b>Interpretação.</b> A <b>regressão simples é estável</b>: correlação entre 0,47 e 0,48 e R² "
  "de 22% a 23% nos três períodos; a inclinação varia de 0,88 a 1,16 pessoa por veículo. Já a "
  "<b>regressão logística não é estável</b>: a razão de chances de veículos é maior que 1 em 2024, "
  "mas menor que 1 (sem significância) em 2018 e 2020, e o modelo treinado em 2024 praticamente "
  "não discrimina acidentes fatais nesses anos (AUC próxima de 0,5). Só o efeito de pessoas "
  "(razão de chances perto de 1,06 a 1,09) se repete. A conclusão é que variáveis numéricas "
  "simples não bastam para prever a morte em um acidente.")

# ====================================================================== 10. INSIGHTS
T("10. Insights e recomendações para o chat despachante de trânsito")
topicos([
    f"<b>Priorizar orientações sobre pedestres.</b> Atropelamentos concentram "
    f"{pct(atrop['fatais'] / FATAIS)} dos acidentes fatais. Conteúdos sobre travessia segura, "
    f"visibilidade e responsabilidades de motoristas e pedestres têm o maior potencial de reduzir "
    f"gravidade.",
    f"<b>Reforçar a condução noturna e a atenção ao entrar na via.</b> A letalidade noturna é "
    f"{n(noite['taxa'] / dia['taxa'], 1)} vez a diurna, e “acessar a via sem observar os outros "
    f"veículos” tem a maior letalidade entre as causas ({pct(acessar['taxa'])}).",
    f"<b>Cobrir as causas mais frequentes.</b> Reação tardia ou ausente do condutor e distância do "
    f"veículo da frente somam grande parte dos acidentes; são temas simples de ensinar em uma "
    f"conversa.",
    "<b>Não prever risco individual.</b> Os modelos têm baixo poder preditivo e não generalizam "
    "entre anos. O assistente deve informar com base em fontes verificáveis, e não calcular "
    "“probabilidade de morte” para o usuário.",
    "<b>Indicadores do protótipo.</b> Esta base não mede acerto das orientações, tempo para "
    "encontrar a informação nem facilidade de uso. Esses indicadores devem vir do teste com "
    "usuários, usando os temas acima como roteiro de perguntas.",
    "<b>Avisos obrigatórios.</b> O assistente deve citar a fonte de cada orientação, informar o "
    "ano e o escopo dos dados (rodovias federais de SP, 2024) e declarar que não é canal oficial.",
])
S("Limitações")
topicos([
    "A base cobre apenas <b>rodovias federais</b> de SP, e não vias urbanas ou estaduais. Os "
    "resultados não representam todo o trânsito paulista.",
    "As relações são <b>associações</b>, não causalidade.",
    "Os dados são <b>registros da PRF</b>: acidentes sem atendimento e causas de difícil "
    "constatação (como álcool) tendem a ser sub-registrados.",
    "A hipótese de normalidade (questões 2 e 3) não se verifica nos dados reais; os resultados "
    "valem como exercício sob a hipótese pedida.",
    "O evento “houve morte” é raro (4,4%), o que limita a avaliação do modelo logístico (64 "
    "casos positivos no teste).",
    "A fonte B enviada não contém o ano de 2019, e a queda de registros entre 2014 e 2018 pode "
    "ter componente metodológico.",
])

# ====================================================================== REFERÊNCIAS
T("Referências e reprodutibilidade")
topicos([
    "ALINEBERTOLANI. <i>Federal Highway Accidents Dataset</i>. Kaggle. Arquivo "
    "datatran20142024.csv. Disponível em: "
    "https://www.kaggle.com/datasets/alinebertolani/federal-highway-accidents-dataset.",
    "EQUEIROZ. <i>Acidentes rodovias federais Brasil Jan/07 a Dez/20</i>. Kaggle. Arquivos "
    "datatran2007.csv a datatran2020.csv. Disponível em: "
    "https://www.kaggle.com/datasets/equeiroz/acidentes-rodovias-federais-brasil-jan07-a-jul19.",
    "Origem dos dados nas duas bases: registros de ocorrências da Polícia Rodoviária Federal (PRF).",
])
versoes = ", ".join(f"{p_} {version(p_)}" for p_ in
                    ("pandas", "numpy", "scipy", "statsmodels", "scikit-learn", "matplotlib",
                     "seaborn", "reportlab"))
P(f"<b>Código:</b> 01_preparar_base.py (recorte e tratamento), 02_analise_estatistica.py "
  f"(questões 02 a 06, figuras e resultados.json) e 03_gerar_relatorio.py (este PDF). "
  f"Semente aleatória: 42. Python {platform.python_version()}; {versoes}.", nota)

# ====================================================================== PDF
def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Corpo", 7.5)
    canvas.setFillColor(CINZA)
    if doc.page > 1:
        canvas.drawString(2 * cm, 1.2 * cm, "Relatório estatístico · GS 2026.2 CitizenTech · "
                          "Acidentes em rodovias federais de SP (2024)")
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(str(ARQUIVO_PDF), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                        topMargin=1.8 * cm, bottomMargin=2 * cm,
                        title="Relatório estatístico – GS 2026.2 CitizenTech",
                        author="Equipe GS 2026.2", subject="Acidentes em rodovias federais de SP")
doc.build(E, onFirstPage=rodape, onLaterPages=rodape)
print("Relatório gerado:", ARQUIVO_PDF.name)
