# Estado real do projeto

Última atualização: 2026-07-13

## Resumo

A versão `0.2.0` está em preparação para Windows x64. Ela inclui a captura local recuperável de reuniões; a publicação do instalador e a validação prolongada de dispositivos ainda estão pendentes. O fluxo disponível é
selecionar e validar áudios, configurar idioma/qualidade/glossário, transcrever localmente,
acompanhar progresso, preservar checkpoints, revisar segmentos e exportar TXT, SRT, VTT ou JSON.

## Concluído

- Escopo Windows 10/11 x64 definido.
- Stack principal definida.
- MVP e exclusões definidos.
- Requisitos e critérios de aceite identificados.
- Fluxo de frontend definido.
- Protocolo de trabalho para agentes definido.
- Roadmap inicial definido.
- Aplicação PySide6 executável com navegação e estados principais.
- Validação de áudio por conteúdo com PyAV.
- Diagnóstico de CPU, RAM e NVIDIA.
- faster-whisper/CTranslate2 com CPU e tentativa de CUDA com fallback.
- SQLite/WAL com jobs, segmentos, texto original e revisado.
- Pausa e cancelamento cooperativos.
- Histórico, revisão sincronizada e exportadores.
- Vinte e cinco testes automatizados passando.
- Ruff, formatação e mypy passando.
- Build PyInstaller `onedir` gerado e iniciado com sucesso.
- Instalador Inno Setup x64 gerado, instalado, iniciado e desinstalado com sucesso.
- CI Windows x64 configurada.
- Migração versionada para bancos existentes.
- Retomada pelo último timestamp confirmado.
- Checkpoint preservando revisão humana.
- Cancelamento separado de conclusão.
- Fechamento cooperativo aguardando worker.
- Recomendação de GPU considerando VRAM e compatibilidade CUDA.
- Gerenciador funcional para baixar, verificar e remover modelos.
- Correção visual das páginas informativas: superfície branca e texto legível, independente da paleta do Qt.
- Lista de arquivos vazia removida da tela inicial; ela aparece somente após uma seleção válida.
- Redesign completo aplicado e comparado à direção visual selecionada; consulte `design-qa.md`.
- Manrope incorporada ao pacote, com tokens tipográficos aplicados a telas, formulários, tabelas, transcrições e timestamps.
- Identidade Voxnote aplicada: símbolo na navegação, paleta oficial, ícone do executável e nome da marca no aplicativo e instalador.
- Ícone Voxnote atualizado com o ativo oficial final fornecido pelo proprietário.
- Ícone Windows regenerado a partir do ativo oficial, com transparência e frames de 16, 20, 24, 32, 40, 48, 64, 128 e 256 px.
- Aviso de atualização disponível: consulta em segundo plano a release pública do GitHub e direciona manualmente para a página da versão, sem baixar ou instalar nada.
- Link público da landing estabilizado em `releases/latest/download/Voxnote-Setup-win64.exe`; a versão `0.1.1` foi publicada com esse ativo e a URL responde com o instalador.
- Atalho existente `Voxnote.lnk` atualizado para o `.ico` oficial instalado; novas instalações e atualizações usarão a mesma referência explícita.
- Atualizações agora usam uma cópia versionada do ícone oficial e regravam o atalho Voxnote existente, evitando cache visual antigo na área de trabalho.
- CI Windows corrigida para criar `.venv` e executar testes, qualidade e build no mesmo ambiente isolado.
- Padrão estético Voxnote aplicado às telas principais, com SVGs Lucide e superfícies elevadas consistentes.
- Conjunto vetorial Lucide aplicado à navegação, upload, busca e itens de histórico; mantém traço consistente de 2px e azul apenas nos destaques.
- Padrão das telas de nova transcrição, histórico e modelos consolidado: formulário sem cartão redundante, tabelas elevadas, progresso visual e ações coerentes.
- Shell Qt Quick/QML implementado como interface padrão, com navegação responsiva, componentes Voxnote reutilizáveis e ponte para arquivos, histórico, modelos, processamento, revisão e exportação.
- PySide6 atualizado para 6.11.1; UI QWidget mantida temporariamente por flag interna para rollback controlado.
- Landing pública criada em `landing/`, com hero Canvas 2D de baixa frequência, três seções objetivas e responsividade específica para mobile. A onda limita renderização a 30 fps e reduz densidade em telas pequenas.
- Onda da landing ajustada com largura total, amplitude e contraste reforçados contra o fundo claro, mantendo interação de ponteiro suave.

- Diagramação da landing consolidada com tokens de margem, superfícies, bordas e ritmo vertical; recursos e passos usam cartões padronizados no desktop e no mobile.
- Copy da landing revisada para posicionamento profissional, privacidade por padrão e fluxo explícito do áudio à exportação.
- Estrutura de publicação do repositório preparada com README, contribuição, segurança, templates GitHub, CI da landing e exclusão de artefatos locais.

Landing publicada em produção na Vercel: https://voxnote-alpha.vercel.app/ (HTTP 200 verificado).

## Em andamento

