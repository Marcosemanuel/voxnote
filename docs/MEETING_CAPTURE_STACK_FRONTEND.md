# Stack e frontend — captura local de reuniões

## 1. Estado e limite

Este documento define a stack alvo e o planejamento de frontend da Fase 9. A primeira entrega funcional usa PyAudioWPatch/WASAPI dentro do pacote Python, com telas QML conectadas a captura real. O helper WASAPI C++20 continua como endurecimento posterior, condicionado ao benchmark de 60 minutos.

Requisitos cobertos: `FR-060` a `FR-067`, `NFR-016` a `NFR-020` e `AC-016` a `AC-020`.

Fluxo aprovado:

`Preparar -> Testar áudio -> Capturar -> Verificar integridade -> Transcrever com precisão -> Revisar -> Exportar`

## 2. Decisão de produto

O modo universal será **Capturar agora e transcrever ao final**. Ele funciona em CPU comum e prioriza a preservação do áudio.

O modo **Acompanhar texto durante a reunião** será opcional. Só será habilitado quando o benchmark local demonstrar capacidade suficiente. O texto exibido nesse modo será sempre identificado como provisório e nunca substituirá o reconhecimento final.

Na primeira entrega:

- o usuário inicia e encerra manualmente;
- a saída do Windows e o microfone local são trilhas separadas;
- a trilha de saída recebe o rótulo `Reunião` e a trilha de microfone recebe `Você`;
- não haverá identificação automática de participantes remotos;
- não haverá extensão, bot, OAuth, scraping ou integração oficial com Google Meet;
- o áudio confirmado em disco tem prioridade sobre qualquer transcrição em andamento.

## 3. Stack completa

| Camada | Tecnologia | Responsabilidade | Motivo |
|---|---|---|---|
| Interface | PySide6 6.11.1 + Qt Quick/QML | Telas, estados, acessibilidade e medidores | Preserva o frontend oficial e o design system existente |
| Orquestração | Python 3.12 x64 | Casos de uso, filas, políticas de hardware e integração com SQLite | Reutiliza a aplicação e o motor atuais |
| Processo de captura atual | PyAudioWPatch no processo Python | Captura WASAPI, blocos e eventos de dispositivo | Entrega empacotável validada; sem runtime instalado pelo usuário |
| Processo de captura alvo | C++20 x64 + Windows SDK | Captura WASAPI, relógio, blocos e eventos de dispositivo | Alternativa de endurecimento após o benchmark de 60 minutos |
| API de áudio | WASAPI + MMDevice API | Loopback da saída e captura do microfone | API nativa suportada no Windows 10/11 x64 |
| IPC | `QProcess` + JSON Lines em stdin/stdout | Comandos, eventos, telemetria e encerramento controlado | Protocolo simples, testável e sem servidor local |
| Arquivos de captura | PCM WAV por blocos de 5 segundos | Fonte recuperável e sem perdas | Cada bloco é autocontido e pode ser confirmado atomicamente |
| Manifesto | JSON versionado + SHA-256 por bloco | Integridade, ordem, relógio e recuperação | Permite reconstruir a sessão sem depender do processo anterior |
| Normalização | PyAV 15.0.0 | Leitura, resample e preparação para 16 kHz mono | Dependência já distribuída pelo produto |
| ASR | faster-whisper 1.2.0 + CTranslate2 | Reconhecimento CPU/GPU | Motor atual, com CPU obrigatória e NVIDIA opcional |
| VAD | Silero VAD via faster-whisper | Remover silêncio antes da inferência | Reduz custo e alucinações em pausas |
| Texto provisório | Janela deslizante + sobreposição + LocalAgreement-2 próprio | Estabilizar prefixos sem nova dependência | Evita publicar palavras ainda instáveis |
| Persistência | SQLite/WAL + migrações | Sessões, trilhas, blocos, execuções e segmentos | Checkpoints curtos e recuperação já adotados pelo app |
| Diagnóstico | `psutil`, hardware detector e logs estruturados | Disco, fila, RTF, backend e falhas | Não registra áudio nem texto integral por padrão |
| Build nativo | CMake + MSVC x64, CRT estático `/MT` | Gerar `voxnote-capture.exe` | Binário autocontido para o instalador |
| Empacotamento | PyInstaller `onedir` + Inno Setup x64 | Distribuir app, helper e licenças | Mantém o pipeline oficial do Voxnote |
| CI | GitHub Actions Windows | Compilar helper, testar Python/QML e montar instalador | Release reproduzível em Windows x64 |

