-- marts.disciplina_clube: uma linha por clube por temporada (2014–2025).
-- Pergunta: quais clubes levam mais cartões por jogo?
-- Origem: refined.cartoes JOIN refined.partidas.
--
-- Decisões:
-- 1. Média por jogo, não total: clubes jogam o mesmo número de partidas na temporada,
--    mas a média deixa comparar temporadas diferentes.
-- 2. jogos vem de refined.partidas (todos os jogos do clube), não só dos jogos em que
--    ele levou cartão — senão um jogo sem cartão não entraria no denominador.
-- 3. Só temporadas que têm cartões na fonte: 2014–2024. A fonte (versão 18) não tem
--    nenhum cartão de 2025. Sem este filtro, 2025 apareceria com 0 cartões para todos
--    os clubes — um zero falso, que na verdade é "não coletado".

create or replace table marts.disciplina_clube as
with jogos as (
    select temporada, clube, count(*) as jogos
    from (
        select temporada, mandante as clube from refined.partidas
        union all
        select temporada, visitante as clube from refined.partidas
    )
    group by temporada, clube
),
cartoes as (
    select
        p.temporada,
        c.clube,
        count(*) filter (where c.cartao = 'amarelo')  as amarelos,
        count(*) filter (where c.cartao = 'vermelho') as vermelhos
    from refined.cartoes c
    join refined.partidas p on p.partida_id = c.partida_id
    group by p.temporada, c.clube
)
select
    j.temporada,
    j.clube,
    j.jogos,
    coalesce(c.amarelos, 0)                                          as amarelos,
    coalesce(c.vermelhos, 0)                                         as vermelhos,
    round((coalesce(c.amarelos, 0) + coalesce(c.vermelhos, 0)) / j.jogos, 2) as cartoes_por_jogo
from jogos j
left join cartoes c on c.temporada = j.temporada and c.clube = j.clube
where j.temporada in (select distinct temporada from cartoes)
order by j.temporada, cartoes_por_jogo desc;
