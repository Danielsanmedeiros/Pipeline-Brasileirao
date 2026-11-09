-- marts.gols_por_faixa: uma linha por temporada e faixa de minuto.
-- Pergunta: em que momento do jogo saem os gols? Os acréscimos pesam quanto?
-- Origem: refined.gols JOIN refined.partidas (para a temporada).
--
-- Decisões:
-- 1. Só temporadas 2014–2025: a fonte não tem gols por minuto antes disso.
-- 2. Faixas de 15 minutos, com os acréscimos separados: '45+' (fim do 1º tempo)
--    e '90+' (fim do jogo). Um gol aos 45+2 não é um gol "dos 31 aos 45".
-- 3. Gols contra entram: contam no placar como qualquer outro gol.

create or replace table marts.gols_por_faixa as
with gols_com_faixa as (
    select
        p.temporada,
        g.tipo_gol,
        case
            when g.minuto = 45 and g.acrescimo > 0 then '45+'
            when g.minuto = 90 and g.acrescimo > 0 then '90+'
            when g.minuto <= 15 then '01-15'
            when g.minuto <= 30 then '16-30'
            when g.minuto <= 45 then '31-45'
            when g.minuto <= 60 then '46-60'
            when g.minuto <= 75 then '61-75'
            else '76-90'
        end as faixa
    from refined.gols g
    join refined.partidas p on p.partida_id = g.partida_id
)
select
    temporada,
    faixa,
    count(*)                                                        as gols,
    count(*) filter (where tipo_gol = 'penalti')                    as gols_penalti,
    round(count(*) / sum(count(*)) over (partition by temporada), 3) as pct_gols_temporada
from gols_com_faixa
group by temporada, faixa
order by temporada, case faixa when '45+' then '31-45+' else faixa end;