### 3.1 APIs nativas do helper

O helper deve usar diretamente:

- `IMMDeviceEnumerator` para enumerar endpoints;
- `IMMNotificationClient` para troca, remoção e mudança do dispositivo padrão;
- `IAudioClient` e `IAudioCaptureClient` para abrir e ler os fluxos;
- `IAudioClock` e posições de dispositivo para sincronizar as trilhas;
- loopback do endpoint como caminho universal;
- captura por árvore de processo apenas como melhoria opcional em builds Windows compatíveis.

Não adotar NAudio/.NET, PortAudio ou um segundo runtime na primeira entrega. Essas opções aumentariam o pacote e não eliminariam a necessidade de tratar WASAPI, dispositivos e recuperação.

### 3.2 Contrato do processo

O Python inicia um único `voxnote-capture.exe` por sessão usando `QProcess`. Cada linha é um objeto JSON UTF-8 com `protocol_version`, `request_id` ou `event_id`, `type`, `timestamp_utc` e `payload`.

Comandos mínimos:

| Comando | Resultado esperado |
|---|---|
| `list_devices` | Saídas e entradas ativas, com ID estável e dispositivo padrão |
| `test_signal` | Nível RMS/pico por trilha durante cinco segundos |
| `start_session` | Cria trilhas, abre endpoints e confirma diretório de sessão |
| `stop_session` | Fecha bloco atual, sincroniza manifesto e encerra dispositivos |
| `get_status` | Estado, duração, último bloco e falhas recuperáveis |
| `shutdown` | Liberação cooperativa e encerramento do helper |

Eventos mínimos:

`device_list`, `signal_level`, `session_started`, `block_committed`, `device_changed`, `capture_degraded`, `disk_warning`, `session_stopped` e `fatal_error`.

O helper nunca envia PCM pelo stdout. Ele grava os blocos diretamente no diretório da sessão e comunica apenas metadados. Isso impede que a UI ou o pipe se tornem gargalo da captura.

## 4. Armazenamento e recuperação

Diretório por sessão:

```text
%LOCALAPPDATA%\Transcritor\captures\<session_uuid>\
├── manifest.json
├── system\
│   ├── 00000001.wav
│   └── 00000002.wav
├── microphone\
│   ├── 00000001.wav
│   └── 00000002.wav
└── recovery.log
```

Regra de escrita:

1. gravar `00000001.wav.partial`;
2. finalizar cabeçalho e fazer `FlushFileBuffers`;
3. calcular SHA-256;
4. renomear atomicamente para `00000001.wav`;
5. registrar o bloco em transação SQLite curta;
6. emitir `block_committed`.

O encerramento forçado pode perder somente o bloco `.partial` aberto. Com blocos de cinco segundos, a perda máxima planejada é inferior ou igual a cinco segundos; o gate real será medido na prova técnica.

### 4.1 Schema alvo

O schema atual de arquivos permanece intacto. A migração da Fase 9 adicionará:

| Tabela | Campos essenciais |
|---|---|
| `meeting_sessions` | id, título, idioma, modo, estado, consent_at, started_at, ended_at, capture_path, error_code |
| `capture_tracks` | id, session_id, kind, device_id, device_name, sample_rate, channels, clock_origin |
| `capture_blocks` | id, track_id, sequence, path, started_ms, duration_ms, bytes, sha256, committed_at |
| `transcription_runs` | id, session_id, kind (`provisional`/`final`/`retry`), model, backend, parameters_json, state |
| `run_segments` | id, run_id, track_kind, start_ms, end_ms, recognized_text, revised_text, status, metrics_json |

