# Registro de decisões arquiteturais

Decisões são append-only. Para substituir uma decisão, adicione outra indicando qual ADR foi substituída. Não reescreva o histórico.

## ADR-001 — Plataforma exclusiva Windows x64

- Data: 2026-07-12
- Estado: aceita
- Decisão: suportar Windows 10 1809+ x64 e Windows 11 x64.
- Consequência: não criar abstrações ou pipelines para Linux, macOS, ARM ou 32 bits.

## ADR-002 — PySide6 Widgets para interface

- Data: 2026-07-12
- Estado: aceita
- Decisão: usar Python 3.12 x64 e PySide6 Widgets.
- Motivo: stack única com o motor Python, UI nativa e menor complexidade que frontend web com sidecar.

## ADR-003 — faster-whisper e CTranslate2

- Data: 2026-07-12
- Estado: aceita
- Decisão: usar faster-whisper/CTranslate2 com CPU obrigatória e GPU NVIDIA opcional.
- Consequência: GPU deve ser testada em runtime e toda falha deve retornar para CPU.

## ADR-004 — Modelos sob demanda

- Data: 2026-07-12
- Estado: aceita
- Decisão: não incluir pesos no instalador nem no Git.
- Consequência: criar gerenciador de download retomável, verificação de integridade e remoção.

## ADR-005 — PyAV como decodificador inicial

- Data: 2026-07-12
- Estado: aceita
- Decisão: usar PyAV e suas bibliotecas FFmpeg incorporadas; não distribuir `ffmpeg.exe` e `ffprobe.exe` sem necessidade comprovada.
- Consequência: validar os dez formatos no build empacotado.

## ADR-006 — SQLite com checkpoints

- Data: 2026-07-12
- Estado: aceita
- Decisão: persistir estado e segmentos incrementalmente em SQLite/WAL.
- Consequência: trabalhos longos devem retomar do último checkpoint válido.

## ADR-007 — PyInstaller onedir e Inno Setup

- Data: 2026-07-12
- Estado: aceita
- Decisão: empacotar em `onedir` e criar instalador x64 por usuário com Inno Setup.
- Motivo: reduzir extração temporária e problemas com DLLs nativas.

## ADR-008 — Texto original imutável

- Data: 2026-07-12
- Estado: aceita
- Decisão: preservar separadamente reconhecimento original e revisão do usuário.
- Consequência: exportação permite escolher a versão, e edições nunca sobrescrevem a evidência original.

## ADR-009 — Retomada por timestamp confirmado

- Data: 2026-07-12
- Estado: aceita
- Contexto: contar segmentos de uma nova transcrição completa não garante o mesmo alinhamento do VAD.
- Decisão: retomar pelo maior timestamp final confirmado usando `clip_timestamps`.
- Consequências: o áudio anterior não é retranscrito e novos segmentos continuam a sequência persistida.

## ADR-010 — UPSERT preserva revisão humana

- Data: 2026-07-12
- Estado: aceita
- Decisão: conflitos de checkpoint atualizam métricas e reconhecimento, mas preservam texto revisado.
- Consequências: retomadas não apagam correções já confirmadas pelo usuário.

## ADR-011 — Identidade visual Voxnote embutida no pacote

- Data: 2026-07-12
- Estado: aceita
- Contexto: a marca enviada pelo proprietário define símbolo, nome e paleta que devem aparecer no aplicativo Windows sem depender de arquivos externos.
- Decisão: incluir o símbolo transparente e o ícone `.ico` em `assets/branding`, empacotá-los com o PyInstaller e aplicar a paleta oficial na interface. O diretório de dados permanece `%LOCALAPPDATA%\Transcritor` para preservar instalações existentes.
- Consequências: o produto se apresenta como Voxnote, mas atualizações não deslocam banco, modelos, logs ou transcrições já existentes.

## ADR-012 — Ícones vetoriais Lucide na interface

- Data: 2026-07-12
- Estado: aceita
- Contexto: os ícones padrão do Windows destoam da linguagem visual Voxnote e não mantêm a mesma aparência em escalas altas.
- Decisão: usar os SVGs Lucide incluídos em `assets/icons/lucide`, renderizados pelo Qt e coloridos apenas em preto ou azul de destaque.
- Consequências: ícones ficam nítidos em DPI alto; o arquivo `assets/icons/lucide/LICENSE` deve acompanhar qualquer distribuição do aplicativo.

## ADR-013 — Landing estática em Vercel com download no GitHub Releases

- Data: 2026-07-12
- Estado: aceita
- Contexto: a página pública precisa ser rápida e independente do aplicativo Windows, enquanto o instalador deve manter rastreabilidade de release e checksum.
- Decisão: manter a landing React/Vite em `landing/`, hospedar seus arquivos estáticos na Vercel e apontar `VITE_DOWNLOAD_URL` diretamente para o instalador em GitHub Releases. Three.js fica limitado a uma cena decorativa sem captura de áudio.
- Consequências: a landing pode ser publicada sem hospedar binários na Vercel; uma release pública precisa existir antes de habilitar o CTA de download.

## ADR-014 — Onda Canvas 2D para o hero da landing

- Data: 2026-07-13
- Estado: aceita
- Contexto: a implementação efetiva da landing usa Canvas 2D, não Three.js. A cena precisa manter leitura clara e baixo custo em desktop e mobile.
- Decisão: usar uma onda Canvas 2D limitada a 30 fps, com densidade, amplitude e interação reduzidas em telas menores.
- Consequências: a landing não adiciona dependência Three.js; a animação respeita `prefers-reduced-motion` e reduz uso de CPU/GPU.
- Substitui: a parte de cena decorativa da ADR-013.

## ADR-015 — Qt Quick/QML substitui Widgets como camada visual

- Data: 2026-07-13
- Estado: aceita
- Contexto: o frontend QWidget/QSS acumulou larguras fixas, composição monolítica e clipping em escalas altas do Windows.
- Decisão: usar PySide6 6.11.1, `QQmlApplicationEngine`, Qt Quick Controls 2 e componentes Voxnote em QML. O domínio e a infraestrutura Python permanecem inalterados.
- Consequências: a UI ganha layouts responsivos e delegates reutilizáveis. A versão QWidget fica disponível temporariamente por `VOXNOTE_LEGACY_UI=1` e será removida após paridade funcional e visual comprovada.
- Substitui: ADR-002 quanto à tecnologia de apresentação; preserva Python/PySide6 como stack única.

## Modelo para nova decisão

```text
## ADR-XXX — Título

- Data: AAAA-MM-DD
- Estado: proposta | aceita | substituída | rejeitada
- Contexto:
- Decisão:
- Consequências:
- Substitui: ADR-XXX, quando aplicável
```
