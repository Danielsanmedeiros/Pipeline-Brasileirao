-- refined.estatisticas: uma linha por clube por partida, só partidas com estatística coletada.
-- Origem: raw.estatisticas (campeonato-brasileiro-estatisticas-full.csv).
--
-- Decisões:
-- 1. Zero não é zero. A fonte tem 2 linhas para TODAS as 9165 partidas, mas em parte
--    delas as duas linhas vêm com chutes, passes, faltas e escanteios = 0.
--    Nenhum time termina um jogo sem chutar nem passar: é estatística não coletada.
--    Essas partidas saem da tabela (em vez de ficarem com zeros que derrubariam médias).
--    Conferido: as linhas zeradas sempre vêm em par (os dois clubes da mesma partida).
--    raw 18330 linhas -> refined 7580 linhas (3790 partidas x 2).
--    Cobertura resultante: 2015–2023 e 2025 quase completas; 2014 só 16 jogos;
--    2024 nenhum. Indicadores que usam esta tabela precisam dizer isso.
-- 2. "Sem dado" aparece de dois jeitos na fonte: campo vazio e o TEXTO 'None'
--    (posse_de_bola e precisao_passes). Os dois viram nulo.
-- 3. posse_de_bola '35%' vira 0.35 (fração), para poder somar e tirar média.
--    O mesmo para precisao_passes.
-- 4. rodata (erro de digitação) não é levada: a rodada vem de refined.partidas.

create or replace table refined.estatisticas as
with partidas_sem_estatistica as (
    select partida_id
    from raw.estatisticas
    group by partida_id
    having bool_and(chutes = '0' and passes = '0' and faltas = '0' and escanteios = '0')
)
select
    cast(e.partida_id as integer)                                   as partida_id,
    e.clube,
    cast(e.chutes as integer)                                       as chutes,
    cast(e.chutes_no_alvo as integer)                               as chutes_no_alvo,
    cast(replace(nullif(e.posse_de_bola, 'None'), '%', '') as decimal(5, 2)) / 100   as posse_de_bola,
    cast(e.passes as integer)                                       as passes,
    cast(replace(nullif(e.precisao_passes, 'None'), '%', '') as decimal(5, 2)) / 100 as precisao_passes,
    cast(e.faltas as integer)                                       as faltas,
    cast(e.cartao_amarelo as integer)                               as cartao_amarelo,
    cast(e.cartao_vermelho as integer)                              as cartao_vermelho,
    cast(e.impedimentos as integer)                                 as impedimentos,
    cast(e.escanteios as integer)                                   as escanteios
from raw.estatisticas e
where e.partida_id not in (select partida_id from partidas_sem_estatistica);