- Captura local de reuniões aprovada para pós-MVP: requisitos `FR-060` a `FR-067`, critérios `AC-016` a `AC-020` e ADR-017 registrados.
- Stack técnica, armazenamento, IPC, pipeline, frontend, estados, componentes e gates da Fase 9 definidos em `docs/MEETING_CAPTURE_STACK_FRONTEND.md`.
- Captura local de reuniões implementada como primeira entrega funcional: PyAudioWPatch/WASAPI grava a saída do Windows e o microfone opcional em blocos WAV separados, com journal fsync, SQLite e recuperação no próximo início.
- Fluxo QML de Capturar reunião implementado: confirmação de autorização, dispositivos, teste de sinal, captura, finalização, transcrição final, revisão e exportação.
- Aba de gravações de reuniões padronizada com os componentes reutilizáveis Voxnote para seleção, consentimento, medidores, edição, estados e ações.
- Smoke test real em 2026-07-13: loopback padrão WASAPI abriu, gravou um WAV estéreo de 48 kHz com 54.272 frames e emitiu `block_committed`; nenhum `fatal_error` ocorreu.
- Build PyInstaller `onedir` e instalador Inno Setup `0.2.0` concluídos com PyAudioWPatch; instalação local criou o atalho `Voxnote.lnk` apontando para o ícone oficial versionado. Prova de 60 minutos e matriz de dispositivos permanecem pendentes.
- Sessões de reunião com blocos persistidos podem ser transcritas ou reprocessadas pelo histórico; recuperação inclui estado `failed` e cria nova execução sem sobrescrever revisão anterior.
- Fluxo QML de captura teve textos UTF-8 e rótulos de perfis corrigidos; `Alta precisão` e `Rápida` agora correspondem ao perfil recomendado do backend.
- Timestamps de trilhas usam QPC comum e há monitor de variação por bloco com alerta acima de 250 ms. A medição em chamada longa e dispositivos reais ainda não foi concluída.
- Verificação pós-correção em 2026-07-13: 39 testes, Ruff, mypy e lint QML aprovados; PyInstaller `onedir` foi reconstruído e `TranscritorLocal.exe` permaneceu responsivo no smoke test.

- Verificação visual concluída para o menu aberto de idioma/qualidade: os itens mantêm contraste legível em superfície clara, sem herdar o tema escuro nativo do Windows.
- Seletores de idioma e qualidade usam itens QML próprios com cores explícitas; não há mais dependência do `ItemDelegate` nativo do Windows.
- Fallback CUDA cobre criação do modelo e inferência; falhas durante a transcrição retomam em CPU usando os checkpoints já persistidos.
- Exportação ocorre em worker, sem bloquear a interface em transcrições longas.
- Download de modelo usa diretório temporário, troca atômica e manifesto SHA-256; arquivos adulterados ou incompletos não são usados.
- Diálogos do fluxo QML são renderizados pelo design system Voxnote; o controlador não usa mais diálogos QWidget.
- Fechamento durante transcrição cancela cooperativamente e encerra o aplicativo depois que o worker termina.
- Build valida lint de todos os arquivos QML; a formatação é aplicada com `pyside6-qmlformat -i` antes da validação.
- Validação ampliada com corpus real, áudios longos e diferentes GPUs.
- Matriz ampliada de QA do shell QML em 100%, 125%, 150% e 200% ainda em execução; captura base de 1280x820 aprovada visualmente.
- Publicação da landing na Vercel, dependente do repositório remoto e da URL definitiva do instalador no GitHub Releases.

## Próximo passo aprovado

Executar captura de 60 minutos em saída USB/Bluetooth e microfone, medir blocos perdidos, RAM, drift e recuperação. Depois, gerar e instalar o pacote Windows contendo PyAudioWPatch. Em paralelo, permanece pendente a matriz do MVP com os dez formatos, áudio longo e perfis de hardware.

## Ainda não comprovado

- Compatibilidade real dos dez formatos no pacote final; a validação e os filtros estão implementados.
- Desempenho de modelos por perfil de hardware.
- Download e transcrição end-to-end de cada modelo no pacote instalado.
- Distribuição opcional das dependências NVIDIA.
- Recuperação de áudio longo em material real; a lógica de retomada está coberta por teste automatizado.
- Métricas de precisão.
- Instalador em VM limpa; o teste local isolado passou.

## Evidências locais da versão 0.2.0

- `pytest`: 39 testes aprovados.
- `ruff check`: aprovado.
- `ruff format --check`: aprovado.
- `mypy`: aprovado.
- Executável empacotado: iniciado e permaneceu ativo no smoke test.
- Pacote `onedir`: gerado em 2026-07-13 após as correções pós-revisão.
- Instalador: 182,6 MB.
- SHA-256: `6C049E604DFC3DD0809DD53D985999D28EAA4D1652256ED10105603A88B00BA2`.
- Instalação silenciosa: código 0.
- Inicialização após instalação: aprovada.
- Desinstalação silenciosa: código 0 e pasta do programa removida.

## Riscos ativos

- `RISK-001` Compatibilidade das DLLs CUDA/cuDNN no pacote Windows.
- `RISK-002` Tamanho e confiabilidade do instalador com dependências nativas.
- `RISK-003` Desempenho de `large-v3` em CPU comum.
- `RISK-004` Cortes de VAD removerem fala baixa.
- `RISK-005` Antivírus/SmartScreen sinalizarem executável não assinado.
- `RISK-006` Métricas do Whisper serem interpretadas incorretamente como confiança absoluta.
- `RISK-007` Loopback da saída do Windows capturar sons de outros aplicativos durante uma reunião.
- `RISK-008` Troca, remoção ou latência de dispositivos Bluetooth afetar sincronização de captura.

## Regra de atualização

Todo agente que modificar comportamento, arquitetura, testes, roadmap ou build deve atualizar este arquivo com a data e o estado real. Não registrar como concluído algo que não foi verificado.
