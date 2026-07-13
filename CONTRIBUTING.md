# Contribuindo com o Voxnote

## Antes de abrir uma alteração

1. Leia `AGENTS.md` e a documentação aplicável em `docs/`.
2. Confirme que a alteração permanece no escopo Windows 10/11 x64.
3. Abra uma issue quando houver mudança de requisito, contrato ou arquitetura.

## Fluxo local

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
pytest -q
ruff check src tests
ruff format --check src tests
mypy src
```

Para validar a landing:

```powershell
cd landing
npm ci
npm run build
```

## Pull requests

- Explique o problema, a solução e os critérios de aceite atendidos.
- Inclua testes e atualize a documentação correspondente.
- Não inclua áudio, modelos, bancos locais, logs ou artefatos de build.
- Não altere o comportamento de fallback CPU/GPU sem registrar uma decisão em `docs/DECISIONS.md`.

## Escopo de plataforma

O projeto aceita contribuições somente para Windows 10/11 x64. Linux, macOS, Windows ARM e Windows 32 bits estão fora do escopo.
