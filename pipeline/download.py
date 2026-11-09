"""Baixa o dataset do Kaggle (versão fixa) para data/raw/, sem alterar nada.

Uso:  python -m pipeline.download

Decisões:
- A versão do dataset é fixada (18, de 05/02/2026). O autor atualiza o dataset a cada
  temporada; sem fixar, quem rodar daqui a um ano teria outros números nos indicadores.
- Cada CSV é conferido por SHA-256. Se o arquivo não for byte a byte o que foi usado
  no projeto, o download falha em vez de seguir com um dado diferente.
- O download do Kaggle funciona sem login para este dataset público.
"""

import hashlib
import io
import urllib.request
import zipfile
from pathlib import Path

DATASET = "adaoduque/campeonato-brasileiro-de-futebol"
VERSAO = 18
URL = f"https://www.kaggle.com/api/v1/datasets/download/{DATASET}?datasetVersionNumber={VERSAO}"

PASTA_RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

SHA256 = {
    "campeonato-brasileiro-full.csv": "4e5bee3000f27dfa71f30389aa4af11c03725393a82d8814fb373659ee94891b",
    "campeonato-brasileiro-gols.csv": "717aecabde608ac843d3899ee88c872e15b3b5b002217e3459131d4c4ba98f4e",
    "campeonato-brasileiro-cartoes.csv": "6b48b7ceaf2ea5018972f12821571870a9ebd277fca1ccb66045465911fc6b33",
    "campeonato-brasileiro-estatisticas-full.csv": "9188b0bf62db1dcc2d7bcf84a69a352db13d48f37d92a4c87388b113c5d7d012",
}


def sha256(conteudo: bytes) -> str:
    return hashlib.sha256(conteudo).hexdigest()


def baixar(pasta: Path = PASTA_RAW) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    print(f"Baixando {DATASET} (versão {VERSAO})...")
    req = urllib.request.Request(URL, headers={"User-Agent": "pipeline-brasileirao"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        zip_bytes = resp.read()

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for nome, esperado in SHA256.items():
            conteudo = zf.read(nome)
            obtido = sha256(conteudo)
            if obtido != esperado:
                raise ValueError(f"{nome}: SHA-256 {obtido} difere do esperado {esperado}")
            (pasta / nome).write_bytes(conteudo)
            linhas = conteudo.count(b"\n")
            print(f"  ok  {nome}  ({linhas} linhas com cabeçalho)")
        (pasta / "Legenda.txt").write_bytes(zf.read("Legenda.txt"))


if __name__ == "__main__":
    baixar()
