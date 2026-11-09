"""Camada raw: o CSV entra sem nenhuma alteração."""

import duckdb

from pipeline.run import ARQUIVOS_RAW, carregar_raw


def test_raw_nao_converte_nada(tmp_path):
    # CSV inventado com valores que uma conversão automática estragaria.
    cabecalho = '"partida_id","rodata","clube","atleta","minuto","tipo_de_gol"\n'
    (tmp_path / ARQUIVOS_RAW["gols"]).write_text(
        cabecalho + '"7","1","Time A","Fulano","90+2","Penalty"\n"7","1","Time A","Ciclano","05",""\n',
        encoding="utf-8",
    )
    for tabela, arquivo in ARQUIVOS_RAW.items():
        if tabela != "gols":
            (tmp_path / arquivo).write_text('"col"\n"x"\n', encoding="utf-8")

    con = duckdb.connect(":memory:")
    carregar_raw(con, tmp_path)

    linhas = con.execute("select minuto, partida_id from raw.gols order by atleta desc").fetchall()
    assert linhas == [("90+2", "7"), ("05", "7")]  # '05' não vira 5, '90+2' continua texto
    tipos = {t for (t,) in con.execute(
        "select distinct data_type from information_schema.columns where table_schema = 'raw'"
    ).fetchall()}
    assert tipos == {"VARCHAR"}