Uma execução final cria novos registros. Não atualiza segmentos provisórios e não sobrescreve `revised_text`.

## 5. Pipeline de transcrição

### 5.1 Captura universal

1. Helper confirma cada bloco em disco.
2. Python registra o bloco e acompanha espaço livre.
3. A UI mostra duração, sinal e integridade; não mostra percentual.
4. Ao encerrar, o app verifica sequência, hash e relógios.
5. O motor normaliza progressivamente as trilhas com PyAV.
6. VAD conservador separa regiões de fala.
7. faster-whisper gera a execução final.
8. Trechos sinalizados podem ser repetidos com contexto limitado.
9. O usuário abre a revisão e exporta.

### 5.2 Texto provisório opcional

- janela de 25 a 30 segundos;
- sobreposição suficiente para evitar corte de palavras na borda;
- prefixo publicado somente após duas hipóteses consecutivas compatíveis;
- modelo carregado uma vez por sessão;
- processamento sequencial e prioridade normal ou abaixo do normal;
- reservar pelo menos dois processadores lógicos para sistema, navegador e captura;
- se a fila provisória ultrapassar 90 segundos, suspender o texto provisório e continuar a captura sem perda;
- medidores limitados a 10 atualizações por segundo.

### 5.3 Perfis por hardware

| Hardware | Durante a reunião | Transcrição final |
|---|---|---|
| 8 GB, CPU básica | Somente captura | `small` ou `medium`, CPU int8 |
| 16 GB, CPU comum | Provisório `small` se benchmark aprovar | `medium`, CPU int8 |
| NVIDIA com 6 GB VRAM | `turbo` provisório | `large-v3`, GPU float16 |
| NVIDIA com 8 GB+ VRAM | `turbo` provisório | `large-v3`, GPU float16 |

Para português do Brasil, `distil-large-v3` não será o perfil de precisão porque o modelo é orientado a inglês. O app deve pedir idioma explícito e aplicar o glossário como `hotwords` quando suportado.

## 6. Arquitetura de software alvo

```text
QML MeetingCapturePage
    -> QmlController / MeetingCaptureViewModel
        -> PrepareMeetingCapture
        -> TestMeetingSignal
        -> StartMeetingCapture
        -> StopMeetingCapture
        -> RecoverMeetingCapture
        -> FinalizeMeetingTranscription
            -> MeetingAudioCapture port
                -> WasapiCaptureProcessAdapter
                    -> voxnote-capture.exe
            -> MeetingSessionRepository port
                -> SQLiteMeetingSessionRepository
            -> TranscriptionEngine port
                -> FasterWhisperEngine
```

Estrutura alvo, criada apenas quando a implementação começar:

```text
native/capture/
├── CMakeLists.txt
├── src/
└── tests/

src/transcritor/
├── application/meeting_capture/
├── domain/meeting_capture/
├── infrastructure/capture/
├── infrastructure/persistence/migrations/
└── qml/
    ├── pages/MeetingCapturePage.qml
    └── components/capture/
```

## 7. Planejamento do frontend

### 7.1 Navegação

Adicionar `Capturar reunião` imediatamente depois de `Nova transcrição`. O item usa ícone Lucide de monitor/áudio, texto no modo expandido e nome acessível no modo compacto.

Ordem final:

1. Nova transcrição
2. Capturar reunião
3. Transcrições
4. Modelos
5. Configurações
6. Ajuda

### 7.2 Tela Preparar captura

Objetivo: deixar a sessão pronta sem exigir conhecimento de dispositivos, codecs ou modelos.

Hierarquia:

1. Título `Capturar reunião` e texto curto de privacidade.
2. Card `Antes de começar`, com confirmação: `Confirmo que tenho autorização para gravar esta reunião.`
3. Seção `Áudio da reunião`, com saída atual, botão `Alterar` e medidor.
4. Seção `Sua voz`, com chave `Incluir meu microfone`, seletor e medidor.
5. Botão secundário `Testar áudio por 5 segundos`.
6. Seção `Transcrição`, com idioma, glossário e modo recomendado.
7. Rodapé de ação com estado de disco e botão primário `Iniciar captura`.

