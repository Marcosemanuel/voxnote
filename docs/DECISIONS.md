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

## ADR-016 — Aviso de atualização por GitHub Releases

- Data: 2026-07-13
- Estado: aceita
- Contexto: o usuário precisa saber quando uma versão nova do Voxnote estiver publicada, sem criar atualização automática ou interferir no processamento local.
- Decisão: na abertura, uma thread de segundo plano consulta somente os metadados da última release pública no GitHub. Se a versão for superior à instalada, a interface mostra um aviso e abre a página da release no navegador mediante ação explícita do usuário.
- Consequências: nenhum áudio, transcrição, credencial ou dado do usuário é enviado; em modo offline ou em falha da consulta o aplicativo permanece utilizável e não mostra erro. O download e a instalação continuam manuais.

## ADR-017 — Captura manual local para reuniões

- Data: 2026-07-13
- Estado: aceita
- Contexto: o produto deve atender reuniões no Google Meet sem depender de plano Workspace, extensão de navegador ou envio de áudio a servidores.
- Decisão: criar, após o MVP, uma capacidade de captura manual do áudio da saída do Windows e do microfone opcional. A captura será local, segmentada em disco, com transcrição provisória em fila e reprocessamento final para precisão. WASAPI loopback é o candidato inicial da prova técnica, atrás de um port de captura isolado.
- Consequências: a funcionalidade exige confirmação explícita de autorização para gravar, novos estados de sessão, testes de dispositivos e preservação de blocos em interrupções. Não será apresentada como integração oficial com Google Meet nem como transcrição instantânea de alta precisão.

## ADR-018 — Helper nativo isolado para captura WASAPI

- Data: 2026-07-13
- Estado: proposta, condicionada à prova técnica F9.1
- Contexto: a captura precisa continuar estável mesmo quando a inferência estiver atrasada e não pode depender da thread de UI, de Python para transportar PCM ou de runtime técnico instalado pelo usuário.
- Decisão: avaliar um helper C++20 x64, compilado com Windows SDK e CRT estático, usando WASAPI/MMDevice API. O aplicativo o controla por `QProcess` e JSON Lines; o helper grava blocos PCM WAV diretamente no disco e comunica apenas eventos e metadados.
- Consequências: o pipeline de build passa a compilar um binário nativo e testá-lo no instalador. O helper só será aceito após 60 minutos sem perda de bloco finalizado, sem crescimento contínuo de RAM e com drift inferior a 250 ms entre trilhas.

## ADR-019 — Modo universal final-first e texto provisório opcional

- Data: 2026-07-13
- Estado: aceita para o planejamento da Fase 9
- Contexto: texto durante a chamada pode consumir recursos necessários ao navegador e à captura, principalmente em máquinas CPU com 8 GB ou 16 GB de RAM.
- Decisão: usar `Capturar e transcrever ao final` como modo universal. `Acompanhar texto durante a reunião` é opcional, condicionado a benchmark local e suspenso automaticamente quando a fila provisória ultrapassar 90 segundos.
- Consequências: preservar áudio tem prioridade sobre latência. O texto provisório e o reconhecimento final são execuções separadas; nenhum deles sobrescreve revisão humana.
- Substitui: a obrigatoriedade implícita de transcrição provisória durante toda captura descrita na ADR-017; preserva o restante da decisão.

## ADR-020 — Primeira implementação da captura WASAPI em Python empacotável

- Data: 2026-07-13
- Estado: aceita para a primeira entrega funcional da Fase 9
- Contexto: o ambiente de desenvolvimento não possui compilador C++/Windows SDK disponível para validar e empacotar o helper proposto na ADR-018. A funcionalidade aprovada precisa continuar utilizável e verificável no aplicativo atual.
- Decisão: implementar o port de captura isolado com PyAudioWPatch, que expõe os dispositivos WASAPI loopback e de microfone ao processo Python já distribuído pelo Voxnote. Cada trilha grava blocos WAV atômicos, confirma journal com fsync e comunica apenas metadados à interface.
- Consequências: a aplicação funciona sem extensão do Meet, OAuth ou serviço remoto e mantém as trilhas separadas. O helper C++20 da ADR-018 permanece uma alternativa de endurecimento após o benchmark de 60 minutos; não foi declarado como implementado.
- Substitui: a exigência de helper C++20 para a primeira entrega da Fase 9; não substitui os critérios de estabilidade da ADR-018.

## ADR-021 — Retentativa imutável e sincronização observável das trilhas

- Data: 2026-07-13
- Estado: aceita
- Contexto: uma sessão pode falhar depois de confirmar blocos no journal, e duas fontes de áudio não podem ser misturadas sem controle de tempo.
- Decisão: recuperar o journal também para sessões `failed`; expor `Transcrever`/`Reprocessar` para qualquer sessão com blocos persistidos; criar uma nova `transcription_run` a cada tentativa. Os blocos recebem tempo relativo ao mesmo QPC e o serviço compara o offset entre trilhas por sequência, alertando em variação maior que 250 ms.
- Consequências: nenhuma revisão ou reconhecimento anterior é sobrescrito. A primeira entrega preserva e ordena as fontes por timestamp, mas não faz mistura de PCM ou correção destrutiva de fala; o benchmark real continua obrigatório.

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
