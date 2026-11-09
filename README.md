# Pipeline Brasileirão

Pipeline de dados do Campeonato Brasileiro Série A, de 2003 a 2025: do CSV de origem até os
indicadores, com Python, SQL (DuckDB), testes com pytest e git.

**Perguntas que o dado responde aqui**

1. Quem terminou em que posição em cada temporada?
2. Jogar em casa ainda dá vantagem? Ela mudou nos jogos sem torcida (2020)?
3. Em que momento do jogo saem os gols, e quanto pesam os acréscimos?
4. Quais clubes levam mais cartões por jogo?
5. Quais clubes transformam mais chutes em gol, e ter mais posse significa marcar mais?

---

## Fonte do dado

| | |
|---|---|
| Dataset | [Campeonato Brasileiro de futebol — Adão Duque (Kaggle)](https://www.kaggle.com/datasets/adaoduque/campeonato-brasileiro-de-futebol) |
| Licença | **GPL 2** (permite redistribuição e uso público, com crédito ao autor e mantendo a licença) |
| Versão usada | **18** (atualizada em 05/02/2026), fixada no download |
| Repositório do autor | https://github.com/adaoduque/Brasileirao_Dataset |
| Conferência | cada CSV é verificado por SHA-256 em [pipeline/download.py](pipeline/download.py) |

Os CSVs **não ficam no repositório**: são baixados pelo pipeline (pasta `data/` no `.gitignore`).
A versão é fixada porque o autor atualiza o dataset a cada temporada. Sem isso, quem rodar o
projeto daqui a um ano teria outros números nos indicadores.

---

## Como rodar do zero

Requisitos: Python 3.10 ou mais novo (testado com 3.13) e git. Não precisa de conta no Kaggle.

```bash
git clone https://github.com/Danielsanmedeiros/Pipeline-Brasileirao.git
cd Pipeline-Brasileirao
python -m venv .venv
```

Ative o ambiente. No Windows (PowerShell):

```bash
.venv\Scripts\Activate.ps1
```

No Linux ou macOS:

```bash
source .venv/bin/activate
```

Depois:

```bash
pip install -r requirements.txt
python -m pipeline.download      # baixa os 4 CSVs para data/raw/ e confere o SHA-256
python -m pipeline.run           # cria data/brasileirao.duckdb com raw -> refined -> marts
pytest                           # 24 testes, com dado inventado, sem abrir o banco
```

Saída esperada de `python -m pipeline.run`:

```
raw.cartoes            20953 linhas      refined.cartoes        20953 linhas
raw.estatisticas       18330 linhas      refined.estatisticas    7580 linhas
raw.gols               10820 linhas      refined.gols           10820 linhas
raw.partidas            9165 linhas      refined.partidas        9165 linhas

marts.classificacao      470 linhas      marts.gols_por_faixa      96 linhas
marts.disciplina_clube   220 linhas      marts.mando_de_campo      23 linhas
marts.finalizacao_clube  200 linhas
```

Para abrir o painel (opcional, lê só a camada marts):

```bash
streamlit run dashboard/app.py
```

Para consultar os indicadores direto no banco:

```bash
python -c "import duckdb; print(duckdb.connect('data/brasileirao.duckdb').sql('select * from marts.mando_de_campo'))"
```

---

## As três camadas

```
CSV do Kaggle ──> raw ──────────────> refined ─────────────────────> marts
                  (texto, como veio)  (tipos, limpeza, decisões)      (indicadores)
                  pipeline/run.py     sql/refined/*.sql               sql/marts/*.sql
```

Cada camada é um schema separado no mesmo arquivo DuckDB (`data/brasileirao.duckdb`), e o banco é
recriado do zero a cada execução. Os `.sql` de cada camada rodam em ordem alfabética.

- **raw:** os 4 CSVs carregados **sem nenhuma alteração**. Todas as colunas são texto
  (`all_varchar`), então `"90+2"` e `"29/03/2003"` continuam como estão. O teste
  [test_raw.py](tests/test_raw.py) garante isso.
- **refined:** tipos corrigidos, nomes padronizados e "sem dado" convertido para nulo. Cada
  decisão está escrita no topo do `.sql` correspondente.
- **marts:** um arquivo `.sql` por indicador, sempre lendo da refined.

### O que é uma linha de cada tabela

| Tabela | Uma linha é… | Chave | Cobertura |
|---|---|---|---|
| `raw.partidas` / `refined.partidas` | uma partida | `partida_id` | 2003–2025 (9165 jogos) |
| `raw.gols` / `refined.gols` | um gol | `partida_id` → partidas | 2014–2025 |
| `raw.cartoes` / `refined.cartoes` | um cartão aplicado | `partida_id` → partidas | 2014–2024 (a fonte não tem 2025) |
| `raw.estatisticas` | um clube em uma partida | `partida_id` + `clube` | todas, mas metade zerada |
| `refined.estatisticas` | um clube em uma partida **com estatística coletada** | `partida_id` + `clube` | 3790 partidas: 2015–2023, 2025 (2014 só 16 jogos, 2024 nenhum) |
| `marts.classificacao` | um clube em uma temporada | `temporada` + `clube` | 2003–2025 |
| `marts.mando_de_campo` | uma temporada | `temporada` | 2003–2025 |
| `marts.gols_por_faixa` | uma faixa de minuto em uma temporada | `temporada` + `faixa` | 2014–2025 |
| `marts.disciplina_clube` | um clube em uma temporada | `temporada` + `clube` | 2014–2024 |
| `marts.finalizacao_clube` | um clube em uma temporada (mín. 10 jogos com estatística) | `temporada` + `clube` | 2015–2023, 2025 |

As tabelas se ligam por `partida_id`. Todos os indicadores que não são de partidas usam um JOIN
com `refined.partidas` para obter a temporada e o placar.

---

## Indicadores

| Indicador | Arquivo | Tabelas usadas |
|---|---|---|
| Classificação por temporada | [sql/marts/01_classificacao.sql](sql/marts/01_classificacao.sql) | partidas |
| Vantagem do mandante | [sql/marts/02_mando_de_campo.sql](sql/marts/02_mando_de_campo.sql) | partidas |
| Gols por faixa de minuto | [sql/marts/03_gols_por_faixa.sql](sql/marts/03_gols_por_faixa.sql) | gols ⨝ partidas |
| Cartões por jogo | [sql/marts/04_disciplina_clube.sql](sql/marts/04_disciplina_clube.sql) | cartões ⨝ partidas |
| Conversão de chutes e posse | [sql/marts/05_finalizacao_clube.sql](sql/marts/05_finalizacao_clube.sql) | estatísticas ⨝ partidas |

### O que eles mostram

- **Classificação:** os campeões calculados de 2015 a 2025 batem com os campeões reais
  (Corinthians 2015, Palmeiras 2016, …, Botafogo 2024, Flamengo 2025). Usei isso como
  conferência do cálculo de pontos.
- **Mando de campo:** o mandante venceu 50,7% dos jogos em 2003–2019, 45,0% em 2020 (sem
  torcida) e 46,9% em 2021–2025. Mas 2017, com torcida, teve a menor taxa da série (43,9%).
  Por isso o dado **não** sustenta "sem torcida = sem vantagem": a queda de 2020 está dentro
  de uma redução mais longa.
- **Gols por minuto:** a segunda metade dos tempos concentra mais gols (76–90' é a faixa com
  mais gols). Os gols nos acréscimos (45+ e 90+) passaram de 7,1% em 2014 para 11–14% a partir
  de 2019.
- **Disciplina (2014–2024, clubes com 150+ jogos):** Coritiba (2,88 cartões/jogo) e Vasco
  (2,83) no topo; Corinthians (2,17) é o mais disciplinado.
- **Finalização:** a posse média tem correlação 0,57 com os gols por jogo e 0,41 com a
  conversão de chutes. Correlação não é causa: times melhores têm mais posse **e** mais gols.

---

## Decisões sobre o dado

Cada decisão está comentada no `.sql` onde é aplicada e tem um teste em `tests/`.

| Decisão | Motivo | Onde |
|---|---|---|
| Temporada = ano da data, mas jogos de jan/fev contam para o ano anterior | A temporada 2020 terminou em fev/2021 (pandemia). Pelo ano da data, 2020 teria 268 jogos e 2021 teria 492. Com a regra, são 380 e 380 | refined/01_partidas.sql |
| Vencedor `-` vira nulo, e a coluna `resultado` diz mandante/empate/visitante | Não depender do nome do clube para saber o resultado. Conferido: `-` aparece exatamente quando o placar é igual | refined/01_partidas.sql |
| Hora `00:00` vira nulo | Aparece em 1 jogo só (ID 2206) e não é horário real | refined/01_partidas.sql |
| Gol contra fica com o clube beneficiado | É assim que a fonte faz. Conferido: somando gols por clube, o resultado bate com o placar nas 4172 partidas com gol | refined/02_gols.sql |
| `90+2` vira minuto 90 + acréscimo 2 | Para ordenar e agrupar por faixa sem perder o acréscimo | refined/02_gols.sql, 03_cartoes.sql |
| Estatística toda zerada nos dois clubes = partida sem estatística (sai da tabela) | Nenhum time termina um jogo com zero chutes e zero passes. Manter os zeros derrubaria as médias | refined/04_estatisticas.sql |
| Texto `None` vira nulo | A fonte usa dois jeitos de dizer "sem dado": vazio e o texto `None` | refined/04_estatisticas.sql |
| Classificação esportiva (sem punições do STJD) | A fonte só tem os jogos. Ex.: em 2013, Portuguesa e Flamengo perderam pontos no tribunal | marts/01_classificacao.sql |
| Disciplina só em temporadas que têm cartões | A fonte não tem cartões de 2025. Sem o filtro, todos os clubes apareceriam com 0 cartões | marts/04_disciplina_clube.sql |
| Finalização exige 10+ jogos com estatística | A conversão de 2 jogos não diz nada sobre uma temporada | marts/05_finalizacao_clube.sql |
| `Barueri` e `Gremio Prudente` ficam separados | São o mesmo clube, que mudou de cidade e de nome, mas disputaram a liga com nomes diferentes | refined/01_partidas.sql |

---

## Estrutura

```
pipeline/download.py     baixa a fonte (versão fixa) e confere o SHA-256
pipeline/run.py          carrega a raw e roda sql/refined e sql/marts
sql/refined/*.sql        camada transformada (uma tabela por arquivo)
sql/marts/*.sql          indicadores (um indicador por arquivo)
tests/                   pytest com dado inventado em DuckDB em memória
dashboard/app.py         painel Streamlit: lê só marts.*, sem nenhum cálculo na tela
```

### Painel

[dashboard/app.py](dashboard/app.py) mostra os 5 indicadores com filtro por temporada. Regra: todo
número exibido sai pronto de uma tabela `marts.*`. O painel só filtra linhas pela temporada escolhida
e decide como desenhar. Se um número precisar de conta, a conta vai para um `.sql` em `sql/marts/`.
Quando a fonte não tem dado para a temporada (cartões de 2025, estatísticas de 2024, gols antes de
2014), o painel diz isso em vez de mostrar zero.

---

## Onde a IA errou ou assumiu algo que eu não pedi

> ⚠️ **Rascunho: revisar e reescrever com suas palavras antes de entregar.** Os quatro casos
> abaixo aconteceram de verdade durante a construção (estão no histórico de commits), mas
> esta seção é sobre a **sua** conferência. Confira cada número e acrescente o que você
> mesmo encontrar.

1. **"precisao_passes está vazia em todas as linhas".** A IA concluiu isso olhando 5 linhas e
   escreveu no SQL que a coluna não seria levada. A conversão de `posse_de_bola` falhou com o
   texto `"None"`, e contando os valores por tipo apareceram 5264 linhas com percentual
   preenchido. A coluna voltou para a refined.
2. **Regra de "estatística zerada".** A primeira versão exigia posse nula, mas 1538 linhas
   zeradas tinham posse = texto `"None"` e teriam passado como jogos com zero chutes. Descoberto
   contando as combinações (nulo / `None` / zerada) antes e depois.
3. **Cartões de 2025.** A IA assumiu que os cartões cobriam 2014–2025 e filtrou `>= 2014`.
   O indicador mostrou Grêmio, Ceará e Santos com 0 cartões em 38 jogos. Contando os jogos com
   cartão por temporada: 2025 tinha 0 de 380. O filtro passou a usar as temporadas que têm dado.
4. **Teste que não testava o que dizia.** O comentário do teste de classificação dizia "A e C
   empatam em pontos e A fica na frente por vitórias", mas no dado inventado A tinha 4 pontos e
   C tinha 3, ou seja, não havia empate para desempatar. Descoberto recalculando a tabela à mão.
   Foi criado um teste de desempate de verdade, e a regra foi quebrada de propósito para
   confirmar que o teste falha.
