-- marts.finalizacao_clube: uma linha por clube por temporada com estatística.
-- Pergunta: quais clubes transformam mais chutes em gol? Ter mais posse de bola
-- significa marcar mais?
-- Origem: refined.estatisticas JOIN refined.partidas (temporada e gols marcados).
--
-- Decisões:
-- 1. Gols vêm do placar de refined.partidas, não de refined.gols: o placar existe
--    para todos os jogos e é a fonte oficial do resultado.
-- 2. Só jogos com estatística coletada (ver refined.estatisticas): 2024 não aparece e
--    2014 tem só 16 jogos. A coluna jogos_com_estatistica mostra a base de cada linha.
-- 3. Temporadas com menos de 10 jogos com estatística para o clube são descartadas:
--    uma taxa de conversão de 2 jogos não diz nada sobre a temporada.
-- 4. conversao = gols / chutes. pct_no_alvo = chutes_no_alvo / chutes.

create or replace table marts.finalizacao_clube as
with jogos as (
    select
        p.temporada,
        e.clube,
        e.chutes,
        e.chutes_no_alvo,
        e.posse_de_bola,
        case when e.clube = p.mandante then p.gols_mandante else p.gols_visitante end as gols
    from refined.estatisticas e
    join refined.partidas p on p.partida_id = e.partida_id
)
select
    temporada,
    clube,
    count(*)                                        as jogos_com_estatistica,
    sum(gols)                                       as gols,
    sum(chutes)                                     as chutes,
    sum(chutes_no_alvo)                             as chutes_no_alvo,
    round(sum(chutes_no_alvo) / sum(chutes), 3)     as pct_no_alvo,
    round(sum(gols) / sum(chutes), 3)               as conversao,
    round(avg(posse_de_bola), 3)                    as posse_media
from jogos
group by temporada, clube
having count(*) >= 10
order by temporada, conversao desc;