Regras:

- `Iniciar captura` fica desabilitado até consentimento e teste válido da saída;
- microfone é opcional; falha nele não bloqueia a captura da reunião;
- dispositivo padrão aparece como `Saída atual do Windows`, com nome técnico em texto secundário;
- o usuário escolhe entre `Capturar e transcrever ao final — recomendado` e `Acompanhar texto durante a reunião — exige hardware compatível`;
- se o benchmark reprovar o modo provisório, mostrar o motivo e manter o modo recomendado selecionado.

### 7.3 Tela Captura em andamento

Objetivo: provar que o áudio está sendo preservado e permitir encerramento seguro.

Hierarquia:

1. Cabeçalho com ponto vermelho, `Capturando reunião`, duração tabular e ação `Encerrar captura`.
2. Faixa de integridade: `Áudio preservado até 14:32`, espaço livre e último bloco confirmado.
3. Dois cards compactos de trilha: `Reunião` e `Você`, com medidor, dispositivo e estado.
4. Área principal:
   - modo universal: instrução de que a transcrição será gerada ao encerrar;
   - modo provisório: lista de texto com rótulo fixo `Provisório` e atraso atual.
5. Avisos não bloqueantes para fila, Bluetooth ou microfone indisponível.

Não mostrar:

- percentual de uma reunião sem duração conhecida;
- probabilidades de confiança;
- nomes de APIs, modelos, compute type ou VAD;
- botão de pausar que gere falsa expectativa de continuidade do conteúdo da chamada.

### 7.4 Tela Encerramento e recuperação

Etapas visíveis e textuais:

1. `Finalizando os últimos blocos`
2. `Verificando a gravação`
3. `Gerando a transcrição final`
4. `Preparando a revisão`

Durante a inferência final, o progresso usa duração de áudio processada, pois o total já é conhecido. Fechar a janela deve oferecer `Continuar em segundo plano` ou `Parar após salvar o trecho atual`.

Se o app encontrar uma sessão interrompida na abertura:

> Sua reunião foi preservada até 14:32. Você pode continuar a transcrição a partir dos blocos recuperados ou abrir a gravação disponível.

Ações: `Continuar transcrição`, `Abrir pasta da gravação` e `Agora não`.

### 7.5 Tela Concluída

Resumo:

- duração capturada;
- trilhas preservadas;
- perfil final utilizado;
- quantidade de trechos marcados para revisão;
- ação primária `Revisar transcrição`;
- ação secundária `Exportar`;
- detalhes técnicos apenas em área recolhida.

## 8. Estados de interface

| Estado | Tela/comportamento | Ação principal |
|---|---|---|
| `idle` | Formulário inicial | Testar áudio |
| `permission_required` | Consentimento pendente | Confirmar autorização |
| `testing` | Medidores ativos por cinco segundos | Aguardar |
| `ready` | Sinal e disco aprovados | Iniciar captura |
| `capturing` | Duração e blocos confirmados | Encerrar captura |
| `capture_degraded` | Captura principal continua; fonte secundária falhou | Ver orientação |
| `stopping` | Helper fecha o bloco atual | Aguardar |
| `verifying` | Integridade e sequência | Aguardar |
| `transcribing_final` | Progresso por duração | Parar após salvar |
| `recoverable` | Sessão anterior recuperada | Continuar transcrição |
| `completed` | Resumo e revisão | Revisar transcrição |
| `failed` | Explica preservação e próxima ação | Tentar novamente |

Toda transição inválida deve falhar no domínio e gerar mensagem acionável; a página não controlará o ciclo com booleanos independentes.

## 9. Componentes QML

Reutilizar `Theme.qml`, `VxButton`, `VxComboBox`, `VxField` e `NavItem`. Adicionar somente componentes com responsabilidade clara:

