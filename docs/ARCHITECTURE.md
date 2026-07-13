# Arquitetura

## 1. Stack aprovada

| Área | Tecnologia |
|---|---|
| Linguagem | Python 3.12 x64 |
| Interface | PySide6 6.11.1 + Qt Quick/QML; Widgets mantidos temporariamente como fallback interno |
| Tipografia | Manrope variável incorporada ao pacote (OFL-1.1) |
| Inferência | faster-whisper + CTranslate2 |
| Decodificação | PyAV |
| VAD | Silero VAD via faster-whisper |
| Persistência | SQLite |
| Empacotamento | PyInstaller `onedir` |
| Instalador | Inno Setup x64 |
| Testes | pytest + pytest-qt |
| Qualidade | Ruff + mypy |
| Distribuição | GitHub Actions + GitHub Releases |

Mudanças de stack exigem ADR em `docs/DECISIONS.md` e aprovação do proprietário.

O build inclui `assets/fonts/Manrope-Variable.ttf` e os ativos de marca em `assets/` dentro de `_internal/assets`. `transcritor.app.register_manrope()` registra o arquivo antes de criar a interface; a instalação não depende de fonte prévia no Windows. O executável recebe `assets/branding/voxnote-app-icon.ico` como ícone e a interface carrega `voxnote-symbol.png` empacotado.

Os ícones de interface ficam em `assets/icons/lucide/` e são renderizados pelo Qt a partir de SVG, preservando o traço vetorial de 2px em qualquer escala de DPI. A licença correspondente permanece ao lado dos ativos.

## 1.1 Landing pública

A página de download fica isolada em `landing/`, usa React + Vite e é hospedada pela Vercel como site estático. O hero usa Canvas 2D para uma onda decorativa de baixa frequência; a página não grava, não recebe áudio e não chama serviços de transcrição. O download é servido pelo GitHub Releases via `VITE_DOWNLOAD_URL`, mantendo o arquivo de instalador fora da hospedagem Vercel.

## 2. Camadas

```text
UI Qt Quick/QML
    -> Application Services / Use Cases
        -> Domain
            -> Ports
                -> Infrastructure
```

### UI

`QQmlApplicationEngine` carrega o shell declarativo. `QmlController` expõe propriedades, sinais e slots de
apresentação e delega persistência, modelos, exportação e inferência aos serviços Python existentes. A UI QWidget
permanece acessível apenas por `VOXNOTE_LEGACY_UI=1` durante a validação da migração.

### Application

Orquestra casos de uso: validar arquivo, preparar trabalho, iniciar, pausar, retomar, revisar e exportar.

### Domain

Entidades, estados, regras e contratos independentes de Qt, SQLite e faster-whisper.

### Infrastructure

PyAV, faster-whisper, CTranslate2, SQLite, sistema de arquivos, Windows, downloads e exportadores.

## 3. Estrutura alvo

```text
src/transcritor/
├── app.py
├── domain/
│   ├── entities.py
│   ├── enums.py
│   ├── errors.py
│   └── ports.py
├── application/
│   ├── jobs.py
│   ├── models.py
│   ├── review.py
│   └── export.py
├── infrastructure/
│   ├── audio/
│   ├── inference/
│   ├── persistence/
│   ├── hardware/
│   ├── downloads/
│   └── exporters/
└── ui/
    ├── windows/
    ├── dialogs/
    ├── widgets/
    ├── workers/
    └── resources/
```

## 4. Estado do trabalho

Estados permitidos:

```text
pending
validating
downloading_model
ready
transcribing
pausing
paused
cancelling
cancelled
completed
failed
```

Transições inválidas devem falhar explicitamente. Não representar o ciclo inteiro com booleanos.

## 5. Pipeline

```text
Arquivo somente leitura
  -> validação por conteúdo
  -> registro do trabalho
  -> decodificação progressiva
  -> VAD conservador
  -> inferência por segmentos
  -> checkpoint por segmento
  -> análise de sinais de revisão
  -> conclusão
  -> revisão humana
  -> exportação
```

## 6. Concorrência

- Thread principal: somente UI.
- Worker de download: downloads e verificação.
- Worker de transcrição: decodificação, VAD e inferência.
- Persistência: operações curtas e coordenadas; nunca compartilhar conexão SQLite entre threads de forma insegura.
- Um único trabalho pesado ativo por vez.
- Pausa e cancelamento são cooperativos entre segmentos.
- Threads não podem ser terminadas à força.

## 7. Persistência

Configuração inicial:

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;
```

Entidades mínimas:

- `projects`
- `audio_files`
- `transcription_jobs`
- `segments`
- `words`
- `glossaries`
- `models`
- `app_settings`
- `schema_migrations`

Cada segmento preserva texto reconhecido, texto revisado, timestamps, métricas técnicas, status de revisão e parâmetros da execução.

Migrações devem ser numeradas, transacionais quando possível e testadas em cópia de banco existente.

Na inicialização, migrações inspecionam o schema real antes de adicionar colunas. Trabalhos encontrados
em estados transitórios (`transcribing`, `pausing` ou `cancelling`) são recuperados como `paused`.

Checkpoints usam UPSERT que atualiza o reconhecimento automático sem sobrescrever `revised_text` quando
o segmento já foi revisado. A retomada começa no maior timestamp `end` confirmado e atribui novos índices
a partir do último `segment_index` persistido.

## 8. Diretórios Windows

```text
Programa:       %LOCALAPPDATA%\Programs\Transcritor\
Configuração:   %LOCALAPPDATA%\Transcritor\config\
Banco:          %LOCALAPPDATA%\Transcritor\data\transcritor.db
Modelos:        %LOCALAPPDATA%\Transcritor\models\
Logs:           %LOCALAPPDATA%\Transcritor\logs\
Cache:          %LOCALAPPDATA%\Transcritor\cache\
Backups:        %LOCALAPPDATA%\Transcritor\backups\
```

Diretórios devem ser resolvidos por um serviço central, nunca espalhados como strings.

## 9. Hardware e fallback

1. CPU é o backend universal.
2. GPU é opcional.
3. Detecção nominal não basta; consultar VRAM e testar os tipos CUDA disponíveis no CTranslate2.
4. Falha de GPU registra diagnóstico e retorna para CPU.
5. Lote começa conservador e pode ser calibrado.
6. Cache de calibração é invalidado por mudança de GPU, driver, modelo, engine ou compute type.

Perfis de UI não devem expor detalhes internos:

| Perfil | Direção técnica |
|---|---|
| Leve | small, CPU int8 |
| Equilibrado | medium, CPU int8 ou GPU limitada |
| Alta precisão | large-v3 |
| Rápido | turbo |

## 10. Segurança e privacidade

- Processamento local.
- Rede apenas para modelos, versões e links explicitamente acionados.
- Downloads devem usar HTTPS, arquivo temporário, retomada e hash.
- Logs não incluem texto integral por padrão.
- Pacote de diagnóstico deve remover dados pessoais.
- Áudio original nunca é alterado.
- Exclusão de projeto não remove áudio original.

## 11. Empacotamento

- Build Windows x64 nativo.
- PyInstaller `onedir`; não migrar para `onefile` sem benchmark e ADR.
- Inno Setup por usuário em `%LOCALAPPDATA%`.
- Instalador valida Windows e arquitetura.
- Dados e modelos sobrevivem a atualização.
- Dependências são fixadas e suas licenças registradas.
- Modelos não entram no instalador.
