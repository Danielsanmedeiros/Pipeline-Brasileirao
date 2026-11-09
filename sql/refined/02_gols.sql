-- refined.gols: uma linha por gol marcado (temporadas 2014–2025).
-- Origem: raw.gols (campeonato-brasileiro-gols.csv).
--
-- Decisões:
-- 1. clube = clube que ganhou o gol, inclusive no gol contra (o atleta é do adversário).
--    Conferido: contando gols por clube, o resultado bate com o placar de refined.partidas
--    nas 4172 partidas com gol a partir de 2014 (teste em tests/).
-- 2. minuto '90+2' vira minuto = 90 e acrescimo = 2, para dar para ordenar e agrupar.
--    O texto original fica em minuto_original.
-- 3. tipo_de_gol vazio = gol normal. 'Penalty' -> 'penalti', 'Gol Contra' -> 'contra'.
-- 4. A coluna rodata (erro de digitação na fonte) não é levada: a rodada vem de
--    refined.partidas pelo partida_id, para existir uma fonte só para esse dado.

create or replace table refined.gols as
select
    cast(partida_id as integer)                                       as partida_id,
    clube,
    atleta,
    minuto                                                            as minuto_original,
    cast(split_part(minuto, '+', 1) as integer)                       as minuto,
    coalesce(cast(nullif(split_part(minuto, '+', 2), '') as integer), 0) as acrescimo,
    case tipo_de_gol
        when 'Penalty'    then 'penalti'
        when 'Gol Contra' then 'contra'
        else 'normal'
    end                                                               as tipo_gol
from raw.gols;
