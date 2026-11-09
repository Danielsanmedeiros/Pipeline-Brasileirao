-- refined.partidas: uma linha por partida da Série A (2003–2025).
-- Origem: raw.partidas (campeonato-brasileiro-full.csv).
--
-- Decisões:
-- 1. temporada != ano da data. A temporada 2020 foi até fevereiro de 2021 (pandemia),
--    então o ano da data põe 112 jogos de 2020 em 2021. Regra: jogo em janeiro ou
--    fevereiro pertence à temporada do ano anterior. Nenhuma temporada começa antes de
--    março (a mais cedo é 29/03/2003). Conferido: 380 jogos por temporada, exceto
--    2003/2004 (552, 24 clubes), 2005 (462, 22 clubes) e 2016 (379, Chapecoense x
--    Atlético-MG não foi disputado após o acidente aéreo).
-- 2. hora '00:00' vira nulo: aparece em uma única partida (ID 2206, 2007) e não é
--    horário real de jogo.
-- 3. vencedor '-' (empate) vira nulo, e a coluna resultado diz quem venceu sem depender
--    do nome do clube. Conferido: '-' acontece exatamente quando o placar é igual.
-- 4. arena tem espaço no início em 5077 linhas: trim.
-- 5. formação/técnico vazios viram nulo (só existem a partir de 2014/2015).
-- 6. arrecadacao só existe em 2025; fica nula nas demais temporadas, não zero.
-- 7. Nomes de clubes ficam como na fonte. 'Barueri' (2009) e 'Gremio Prudente' (2010)
--    são o mesmo clube que mudou de cidade e nome; mantidos separados porque
--    disputaram a liga com nomes diferentes.

create or replace table refined.partidas as
with base as (
    select
        *,
        strptime(data, '%d/%m/%Y')::date as data_partida
    from raw.partidas
)
select
    cast(id as integer)                                   as partida_id,
    cast(case when month(data_partida) <= 2
              then year(data_partida) - 1
              else year(data_partida) end as integer)     as temporada,
    cast(rodata as integer)                               as rodada,
    data_partida,
    cast(nullif(hora, '00:00') as time)                   as hora,
    mandante,
    visitante,
    cast(mandante_placar as integer)                      as gols_mandante,
    cast(visitante_placar as integer)                     as gols_visitante,
    case
        when cast(mandante_placar as integer) > cast(visitante_placar as integer) then 'mandante'
        when cast(mandante_placar as integer) < cast(visitante_placar as integer) then 'visitante'
        else 'empate'
    end                                                   as resultado,
    nullif(vencedor, '-')                                 as vencedor,
    nullif(trim(arena), '')                               as arena,
    mandante_estado                                       as uf_mandante,
    visitante_estado                                      as uf_visitante,
    nullif(formacao_mandante, '')                         as formacao_mandante,
    nullif(formacao_visitante, '')                        as formacao_visitante,
    nullif(tecnico_mandante, '')                          as tecnico_mandante,
    nullif(tecnico_visitante, '')                         as tecnico_visitante,
    cast(arrecadacao as decimal(14, 2))                   as arrecadacao
from base;
