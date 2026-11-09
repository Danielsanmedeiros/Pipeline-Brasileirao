"""Painel do Brasileirão: lê só a camada marts, sem nenhum cálculo na tela.

Uso:  streamlit run dashboard/app.py   (depois de python -m pipeline.run)

Regra: todo número exibido aqui sai pronto de uma tabela marts.*. O painel só
seleciona linhas (filtro por temporada) e escolhe como desenhar. Se um número
precisar de conta, a conta vai para um .sql em sql/marts/, não para este arquivo.
"""

from pathlib import Path

import altair as alt
import duckdb
import pandas as pd
import streamlit as st

BANCO = Path(__file__).resolve().parent.parent / "data" / "brasileirao.duckdb"
REPO = "https://github.com/Danielsanmedeiros/Pipeline-Brasileirao"
ORDEM_FAIXAS = ["01-15", "16-30", "31-45", "45+", "46-60", "61-75", "76-90", "90+"]

st.set_page_config(page_title="Brasileirão em dados", page_icon=":material/sports_soccer:", layout="wide")


@st.cache_data
def ler_mart(tabela: str) -> pd.DataFrame:
    """Lê uma tabela inteira da camada marts. Única fonte de dados do painel."""
    with duckdb.connect(str(BANCO), read_only=True) as con:
        return con.execute(f"select * from marts.{tabela}").df()


if not BANCO.exists():
    st.error("Rode antes: python -m pipeline.download e python -m pipeline.run", title="Banco não encontrado")
    st.stop()

classificacao = ler_mart("classificacao")
mando = ler_mart("mando_de_campo")
gols_faixa = ler_mart("gols_por_faixa")
disciplina = ler_mart("disciplina_clube")
finalizacao = ler_mart("finalizacao_clube")

# ---------- cabeçalho e filtro ----------

st.title("Brasileirão em dados, 2003–2025")
st.caption(
    f"Série A, 9.165 partidas. Fonte: Kaggle (Adão Duque, GPL 2). "
    f"Cada número vem de uma tabela da camada marts — código em [GitHub]({REPO})."
)

temporadas = sorted(mando["temporada"].tolist(), reverse=True)
temporada = st.selectbox("Temporada", temporadas, index=0, key="temporada")

campeao = classificacao.query("temporada == @temporada and posicao == 1").iloc[0]
mando_t = mando.query("temporada == @temporada").iloc[0]

with st.container(horizontal=True):
    st.metric("Campeão", campeao["clube"], border=True)
    st.metric("Pontos do campeão", int(campeao["pontos"]), border=True)
    st.metric("Vitórias do mandante", f"{mando_t['pct_vitoria_mandante']:.1%}", border=True)
    st.metric("Gols por jogo", f"{mando_t['gols_por_jogo']:.2f}", border=True)

# ---------- mando de campo (todas as temporadas) ----------

with st.container(border=True):
    st.subheader("Jogar em casa ainda dá vantagem?")
    st.caption(
        "Resultado das partidas por temporada. 2020 foi inteira sem torcida. A vitória do mandante "
        "caiu para 45%, mas 2017, com torcida, ficou abaixo disso: o dado mostra uma queda mais longa, "
        "não um efeito só da pandemia. — `marts.mando_de_campo`"
    )
    mando_longo = mando.melt(
        id_vars="temporada",
        value_vars=["pct_vitoria_mandante", "pct_empate", "pct_vitoria_visitante"],
        var_name="resultado",
        value_name="percentual",
    ).replace({"pct_vitoria_mandante": "Vitória do mandante", "pct_empate": "Empate",
               "pct_vitoria_visitante": "Vitória do visitante"})
    linhas = (
        alt.Chart(mando_longo)
        .mark_line(point=True)
        .encode(
            x=alt.X("temporada:O", title=None),
            y=alt.Y("percentual:Q", title="% das partidas", axis=alt.Axis(format="%")),
            color=alt.Color("resultado:N", title=None, sort=["Vitória do mandante", "Empate", "Vitória do visitante"],
                            legend=alt.Legend(orient="top")),
            tooltip=[alt.Tooltip("temporada:O", title="Temporada"), alt.Tooltip("resultado:N", title="Resultado"),
                     alt.Tooltip("percentual:Q", title="Percentual", format=".1%")],
        )
    )
    sem_torcida = alt.Chart(pd.DataFrame({"temporada": [2020], "rotulo": ["sem torcida"]})).mark_rule(
        strokeDash=[4, 4], color="gray"
    ).encode(x="temporada:O")
    st.altair_chart(linhas + sem_torcida, alt="Vitória do mandante caiu de cerca de 50% para 45% a 47% desde 2017")

# ---------- classificação e gols por minuto ----------

col_tabela, col_gols = st.columns([1.1, 1])

