$ErrorActionPreference = 'Stop'
$env:PYTHONPATH = Join-Path $PSScriptRoot 'src'
& (Join-Path $PSScriptRoot '.venv\Scripts\pythonw.exe') -m transcritor.app