| Componente | Responsabilidade |
|---|---|
| `ConsentCard` | Texto legal curto, checkbox e erro de validação |
| `AudioDeviceSelector` | Nome amigável, seletor, estado e ação de teste |
| `SignalMeter` | RMS/pico, estado textual e alternativa para leitor de tela |
| `CaptureModeOption` | Duas opções exclusivas com recomendação e requisitos |
| `RecordingHeader` | Estado, duração e encerramento |
| `TrackStatusCard` | Medidor, dispositivo, último bloco e falha recuperável |
| `IntegrityBanner` | Último tempo preservado, disco e fila |
| `ProvisionalTranscriptView` | Texto instável separado e rotulado |
| `FinalizeProgress` | Etapa atual e progresso por duração |
| `RecoveryCard` | Sessão recuperada e próximas ações |

Não criar um framework visual paralelo. Tokens novos entram em `Theme.qml` e correções compartilhadas entram nos componentes existentes.

## 10. Diagramação e responsividade

- largura mínima do app permanece 980 px;
- conteúdo usa máximo visual de 1180 px, centralizado quando houver espaço;
- padding de página: 28 px em largura compacta e 46 px em largura normal;
- cards: raio 20 px, borda 1 px `Theme.line`, superfície branca e padding interno de 24 a 32 px;
- ritmo vertical: 8, 12, 16, 20, 24 e 32 px; não usar valores isolados;
- controles têm 46 a 52 px de altura e área acionável mínima de 40 px;
- grid de duas colunas somente quando cada coluna mantiver pelo menos 360 px;
- abaixo desse limite, seções empilham sem esconder status ou ação primária;
- texto provisório ocupa espaço flexível e usa virtualização; não renderizar a reunião inteira de uma vez;
- em escala de 200%, o rodapé de ação entra no fluxo rolável e nunca sobrepõe campos;
- duração, atraso, disco e timestamps usam números tabulares.

## 11. Conteúdo final da interface

| Contexto | Texto aprovado |
|---|---|
| Privacidade | `O áudio é capturado e processado neste computador.` |
| Consentimento | `Confirmo que tenho autorização para gravar esta reunião.` |
| Teste | `Testar áudio por 5 segundos` |
| Modo recomendado | `Capturar e transcrever ao final` |
| Modo opcional | `Acompanhar texto durante a reunião` |
| Estado seguro | `Áudio preservado até {duração}` |
| Fila atrasada | `A captura continua normalmente. O texto provisório está {duração} atrasado.` |
| Provisório suspenso | `O texto provisório foi pausado para preservar o desempenho. A gravação continua segura.` |
| Microfone removido | `Seu microfone foi desconectado. O áudio da reunião continua sendo gravado.` |
| Disco baixo | `O espaço disponível está acabando. Encerre a captura para preservar a gravação atual.` |
| Encerrar | `Encerrar captura` |
| Final | `Revisar transcrição` |

## 12. Acessibilidade

- foco visível e ordem: consentimento, dispositivos, teste, opções, ação;
- medidor deve expor também `Sem sinal`, `Sinal baixo`, `Sinal adequado` ou `Sinal alto`;
- estado nunca depende apenas de vermelho, verde ou animação;
- duração deve ter nome acessível completo;
- atualizações frequentes do medidor não entram na região de anúncio do leitor de tela;
- eventos importantes — início, falha, preservação e conclusão — usam região de status moderada;
- `Esc` não encerra captura; o encerramento exige confirmação;
- `Ctrl+Shift+R` pode iniciar somente quando a tela estiver pronta e deve exigir a mesma confirmação visual.

## 13. Plano de implementação

### F9.1 — Prova técnica nativa

- compilar helper C++20 x64;
- enumerar e testar saída/microfone;
- gravar blocos por 60 minutos;
- medir RAM, perdas, drift, Bluetooth e remoção de dispositivo;
- decidir, por evidência, se o helper pode entrar no produto.

Gate: `AC-016` em teste técnico, drift inferior a 250 ms em 60 minutos e nenhuma perda de bloco finalizado.

