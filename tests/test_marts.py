"""Camada marts: cada indicador conferido com um caso pequeno calculado à mão."""

import pytest

from conftest import estatistica, partida, rodar


def cartao(partida_id, clube, cor="Amarelo"):
    return {"partida_id": str(partida_id), "clube": clube, "cartao": cor, "atleta": "x",
            "num_camisa": "10", "posicao": "Meio-campo", "minuto": "30"}


def gol(partida_id, clube, minuto, tipo=None):
    return {"partida_id": str(partida_id), "clube": clube, "atleta": "x", "minuto": minuto,
            "tipo_de_gol": tipo}


# ---------- marts.classificacao ----------

def test_pontos_vitorias_empates_derrotas_e_saldo(banco):
    # Calculado à mão: B 1V 2E 1D = 5 pts (4 gols pró, 3 contra); A 1V 1E 1D = 4 pts
    # (2 pró, 3 contra); C 3E = 3 pts.
    con = rodar(banco(partidas=[
        partida(1, "01/05/2021", "A", "B", 2, 0),
        partida(2, "02/05/2021", "C", "A", 0, 0),   # A empata
        partida(3, "03/05/2021", "C", "B", 1, 1),
        partida(4, "04/05/2021", "B", "C", 0, 0),
        partida(5, "05/05/2021", "B", "A", 3, 0),
    ]), "refined", "marts")
    tabela = con.execute(
        "select posicao, clube, pontos, vitorias, empates, derrotas, saldo_gols "
        "from marts.classificacao order by posicao"
    ).fetchall()
    assert tabela == [
        (1, "B", 5, 1, 2, 1, 1),
        (2, "A", 4, 1, 1, 1, -1),
        (3, "C", 3, 0, 3, 0, 0),
    ]


def test_desempate_vitorias_vem_antes_do_saldo(banco):
    # A: 1V 1D = 3 pts, saldo -2. C: 3E = 3 pts, saldo 0. Empate em pontos;
    # A fica na frente por vitórias, mesmo com saldo pior.
    con = rodar(banco(partidas=[
        partida(1, "01/05/2021", "A", "B", 1, 0),
        partida(2, "02/05/2021", "B", "A", 3, 0),
        partida(3, "03/05/2021", "C", "D", 0, 0),
        partida(4, "04/05/2021", "D", "C", 1, 1),
        partida(5, "05/05/2021", "C", "D", 2, 2),
    ]), "refined", "marts")
    ordem = con.execute(
        "select clube, pontos, saldo_gols from marts.classificacao where clube in ('A', 'C') order by posicao"
    ).fetchall()
    assert ordem == [("A", 3, -2), ("C", 3, 0)]


def test_classificacao_separa_temporadas(banco):
    con = rodar(banco(partidas=[
        partida(1, "01/05/2020", "A", "B", 1, 0),
        partida(2, "10/02/2021", "B", "A", 1, 0),  # ainda temporada 2020
        partida(3, "01/06/2021", "A", "B", 1, 0),
    ]), "refined", "marts")
    jogos = con.execute(
        "select temporada, sum(jogos) / 2 from marts.classificacao group by 1 order by 1"
    ).fetchall()
    assert jogos == [(2020, 2), (2021, 1)]


# ---------- marts.mando_de_campo ----------

def test_mando_de_campo_percentuais(banco):
    con = rodar(banco(partidas=[
        partida(1, "01/05/2021", "A", "B", 2, 0),
        partida(2, "02/05/2021", "B", "A", 1, 0),
        partida(3, "03/05/2021", "A", "B", 1, 1),
        partida(4, "04/05/2021", "B", "A", 0, 3),
    ]), "refined", "marts")
    linha = con.execute(
        "select pct_vitoria_mandante, pct_empate, pct_vitoria_visitante, "
        "pontos_por_jogo_mandante, pontos_por_jogo_visitante, gols_por_jogo from marts.mando_de_campo"
    ).fetchone()
    assert linha == (0.5, 0.25, 0.25, 1.75, 1.0, 2.0)


