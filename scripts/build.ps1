$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    throw 'Ambiente .venv não encontrado. Crie-o e instale o projeto antes do build.'
}

Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
$env:PYTHONPATH = Join-Path $Root 'src'

function Invoke-Checked {
    param([Parameter(Mandatory = $true)][string]$Executable, [Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao executar $Executable (código $LASTEXITCODE)."
    }
}

$qmlFiles = Get-ChildItem -Recurse -Path 'src\transcritor\qml' -Filter '*.qml' | Select-Object -ExpandProperty FullName
Invoke-Checked .\.venv\Scripts\python.exe -m pytest -q
Invoke-Checked .\.venv\Scripts\python.exe -m ruff check src tests
Invoke-Checked .\.venv\Scripts\python.exe -m ruff format --check src tests
Invoke-Checked .\.venv\Scripts\python.exe -m mypy src
Invoke-Checked .\.venv\Scripts\pyside6-qmllint.exe --unqualified=disable @qmlFiles
Invoke-Checked .\.venv\Scripts\pyinstaller.exe --noconfirm --clean --windowed --onedir `
    --name 'TranscritorLocal' `
    --paths src `
    --icon "assets/branding/voxnote-app-icon.ico" `
    --add-data "assets;assets" `
    --add-data "src/transcritor/qml;qml" `
    --collect-all faster_whisper `
    --collect-all ctranslate2 `
    --collect-all av `
    --collect-all pyaudiowpatch `
    src\transcritor\app.py

Write-Host "Build criado em $Root\dist\TranscritorLocal"
