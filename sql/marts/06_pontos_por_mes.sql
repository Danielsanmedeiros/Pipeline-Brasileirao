-- marts.pontos_por_mes: uma linha por clube, por mês, por temporada.
-- Pergunta: quem estava na frente em cada mês do campeonato? Como foi a corrida pelo título?
-- Origem: refined.partidas.
--
-- Decisões:
-- 1. "Mês" é o mês da data do jogo, e a tabela é a do FIM do mês, com todos os jogos
--    disputados até ali. Jogos adiados entram na data em que aconteceram, não na rodada
--    original — é a tabela que o torcedor via naquele dia.
-- 2. Todo clube aparece em todos os meses da temporada, mesmo sem jogar no mês: os pontos
--    se repetem. Sem isso, um clube parado sumiria da tabela daquele mês.
-- 3. Mesmos critérios de desempate de marts.classificacao: pontos, vitórias, saldo, gols pró.
--    Conferido: o último mês de cada temporada é igual a marts.classificacao.
-- 4. A temporada 2020 vai de agosto/2020 a fevereiro/2021; o mês é a data real, a temporada
--    é a de refined.partidas.
-- 5. liderou_na_temporada marca os clubes que terminaram pelo menos um mês em 1º. O painel
--    usa essa coluna para escolher as linhas do gráfico, sem calcular nada.

create or replace table marts.pontos_por_mes as
with jogos as (
    select temporada, date_trunc('month', data_partida)::date as mes,
           mandante as clube, gols_mandante as gols_pro, gols_visitante as gols_contra
    from refined.partidas
    union all
    select temporada, date_trunc('month', data_partida)::date as mes,
           visitante as clube, gols_visitante as gols_pro, gols_mandante as gols_contra
    from refined.partidas
),
por_mes as (
    select
        temporada, mes, clube,
        count(*)                                        as jogos,
        count(*) filter (where gols_pro > gols_contra)  as vitorias,
        count(*) filter (where gols_pro = gols_contra)  as empates,
        sum(gols_pro)                                   as gols_pro,
        sum(gols_contra)                                as gols_contra
    from jogos
    group by temporada, mes, clube
),
grade as (
    -- todos os clubes x todos os meses da temporada
    select c.temporada, m.mes, c.clube
    from (select distinct temporada, clube from jogos) c
    join (select distinct temporada, mes from jogos) m on m.temporada = c.temporada
),
acumulado as (
    select
        g.temporada, g.mes, g.clube,
        sum(coalesce(p.jogos, 0))       over w as jogos,
        sum(coalesce(p.vitorias, 0))    over w as vitorias,
        sum(coalesce(p.empates, 0))     over w as empates,
        sum(coalesce(p.gols_pro, 0))    over w as gols_pro,
        sum(coalesce(p.gols_contra, 0)) over w as gols_contra
    from grade g
    left join por_mes p on p.temporada = g.temporada and p.mes = g.mes and p.clube = g.clube
    window w as (partition by g.temporada, g.clube order by g.mes
                 rows between unbounded preceding and current row)
),
com_posicao as (
    select
        temporada, mes, clube, jogos,
        vitorias * 3 + empates     as pontos,
        vitorias,
        gols_pro - gols_contra     as saldo_gols,
        gols_pro,
        row_number() over (
            partition by temporada, mes
            order by vitorias * 3 + empates desc, vitorias desc, gols_pro - gols_contra desc, gols_pro desc, clube
        ) as posicao
    from acumulado
)
select
    temporada,
    mes,
    clube,
    jogos,
    pontos,
    vitorias,
    saldo_gols,
    posicao,
    posicao = 1                                                         as lider,
    bool_or(posicao = 1) over (partition by temporada, clube)           as liderou_na_temporada
from com_posicao
order by temporada, mes, posicao;
