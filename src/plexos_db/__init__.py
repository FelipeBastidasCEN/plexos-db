from pathlib import Path
from plexos_db.model.plexos import ApiPlexos
from plexos_db.model.ddb import ApiDuckDB

TEST_PATH: str = r"C:\Users\felipe.bastidas\test\PCP\20251011\Datos\Model PRGdia_Full_Definitivo Solution\Model PRGdia_Full_Definitivo Solution.zip"
TEST_DDB: str = r"C:\Users\felipe.bastidas\test\PCP\20251011\Antecedentes"


def main() -> None:
    print("Hello from plexos-db!")
    plx = ApiPlexos.from_zip(Path(TEST_PATH))
    t_object = plx.t_object()
    print(t_object[1])
    ddb = ApiDuckDB("test.ddb", Path(TEST_DDB))
    ddb.connect()
    # ddb.create_db()
    ddb.t_object(t_object)
