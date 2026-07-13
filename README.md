# Voxnote

Aplicativo desktop local para transcrição de áudios longos no Windows 10/11 x64. O fluxo do produto é:

`Adicionar áudio → Transcrever → Revisar → Exportar`

O processamento ocorre no computador do usuário, com suporte a CPU e fallback seguro quando a aceleração NVIDIA não estiver disponível.

## Repositório

| Diretório/arquivo | Finalidade |
| --- | --- |
| `src/transcritor/` | Aplicativo desktop, domínio, motor, banco e interface Qt/QML |
| `tests/` | Testes automatizados Python/Qt |
| `landing/` | Landing pública React/Vite para download |
| `assets/` | Marca, fontes e ícones distribuídos com o produto |
| `installer/` | Script Inno Setup para instalador Windows x64 |
| `scripts/` | Automação de build e empacotamento |
| `docs/` | Produto, requisitos, arquitetura, UX, testes e decisões |
| `.github/` | CI, templates de issues e pull requests |

## Desenvolvimento do aplicativo

Requisitos: Windows 10/11 x64 e Python 3.12 x64.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\run.ps1
```

Na primeira transcrição, o modelo selecionado é baixado para `%LOCALAPPDATA%\Transcritor\models`.

## Testes e qualidade

```powershell
pytest -q
ruff check src tests
ruff format --check src tests
mypy src
```

## Landing

```powershell
cd landing
npm ci
npm run dev
npm run build
```

A landing aponta por padrão para o ativo permanente da Release pública mais recente: `https://github.com/Marcosemanuel/voxnote/releases/latest/download/Voxnote-Setup-win64.exe`. Defina `VITE_DOWNLOAD_URL` em `landing/.env` somente para substituir o link em outro ambiente. A landing não recebe áudio nem acessa o microfone.

## Instalador

```powershell
.\scripts\build.ps1
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" .\installer\TranscritorLocal.iss
```

O instalador gerado fica em `installer/output/` e não deve ser commitado.

Para publicar uma Release, use `./scripts/publish-release.ps1 -Version <versão>` depois de gerar o instalador. Ele publica também o ativo permanente consumido pela landing.

## Documentação obrigatória

- [Regras para agentes](AGENTS.md)
- [Produto](docs/PRODUCT.md)
- [Requisitos](docs/REQUIREMENTS.md)
- [Arquitetura](docs/ARCHITECTURE.md)
- [UX](docs/UX.md)
- [Desenvolvimento](docs/DEVELOPMENT.md)
- [Testes](docs/TESTING.md)
- [Roadmap](docs/ROADMAP.md)
- [Estado real](docs/STATUS.md)
- [Decisões](docs/DECISIONS.md)
- [Landing](docs/LANDING.md)
- [Contribuição](CONTRIBUTING.md)
- [Segurança](SECURITY.md)

## Plataformas

Suportado: Windows 10 1809+ x64 e Windows 11 x64.

Fora do escopo: Windows 32 bits, Windows ARM, Linux e macOS.
