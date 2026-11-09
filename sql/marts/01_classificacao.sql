-- marts.classificacao: tabela final de cada temporada, uma linha por clube por temporada.
-- Pergunta: quem terminou em que posição em cada Brasileirão?
-- Origem: refined.partidas.
--
-- Decisões:
-- 1. Pontos: vitória 3, empate 1, derrota 0 (regra do Brasileirão desde 2003).
-- 2. Desempate: pontos, vitórias, saldo de gols, gols pró — os critérios oficiais
--    na ordem. Confronto direto e sorteio não são calculados; se ainda assim houver
--    empate, a ordem alfabética só serve para a posição não ficar indefinida.
-- 3. É a classificação ESPORTIVA, só com o que aconteceu em campo. Punições de
--    tribunal (ex.: 2013, Portuguesa e Flamengo perderam 4 pontos cada no STJD) não
--    estão na fonte e não entram. Por isso a posição pode diferir da tabela oficial.

create or replace table marts.classificacao as
with jogos_por_clube as (
    select temporada, mandante as clube, gols_mandante as gols_pro, gols_visitante as gols_contra
    from refined.partidas
    union all
    select temporada, visitante as clube, gols_visitante as gols_pro, gols_mandante as gols_contra
    from refined.partidas
),
totais as (
    select
        temporada,
        clube,
        count(*)                                        as jogos,
        count(*) filter (where gols_pro > gols_contra)  as vitorias,
        count(*) filter (where gols_pro = gols_contra)  as empates,
        count(*) filter (where gols_pro < gols_contra)  as derrotas,
        sum(gols_pro)                                   as gols_pro,
        sum(gols_contra)                                as gols_contra
    from jogos_por_clube
    group by temporada, clube
)
select
    temporada,
    row_number() over (
        partition by temporada
        order by vitorias * 3 + empates desc, vitorias desc, gols_pro - gols_contra desc, gols_pro desc, clube
    )                                                   as posicao,
    clube,
    vitorias * 3 + empates                              as pontos,
    jogos,
    vitorias,
    empates,
    derrotas,
    gols_pro,
    gols_contra,
    gols_pro - gols_contra                              as saldo_gols,
    round((vitorias * 3 + empates) / (jogos * 3.0), 3)  as aproveitamento
from totais
order by temporada, posicao;
