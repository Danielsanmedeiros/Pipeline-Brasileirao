-- refined.cartoes: uma linha por cartão aplicado (temporadas 2014–2025).
-- Origem: raw.cartoes (campeonato-brasileiro-cartoes.csv).
--
-- Decisões:
-- 1. minuto '45+3' vira minuto = 45 e acrescimo = 3 (mesma regra de refined.gols).
-- 2. posicao 'Zagueira' é grafia diferente de 'Zagueiro' na fonte: padronizado.
--    posicao vazia continua nula (não dá para saber a posição).
-- 3. cartao fica em minúsculas ('amarelo' / 'vermelho') para padronizar com tipo_gol.
-- 4. num_camisa vira inteiro; 386 cartões não têm número e ficam nulos.

create or replace table refined.cartoes as
select
    cast(partida_id as integer)                                       as partida_id,
    clube,
    atleta,
    cast(num_camisa as integer)                                       as num_camisa,
    case when posicao = 'Zagueira' then 'Zagueiro' else posicao end   as posicao,
    lower(cartao)                                                     as cartao,
    minuto                                                            as minuto_original,
    cast(split_part(minuto, '+', 1) as integer)                       as minuto,
    coalesce(cast(nullif(split_part(minuto, '+', 2), '') as integer), 0) as acrescimo
from raw.cartoes;
