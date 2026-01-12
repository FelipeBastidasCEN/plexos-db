@echo off

echo Iniciando TEST REAL
uv run --no-cache plexos-db import --input "C:\Users\felipe.bastidas\test\PCP\20251011\Datos\Model PRGdia_Full_Definitivo Solution\Model PRGdia_Full_Definitivo Solution.zip" --output "C:\Users\felipe.bastidas\test\PCP\20251011\Datos\Model PRGdia_Full_Definitivo Solution\pcp.duckdb"

echo TEST FINALIZADO
