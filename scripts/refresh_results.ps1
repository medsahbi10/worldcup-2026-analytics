# Refresh fixtures + group standings from FBref and rebuild the dbt marts,
# updating the local warehouse (data/wc2026.duckdb). Run on demand, or schedule
# it (see below). Steps are SEQUENTIAL because DuckDB allows only one writer.
#
# NOTE: stop the local API first (it holds the DuckDB open) — otherwise the
#       write step fails with a file-lock error.
#
# Schedule it (every 6 hours) via Windows Task Scheduler:
#   schtasks /create /tn "WC2026 Refresh" /sc hourly /mo 6 ^
#     /tr "powershell -NoProfile -ExecutionPolicy Bypass -File \"%CD%\scripts\refresh_results.ps1\""

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot      # scripts/ -> repo root
Set-Location $root
$env:PYTHONPATH = "src"
$dg = ".venv\Scripts\dagster.exe"

Write-Host "[$(Get-Date -Format s)] Refreshing fixtures..."
& $dg asset materialize -m wc2026.definitions --select raw_fixtures
Write-Host "[$(Get-Date -Format s)] Refreshing group standings..."
& $dg asset materialize -m wc2026.definitions --select raw_group_standings
Write-Host "[$(Get-Date -Format s)] Rebuilding dbt marts..."
& $dg asset materialize -m wc2026.definitions --select dbt_marts
Write-Host "[$(Get-Date -Format s)] Refresh complete."
