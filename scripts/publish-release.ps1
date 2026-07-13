param(
    [Parameter(Mandatory = $true)]
    [string]$Version
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$tag = "v$Version"
$versionedAsset = Join-Path $root "installer\output\TranscritorLocal-Setup-$Version-win64.exe"
$stableAsset = Join-Path $root 'installer\output\Voxnote-Setup-win64.exe'

if (-not (Test-Path -LiteralPath $versionedAsset)) {
    throw "Instalador não encontrado: $versionedAsset"
}

Copy-Item -LiteralPath $versionedAsset -Destination $stableAsset -Force

gh release view $tag --repo Marcosemanuel/voxnote *> $null
if ($LASTEXITCODE -eq 0) {
    gh release upload $tag $versionedAsset $stableAsset --clobber --repo Marcosemanuel/voxnote
} else {
    gh release create $tag $versionedAsset $stableAsset --repo Marcosemanuel/voxnote --title "Voxnote $Version" --generate-notes
}

if ($LASTEXITCODE -ne 0) {
    throw "Não foi possível publicar a release $tag."
}

$release = gh release view $tag --repo Marcosemanuel/voxnote --json assets | ConvertFrom-Json
if ($release.assets.name -notcontains 'Voxnote-Setup-win64.exe') {
    throw 'O ativo permanente não foi encontrado na release publicada.'
}

Write-Host "Release publicada: $tag"
Write-Host 'Link permanente: https://github.com/Marcosemanuel/voxnote/releases/latest/download/Voxnote-Setup-win64.exe'
