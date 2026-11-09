"""Monta um banco DuckDB em memória com dado inventado, no formato da camada raw.

Nenhum teste abre data/brasileirao.duckdb nem lê os CSVs reais: cada teste cria só as
linhas de que precisa e roda os mesmos arquivos .sql do pipeline sobre elas.
"""

import duckdb
import pytest

from pipeline.run import executar_camada

# Colunas exatamente como nos CSVs de origem (inclusive o 'rodata' com erro de digitação).
COLUNAS_RAW = {
    "partidas": ["ID", "rodata", "data", "hora", "mandante", "visitante", "formacao_mandante",
                 "formacao_visitante", "tecnico_mandante", "tecnico_visitante", "vencedor", "arena",
                 "mandante_Placar", "visitante_Placar", "mandante_Estado", "visitante_Estado",
                 "arrecadacao"],
    "gols": ["partida_id", "rodata", "clube", "atleta", "minuto", "tipo_de_gol"],
    "cartoes": ["partida_id", "rodata", "clube", "cartao", "atleta", "num_camisa", "posicao", "minuto"],
    "estatisticas": ["partida_id", "rodata", "clube", "chutes", "chutes_no_alvo", "posse_de_bola",
                     "passes", "precisao_passes", "faltas", "cartao_amarelo", "cartao_vermelho",
                     "impedimentos", "escanteios"],
}


def partida(id, data, mandante, visitante, gm, gv, hora="16:00", arena="Estádio", rodada=1):
    """Uma linha de raw.partidas como a fonte escreve: tudo texto, empate com vencedor '-'."""
    vencedor = mandante if gm > gv else visitante if gv > gm else "-"
    return {"ID": str(id), "rodata": str(rodada), "data": data, "hora": hora,
            "mandante": mandante, "visitante": visitante, "vencedor": vencedor, "arena": arena,
            "mandante_Placar": str(gm), "visitante_Placar": str(gv),
            "mandante_Estado": "SP", "visitante_Estado": "RJ"}


def estatistica(partida_id, clube, chutes, no_alvo=0, posse="50%", passes=400, faltas=10,
                escanteios=5, precisao="None"):
    return {"partida_id": str(partida_id), "rodata": "1", "clube": clube, "chutes": str(chutes),
            "chutes_no_alvo": str(no_alvo), "posse_de_bola": posse, "passes": str(passes),
            "precisao_passes": precisao, "faltas": str(faltas), "cartao_amarelo": "0",
            "cartao_vermelho": "0", "impedimentos": "0", "escanteios": str(escanteios)}


@pytest.fixture
def banco():
    """Devolve uma função que cria o banco em memória com as linhas raw informadas."""
    conexoes = []

    def _montar(**linhas_por_tabela):
        con = duckdb.connect(":memory:")
        conexoes.append(con)
        con.execute("create schema raw")
        for tabela, colunas in COLUNAS_RAW.items():
            defs = ", ".join(f'"{c}" varchar' for c in colunas)
            con.execute(f"create table raw.{tabela} ({defs})")
            for linha in linhas_por_tabela.get(tabela, []):
                valores = [linha.get(c) for c in colunas]
                marcadores = ", ".join("?" for _ in colunas)
                con.execute(f"insert into raw.{tabela} values ({marcadores})", valores)
        return con

    yield _montar
    for con in conexoes:
        con.close()


def rodar(con, *camadas):
    for camada in camadas:
        executar_camada(con, camada)
    return con
