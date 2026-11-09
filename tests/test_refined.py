"""Camada refined: cada decisão escrita nos .sql tem um teste com dado inventado."""

from datetime import time

from conftest import estatistica, partida, rodar


# ---------- refined.partidas ----------

def test_jogo_em_fevereiro_conta_para_temporada_anterior(banco):
    con = rodar(banco(partidas=[
        partida(1, "15/12/2020", "A", "B", 1, 0),
        partida(2, "25/02/2021", "A", "B", 1, 0),   # fim da temporada 2020 (pandemia)
        partida(3, "29/03/2021", "A", "B", 1, 0),   # temporada 2021 normal
    ]), "refined")
    temporadas = con.execute("select partida_id, temporada from refined.partidas order by 1").fetchall()
    assert temporadas == [(1, 2020), (2, 2020), (3, 2021)]


def test_empate_vira_resultado_e_vencedor_nulo(banco):
    con = rodar(banco(partidas=[
        partida(1, "01/05/2020", "A", "B", 2, 2),
        partida(2, "01/05/2020", "A", "B", 0, 1),
    ]), "refined")
    linhas = con.execute("select resultado, vencedor from refined.partidas order by partida_id").fetchall()
    assert linhas == [("empate", None), ("visitante", "B")]


def test_hora_zero_vira_nulo_e_arena_sem_espaco(banco):
    con = rodar(banco(partidas=[
        partida(1, "01/05/2020", "A", "B", 1, 0, hora="00:00", arena=" Maracanã"),
        partida(2, "01/05/2020", "A", "B", 1, 0, hora="16:30", arena=" Maracanã"),
    ]), "refined")
    linhas = con.execute("select hora, arena from refined.partidas order by partida_id").fetchall()
    assert linhas == [(None, "Maracanã"), (time(16, 30), "Maracanã")]


# ---------- refined.gols e refined.cartoes ----------

def test_minuto_com_acrescimo_e_tipo_de_gol(banco):
    con = rodar(banco(gols=[
        {"partida_id": "1", "clube": "A", "atleta": "x", "minuto": "90+2", "tipo_de_gol": "Penalty"},
        {"partida_id": "1", "clube": "A", "atleta": "y", "minuto": "31", "tipo_de_gol": None},
        {"partida_id": "1", "clube": "B", "atleta": "z", "minuto": "45+1", "tipo_de_gol": "Gol Contra"},
    ]), "refined")
    linhas = con.execute("select minuto, acrescimo, tipo_gol from refined.gols order by atleta").fetchall()
    assert linhas == [(90, 2, "penalti"), (31, 0, "normal"), (45, 1, "contra")]


def test_posicao_zagueira_padronizada(banco):
    con = rodar(banco(cartoes=[
        {"partida_id": "1", "clube": "A", "cartao": "Amarelo", "atleta": "x", "num_camisa": "4",
         "posicao": "Zagueira", "minuto": "10"},
        {"partida_id": "1", "clube": "A", "cartao": "Vermelho", "atleta": "y", "num_camisa": None,
         "posicao": None, "minuto": "90+3"},
    ]), "refined")
    linhas = con.execute(
        "select posicao, cartao, num_camisa, acrescimo from refined.cartoes order by atleta"
    ).fetchall()
    assert linhas == [("Zagueiro", "amarelo", 4, 0), (None, "vermelho", None, 3)]


# ---------- refined.estatisticas ----------

def test_partida_com_estatistica_zerada_sai_da_tabela(banco):
    con = rodar(banco(estatisticas=[
        estatistica(1, "A", chutes=0, passes=0, faltas=0, escanteios=0, posse=None),
        estatistica(1, "B", chutes=0, passes=0, faltas=0, escanteios=0, posse="None"),
        estatistica(2, "A", chutes=12, posse="60%"),
        estatistica(2, "B", chutes=8, posse="40%"),
    ]), "refined")
    assert con.execute("select distinct partida_id from refined.estatisticas").fetchall() == [(2,)]


def test_um_time_com_zero_chutes_nao_e_descartado(banco):
    # Zero chutes de UM time é possível; só sai a partida em que tudo dos dois lados é zero.
    con = rodar(banco(estatisticas=[
        estatistica(1, "A", chutes=0, posse="30%"),
        estatistica(1, "B", chutes=15, posse="70%"),
    ]), "refined")
    assert con.execute("select count(*) from refined.estatisticas").fetchone()[0] == 2


def test_posse_vira_fracao_e_none_vira_nulo(banco):
    con = rodar(banco(estatisticas=[
        estatistica(1, "A", chutes=10, posse="35%", precisao="82%"),
        estatistica(1, "B", chutes=10, posse="None", precisao="None"),
    ]), "refined")
    linhas = con.execute(
        "select clube, posse_de_bola, precisao_passes from refined.estatisticas order by clube"
    ).fetchall()
    assert linhas == [("A", 0.35, 0.82), ("B", None, None)]