with col_tabela, st.container(border=True, height="stretch"):
    st.subheader(f"Classificação {temporada}")
    st.caption("Classificação esportiva, sem punições de tribunal. — `marts.classificacao`")
    st.dataframe(
        classificacao.query("temporada == @temporada")[
            ["posicao", "clube", "pontos", "jogos", "vitorias", "empates", "derrotas", "saldo_gols", "aproveitamento"]
        ],
        hide_index=True,
        height=420,
        column_config={
            "posicao": st.column_config.NumberColumn("#", width="small"),
            "clube": "Clube",
            "pontos": "Pts",
            "jogos": "J",
            "vitorias": "V",
            "empates": "E",
            "derrotas": "D",
            "saldo_gols": "SG",
            "aproveitamento": st.column_config.ProgressColumn("Aproveit.", format="percent", min_value=0, max_value=1),
        },
        alt=f"Classificação do Brasileirão {temporada}",
    )

with col_gols, st.container(border=True, height="stretch"):
    st.subheader("Quando saem os gols")
    st.caption("% dos gols da temporada por faixa de minuto; acréscimos separados. — `marts.gols_por_faixa`")
    gols_t = gols_faixa.query("temporada == @temporada")
    if gols_t.empty:
        st.info("A fonte só tem gols por minuto a partir de 2014.", icon=":material/info:")
    else:
        barras = (
            alt.Chart(gols_t)
            .mark_bar()
            .encode(
                x=alt.X("faixa:N", sort=ORDEM_FAIXAS, title="Minuto"),
                y=alt.Y("pct_gols_temporada:Q", title="% dos gols", axis=alt.Axis(format="%")),
                color=alt.condition(alt.FieldOneOfPredicate("faixa", ["45+", "90+"]),
                                    alt.value("#E4572E"), alt.value("#4C78A8")),
                tooltip=[alt.Tooltip("faixa:N", title="Faixa"), alt.Tooltip("gols:Q", title="Gols"),
                         alt.Tooltip("gols_penalti:Q", title="De pênalti"),
                         alt.Tooltip("pct_gols_temporada:Q", title="% da temporada", format=".1%")],
            )
            .properties(height=380)
        )
        st.altair_chart(barras, alt=f"Gols por faixa de minuto em {temporada}, acréscimos em destaque")

# ---------- disciplina e finalização ----------

col_disc, col_fin = st.columns(2)

with col_disc, st.container(border=True, height="stretch"):
    st.subheader("Cartões por jogo")
    st.caption("Amarelos + vermelhos por partida, por clube. — `marts.disciplina_clube`")
    disc_t = disciplina.query("temporada == @temporada")
    if disc_t.empty:
        st.info("A fonte tem cartões só de 2014 a 2024.", icon=":material/info:")
    else:
        st.altair_chart(
            alt.Chart(disc_t)
            .mark_bar()
            .encode(
                y=alt.Y("clube:N", sort="-x", title=None),
                x=alt.X("cartoes_por_jogo:Q", title="Cartões por jogo"),
                tooltip=[alt.Tooltip("clube:N", title="Clube"), alt.Tooltip("amarelos:Q", title="Amarelos"),
                         alt.Tooltip("vermelhos:Q", title="Vermelhos"),
                         alt.Tooltip("cartoes_por_jogo:Q", title="Por jogo")],
            )
            .properties(height=420),
            alt=f"Cartões por jogo de cada clube em {temporada}",
        )

with col_fin, st.container(border=True, height="stretch"):
    st.subheader("Posse de bola × conversão")
    st.caption("Cada ponto é um clube: posse média e % dos chutes que viram gol. — `marts.finalizacao_clube`")
    fin_t = finalizacao.query("temporada == @temporada")
    if fin_t.empty:
        st.info("Sem estatística coletada na fonte para esta temporada (só 2015–2023 e 2025).", icon=":material/info:")
    else:
        pontos = alt.Chart(fin_t).encode(
            x=alt.X("posse_media:Q", title="Posse média", axis=alt.Axis(format="%"), scale=alt.Scale(zero=False)),
            y=alt.Y("conversao:Q", title="Conversão (gols / chutes)", axis=alt.Axis(format="%"),
                    scale=alt.Scale(zero=False)),
            tooltip=[alt.Tooltip("clube:N", title="Clube"), alt.Tooltip("gols:Q", title="Gols"),
                     alt.Tooltip("chutes:Q", title="Chutes"),
                     alt.Tooltip("conversao:Q", title="Conversão", format=".1%"),
                     alt.Tooltip("posse_media:Q", title="Posse", format=".1%")],
        )
        st.altair_chart(
            (pontos.mark_circle(size=90) + pontos.mark_text(align="left", dx=7, fontSize=11).encode(text="clube:N"))
            .properties(height=420),
            alt=f"Posse de bola contra conversão de chutes por clube em {temporada}",
        )
