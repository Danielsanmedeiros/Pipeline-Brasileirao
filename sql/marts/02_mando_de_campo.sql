-- marts.mando_de_campo: uma linha por temporada.
-- Pergunta: jogar em casa ainda dá vantagem? Ela mudou com os jogos sem torcida
-- (temporada 2020, inteira com portões fechados, e começo de 2021)?
-- Origem: refined.partidas.
--
-- Decisões:
-- 1. Percentuais sobre o total de jogos da temporada (somam 1).
-- 2. pontos_por_jogo_mandante/visitante: média de pontos que cada lado leva por
--    partida — compara as temporadas mesmo com número diferente de jogos (2003–2005).

create or replace table marts.mando_de_campo as
select
    temporada,
    count(*)                                                             as jogos,
    round(avg(case when resultado = 'mandante'  then 1 else 0 end), 3)   as pct_vitoria_mandante,
    round(avg(case when resultado = 'empate'    then 1 else 0 end), 3)   as pct_empate,
    round(avg(case when resultado = 'visitante' then 1 else 0 end), 3)   as pct_vitoria_visitante,
    round(avg(case resultado when 'mandante' then 3 when 'empate' then 1 else 0 end), 2)  as pontos_por_jogo_mandante,
    round(avg(case resultado when 'visitante' then 3 when 'empate' then 1 else 0 end), 2) as pontos_por_jogo_visitante,
    round(avg(gols_mandante + gols_visitante), 2)                        as gols_por_jogo
from refined.partidas
group by temporada
order by temporada;
