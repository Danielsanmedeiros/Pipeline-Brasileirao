"""Roda o pipeline inteiro: raw -> refined -> marts, num arquivo DuckDB.

Uso:  python -m pipeline.run

Cada camada é um schema separado no mesmo banco (data/brasileirao.duckdb):
- raw:     os CSVs exatamente como vieram, todas as colunas como texto.
- refined: tipos corrigidos, nomes padronizados, uma decisão documentada por coluna.
- marts:   os indicadores, um arquivo .sql por indicador.

As transformações ficam em sql/<camada>/*.sql e rodam em ordem alfabética.
O banco é recriado do zero a cada execução, para o resultado depender só dos arquivos.
"""

from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parent.parent
PASTA_RAW = RAIZ / "data" / "raw"
PASTA_SQL = RAIZ / "sql"
BANCO = RAIZ / "data" / "brasileirao.duckdb"

# tabela raw -> arquivo de origem
ARQUIVOS_RAW = {
    "partidas": "campeonato-brasileiro-full.csv",
    "gols": "campeonato-brasileiro-gols.csv",
    "cartoes": "campeonato-brasileiro-cartoes.csv",
    "estatisticas": "campeonato-brasileiro-estatisticas-full.csv",
}

CAMADAS = ["refined", "marts"]


def carregar_raw(con: duckdb.DuckDBPyConnection, pasta: Path = PASTA_RAW) -> None:
    """Carrega cada CSV em raw.<tabela> sem alterar nada.

    all_varchar=true: nenhuma conversão de tipo nesta camada ("90+2" continua texto,
    "29/03/2003" continua texto). Converter é trabalho da refined.
    """
    con.execute("create schema if not exists raw")
    for tabela, arquivo in ARQUIVOS_RAW.items():
        caminho = (pasta / arquivo).as_posix()
        con.execute(
            f"create or replace table raw.{tabela} as "
            f"select * from read_csv('{caminho}', header=true, all_varchar=true)"
        )


def executar_camada(con: duckdb.DuckDBPyConnection, camada: str, pasta_sql: Path = PASTA_SQL) -> list[str]:
    """Executa os .sql de uma camada em ordem e devolve os nomes dos arquivos executados."""
    con.execute(f"create schema if not exists {camada}")
    executados = []
    for arquivo in sorted((pasta_sql / camada).glob("*.sql")):
        con.execute(arquivo.read_text(encoding="utf-8"))
        executados.append(arquivo.name)
    return executados


def contar_linhas(con: duckdb.DuckDBPyConnection) -> list[tuple[str, str, int]]:
    tabelas = con.execute(
        "select schema_name, table_name from duckdb_tables() "
        "where schema_name in ('raw', 'refined', 'marts') order by schema_name = 'raw' desc, schema_name, table_name"
    ).fetchall()
    return [(s, t, con.execute(f"select count(*) from {s}.{t}").fetchone()[0]) for s, t in tabelas]


def main() -> None:
    if not PASTA_RAW.exists():
        raise SystemExit("data/raw/ não existe. Rode antes: python -m pipeline.download")
    BANCO.unlink(missing_ok=True)
    with duckdb.connect(str(BANCO)) as con:
        carregar_raw(con)
        for camada in CAMADAS:
            executar_camada(con, camada)
        print(f"Banco: {BANCO.relative_to(RAIZ)}")
        for schema, tabela, n in contar_linhas(con):
            print(f"  {schema + '.' + tabela:<40} {n:>7} linhas")


if __name__ == "__main__":
    main()
