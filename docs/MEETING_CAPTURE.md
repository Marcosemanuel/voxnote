# Captura local de reuniões

## Implementação atual (2026-07-13)

A primeira entrega funcional está integrada ao aplicativo em `Capturar reunião`:

- PyAudioWPatch enumera dispositivos WASAPI loopback e microfones no Windows.
- O usuário confirma autorização, escolhe a saída, pode incluir microfone e executa teste de sinal.
- Cada trilha é gravada em blocos WAV de cinco segundos com arquivo parcial, fsync, troca atômica, SHA-256 e journal NDJSON.
- Blocos já confirmados são registrados no SQLite. Ao iniciar novamente, sessões interrompidas ou falhas recuperam os blocos presentes no journal.
- Ao encerrar, a transcrição final usa janelas temporárias limitadas; não é criado WAV único da reunião nem há transcrição provisória apresentada como final.
- Revisão preserva reconhecimento e texto humano em campos separados; TXT, SRT, VTT e JSON são exportados em worker.
- Uma sessão com blocos confirmados pode ser transcrita novamente pelo histórico; cada tentativa cria uma execução final independente e não altera revisões anteriores.
- As duas trilhas mantêm timestamps do mesmo relógio QPC. O serviço mede a variação relativa por bloco e avisa quando superar 250 ms, sem misturar ou modificar o áudio de origem.

Validações ainda pendentes: captura contínua de 60 minutos, medição real de drift entre trilhas, remoção de dispositivo/Bluetooth e falta de espaço. O monitoramento de drift é implementado, mas ainda não substitui a medição prolongada em hardware real.

## Estado

Primeira entrega funcional implementada localmente. A prova de estabilidade de 60 minutos e a matriz de dispositivos permanecem pendentes.

## Objetivo

Permitir que o usuário capture manualmente o áudio de uma reunião em execução no Windows e gere uma transcrição local revisável. O caso de uso inicial é o Google Meet, mas a captura não depende de automação, extensão ou scraping do Meet.

## Escopo da primeira entrega

1. Usuário abre `Capturar reunião` e confirma que possui autorização para gravar.
2. Usuário seleciona a saída de áudio do Windows e, opcionalmente, o microfone local.
3. O app executa teste de sinal e mostra medidores separados antes da gravação.
4. A gravação começa apenas por ação explícita do usuário.
5. Áudio é persistido em segmentos recuperáveis no disco; nunca integralmente na memória.
6. No modo universal, a transcrição começa após o encerramento e usa os blocos confirmados.
7. Quando o benchmark habilitar acompanhamento durante a chamada, o texto será rotulado como `provisório` e poderá ser suspenso sem interromper a captura.
8. Ao encerrar, o app executa o reconhecimento final com o perfil de maior precisão suportado pela máquina.
9. O reconhecimento final segue o fluxo existente de revisão e exportação.

## Fora da primeira entrega

- Captura automática ao detectar Google Meet.
- Extensão Chrome/Edge, scraping de legendas ou automação do navegador.
- Integração OAuth com Google Meet/Drive.
- Identificação automática de participantes ou diarização.
- Garantia de transcrição instantânea ou perfeita durante a chamada.
- Captura em segundo plano sem indicador visível e sem consentimento.

## Arquitetura proposta

```text
UI QML
  -> MeetingCaptureController
    -> CaptureSession (estado, consentimento, dispositivos)
      -> Windows audio adapter (WASAPI loopback + microfone opcional)
        -> segment writer no disco
          -> transcription queue existente
            -> SQLite checkpoints e segmentos
              -> revisão e exportação existentes
```

- A implementação Windows deve usar uma camada nativa isolada atrás de um port de captura; WASAPI loopback é o candidato inicial para a prova técnica.
- A saída do Windows e o microfone devem ser arquivos/streams de origem separados até a etapa de sincronização.
- Se a inferência ficar mais lenta que a captura, a sessão mantém os blocos no disco, informa a fila pendente e não descarta fala.
- O reprocessamento final cria uma nova versão de reconhecimento automático; nunca sobrescreve texto revisado pelo usuário.

## Critérios de saída da prova técnica

1. Capturar 60 minutos de áudio de sistema sem crescimento contínuo de RAM.
2. Capturar microfone e saída com início/fim alinhados dentro de 250 ms no material de teste.
3. Preservar blocos confirmados após encerramento forçado.
4. Continuar a gravação quando a transcrição estiver atrasada.
5. Testar saída por alto-falante, headset USB e Bluetooth em Chrome e Edge.
6. Exibir erro acionável para dispositivo removido, ausência de permissão, falta de espaço e falha do adaptador.

## Riscos ativos

- Loopback de saída captura o mix do sistema, inclusive notificações e outros aplicativos.
- Bluetooth pode introduzir latência e mudar de perfil de áudio durante a chamada.
- Em CPU comum, a transcrição provisória pode acumular fila; a precisão é garantida pela etapa final de reprocessamento, não pela visualização durante a chamada.
- A gravação de reuniões exige consentimento e conformidade com as políticas da organização e da jurisdição aplicável.

A stack, o frontend, os estados, os componentes e os gates quantitativos estão detalhados em `docs/MEETING_CAPTURE_STACK_FRONTEND.md`.