### F9.2 — Persistência e recuperação

- criar migração e repositórios;
- implementar manifesto, hash, retomada e reconciliação SQLite/disco;
- cobrir encerramento forçado e falta de espaço.

Gate: `AC-017`, `AC-019` e teste de migração de banco 0.1.x.

### F9.3 — Fluxo universal final-only

- integrar helper, orquestração e motor final;
- manter trilhas separadas;
- abrir revisão/exportação existentes.

Gate: uma reunião sintética completa segue de teste de sinal até exportação em CPU sem bloquear a UI.

### F9.4 — Frontend completo

- navegação, preparação, captura, finalização, recuperação e concluída;
- teclado, leitor de tela, 1366x768 e escalas 100% a 200%;
- mensagens de erro e estados degradados.

Gate: checklist visual e de acessibilidade sem ação escondida ou texto cortado.

### F9.5 — Texto provisório opcional

- benchmark local;
- janela deslizante e LocalAgreement-2;
- limite de fila e desligamento automático seguro;
- rastreabilidade provisório/final.

Gate: `AC-018`, ausência de duplicação em bordas e nenhuma interferência na captura.

### F9.6 — Empacotamento e matriz

- incorporar helper e licença ao `onedir` e Inno Setup;
- testar VM limpa, Chrome/Edge, alto-falante, USB e Bluetooth;
- medir WER/CER por trilha e hardware;
- publicar somente após todos os gates aplicáveis.

## 14. Gates quantitativos

| Gate | Limite |
|---|---|
| Sessão técnica | 60 minutos sem crescimento contínuo de RAM |
| Blocos finalizados perdidos | 0 |
| Perda após encerramento forçado | no máximo o bloco aberto, alvo <= 5 s |
| Drift entre trilhas | < 250 ms em 60 minutos |
| Duplicação em borda | 0 no corpus controlado |
| Alucinação em silêncio | 0 no corpus de silêncio aprovado |
| Fila provisória | suspender texto provisório acima de 90 s |
| Atualização de medidor | máximo 10 Hz |
| Precisão final | não pior que importar a mesma captura no pipeline atual |

WER e CER serão medidos separadamente para `Reunião` e `Você`. Nenhuma promessa comercial de precisão será publicada antes da execução do corpus PT-BR documentado.

## 15. Riscos e respostas

| Risco | Resposta planejada |
|---|---|
| Loopback captura notificações | Aviso claro e futura captura por processo quando suportada |
| Bluetooth muda perfil/latência | Evento de dispositivo, trilhas separadas e teste prévio obrigatório |
| CPU não acompanha texto provisório | Suspender provisório; nunca suspender captura |
| Disco enche | Alertas por faixas, fechamento seguro e preservação dos blocos confirmados |
| Helper encerra | Detectar pelo `QProcess`, reconciliar manifesto e oferecer recuperação |
| Silêncio gera texto | VAD conservador, corpus de silêncio e revisão sinalizada |
| Texto final diverge do provisório | Manter execuções separadas e apresentar o final como nova versão |
| Usuário acredita que é integração Meet | Copy sempre descreve captura do áudio do computador |

## 16. Referências técnicas primárias

- Microsoft, WASAPI Loopback Recording: <https://learn.microsoft.com/windows/win32/coreaudio/loopback-recording>
- Microsoft, Application Loopback Audio sample: <https://learn.microsoft.com/samples/microsoft/windows-classic-samples/applicationloopbackaudio-sample/>
- Microsoft, `IMMNotificationClient`: <https://learn.microsoft.com/windows/win32/api/mmdeviceapi/nn-mmdeviceapi-immnotificationclient>
- faster-whisper: <https://github.com/SYSTRAN/faster-whisper>
- Whisper-Streaming / LocalAgreement: <https://aclanthology.org/2023.ijcnlp-demo.3/>
- WhisperX: <https://arxiv.org/abs/2303.00747>
- Careless Whisper: <https://arxiv.org/abs/2402.08021>
