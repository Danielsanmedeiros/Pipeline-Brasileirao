"""Conferência das contagens citadas na seção "Onde a IA errou" do README.

Uso (depois de python -m pipeline.run):  .venv\\Scripts\\python.exe conferir.py
"""

import duckdb

con = duckdb.connect("data/brasileirao.duckdb", read_only=True)

print("1. precisao_passes com valor (esperado: 5264)")
print(con.sql("""
    select count(*) as com_valor
    from raw.estatisticas
    where precisao_passes is not null and precisao_passes <> 'None'
"""))

print("2. linhas zeradas com posse = 'None' (esperado: 1538)")
print(con.sql("""
    select count(*) as zeradas_com_none
    from raw.estatisticas
    where chutes = '0' and passes = '0' and posse_de_bola = 'None'
"""))

print("3. cartões por temporada (esperado: 2023 = 2118, 2024 = 2096, 2025 = 0)")
print(con.sql("""
    select p.temporada, count(c.partida_id) as cartoes
    from refined.partidas p
    left join refined.cartoes c using (partida_id)
    where p.temporada >= 2023
    group by 1
    order by 1
"""))