# ---------- marts.gols_por_faixa ----------

@pytest.mark.parametrize("minuto, faixa", [
    ("1", "01-15"), ("15", "01-15"), ("16", "16-30"), ("45", "31-45"), ("45+2", "45+"),
    ("46", "46-60"), ("90", "76-90"), ("90+5", "90+"),
])
def test_faixa_do_minuto(banco, minuto, faixa):
    con = rodar(banco(
        partidas=[partida(1, "01/05/2021", "A", "B", 1, 0)],
        gols=[gol(1, "A", minuto)],
    ), "refined", "marts")
    assert con.execute("select faixa from marts.gols_por_faixa").fetchall() == [(faixa,)]


def test_gols_por_faixa_percentual_soma_um(banco):
    con = rodar(banco(
        partidas=[partida(1, "01/05/2021", "A", "B", 3, 1)],
        gols=[gol(1, "A", "10"), gol(1, "A", "12", "Penalty"), gol(1, "A", "50"), gol(1, "B", "90+1")],
    ), "refined", "marts")
    linhas = con.execute(
        "select faixa, gols, gols_penalti, pct_gols_temporada from marts.gols_por_faixa order by faixa"
    ).fetchall()
    assert linhas == [("01-15", 2, 1, 0.5), ("46-60", 1, 0, 0.25), ("90+", 1, 0, 0.25)]


# ---------- marts.disciplina_clube ----------

def test_disciplina_conta_jogos_sem_cartao_e_ignora_temporada_sem_dado(banco):
    con = rodar(banco(
        partidas=[
            partida(1, "01/05/2021", "A", "B", 0, 0),
            partida(2, "08/05/2021", "B", "A", 0, 0),
            partida(3, "01/05/2022", "A", "B", 0, 0),   # 2022: nenhum cartão na fonte
        ],
        cartoes=[cartao(1, "A"), cartao(1, "A", "Vermelho"), cartao(2, "A")],
    ), "refined", "marts")
    linhas = con.execute(
        "select temporada, clube, jogos, amarelos, vermelhos, cartoes_por_jogo "
        "from marts.disciplina_clube order by clube"
    ).fetchall()
    # B jogou 2 jogos sem cartão: aparece com 0, e não some da tabela.
    # 2022 não aparece: zero cartões lá é falta de dado, não time disciplinado.
    assert linhas == [(2021, "A", 2, 2, 1, 1.5), (2021, "B", 2, 0, 0, 0.0)]


# ---------- marts.finalizacao_clube ----------

def test_finalizacao_usa_placar_e_exige_10_jogos(banco):
    partidas, estatisticas = [], []
    for i in range(1, 11):  # 10 jogos com estatística: A x B, A marca 1 em 10 chutes
        partidas.append(partida(i, f"{i:02d}/05/2021", "A", "B", 1, 0))
        estatisticas += [estatistica(i, "A", chutes=10, no_alvo=4, posse="60%"),
                         estatistica(i, "B", chutes=5, no_alvo=1, posse="40%")]
    partidas.append(partida(11, "01/05/2022", "C", "D", 2, 0))  # 2022: só 1 jogo
    estatisticas += [estatistica(11, "C", chutes=4), estatistica(11, "D", chutes=4)]

    con = rodar(banco(partidas=partidas, estatisticas=estatisticas), "refined", "marts")
    linhas = con.execute(
        "select temporada, clube, jogos_com_estatistica, gols, chutes, pct_no_alvo, conversao, posse_media "
        "from marts.finalizacao_clube order by clube"
    ).fetchall()
    assert linhas == [
        (2021, "A", 10, 10, 100, 0.4, 0.1, 0.6),
        (2021, "B", 10, 0, 50, 0.2, 0.0, 0.4),
    ]
