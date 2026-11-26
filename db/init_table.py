from pathlib import Path
from sqlalchemy import text
from db.db import Sessao

caminho = Path(__file__).parent / "schema.sql"

with Sessao.begin() as sessao:
    sessao.connection().exec_driver_sql(caminho.read_text(encoding="utf-8"))

with Sessao() as sessao:
    tabelas = sessao.execute(text(
        "select table_name from information_schema.tables "
        "where table_schema = 'public' order by 1"
    )).scalars().all()
    print(tabelas)

# rodar python -m db.init_table