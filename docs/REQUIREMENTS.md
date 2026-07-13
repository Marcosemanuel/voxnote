# Requisitos e critérios de aceite

## 1. Requisitos funcionais

### Entrada e validação

- `FR-001` Selecionar um ou vários arquivos pelo seletor do Windows.
- `FR-002` Receber arquivos por arrastar e soltar.
- `FR-003` Aceitar MP3, WAV, M4A, AAC, FLAC, OGG, OPUS, WMA, AIFF/AIF e WEBM.
- `FR-004` Validar conteúdo real do arquivo, faixa de áudio, duração e capacidade de decodificação.
- `FR-005` Mostrar nome, formato, tamanho e duração antes de iniciar.

### Hardware e modelos

- `FR-010` Detectar Windows, CPU, threads, RAM, disco e GPU NVIDIA.
- `FR-011` Testar o backend GPU por inicialização real antes de ativá-lo.
- `FR-012` Retornar automaticamente para CPU quando GPU falhar.
- `FR-013` Recomendar perfil de qualidade conforme hardware.
- `FR-014` Baixar, retomar, verificar e remover modelos.
- `FR-015` Impedir ativação de modelo incompleto ou inválido.

### Transcrição

- `FR-020` Transcrever localmente com faster-whisper/CTranslate2.
- `FR-021` Usar idioma explícito ou detecção automática.
- `FR-022` Aceitar glossário por projeto.
- `FR-023` Processar fila sequencialmente.
- `FR-024` Mostrar progresso por duração processada.
- `FR-025` Permitir pausa cooperativa.
- `FR-026` Permitir cancelamento preservando resultados concluídos.
- `FR-027` Retomar do último checkpoint válido.
- `FR-028` Salvar parâmetros e versão do motor usados no trabalho.

### Revisão

- `FR-030` Exibir segmentos com início, fim e texto.
- `FR-031` Reproduzir o áudio a partir de um segmento.
- `FR-032` Editar texto com salvamento automático.
- `FR-033` Preservar reconhecimento original e texto revisado separadamente.
- `FR-034` Sinalizar segmentos potencialmente problemáticos sem apresentar confiança absoluta.
- `FR-035` Buscar e substituir texto.
- `FR-036` Marcar segmentos como revisados.

### Exportação e histórico

- `FR-040` Exportar TXT.
- `FR-041` Exportar SRT.
- `FR-042` Exportar VTT.
- `FR-043` Exportar JSON com metadados e timestamps.
- `FR-044` Listar, buscar, abrir, continuar e excluir transcrições.
- `FR-045` Excluir transcrição sem excluir o áudio original.

### Diagnóstico

- `FR-050` Registrar versão, hardware, backend, modelo, parâmetros, duração, tempo e erros.
- `FR-051` Gerar pacote de diagnóstico sem texto integral por padrão.
- `FR-052` Mostrar mensagens que expliquem problema, estado do progresso e próxima ação.

## 2. Requisitos não funcionais

- `NFR-UI-001` A interface deve usar Manrope incorporada ao pacote, sem depender de fonte instalada ou internet.
- `NFR-UI-002` A tipografia deve usar somente os pesos 400, 500, 600 e 700; corpo e campos devem manter 16px como padrão.
- `NFR-UI-003` Durações, percentuais e timestamps devem usar números tabulares para manter o alinhamento visual.
- `NFR-UI-004` A aplicação deve exibir a identidade Voxnote: símbolo oficial, nome da marca e paleta `#111111`, `#2B2B2B`, `#D9D9D6`, `#F5F5F3` e `#3B82F6`.
- `NFR-UI-005` O executável e o instalador devem usar o ícone Voxnote sem alterar os diretórios de dados já existentes do usuário.
- `NFR-UI-006` As telas principais devem adotar o padrão visual Voxnote de cartões elevados, navegação com ícones de contorno e azul reservado a destaque, foco e ação primária.
- `NFR-UI-007` A camada visual deve usar componentes QML reutilizáveis e layouts responsivos; nenhuma página pode depender da soma de larguras fixas para permanecer utilizável.
- `NFR-WEB-001` A landing pública deve apresentar o produto em três seções — o que é, o que faz e como utilizar — e conduzir exclusivamente ao instalador Windows x64 publicado no GitHub Releases.
- `NFR-WEB-002` A landing deve funcionar em viewport móvel de 390px sem corte, sobreposição ou controles menores que a área de toque prevista; a animação decorativa deve respeitar `prefers-reduced-motion`.

- `NFR-001` Suportar apenas Windows 10 1809+ x64 e Windows 11 x64.
- `NFR-002` Funcionar sem Python instalado.
- `NFR-003` Funcionar em CPU sem CUDA instalado.
- `NFR-004` Não exigir instalação manual de dependências técnicas.
- `NFR-005` Não bloquear a thread da interface durante operações longas.
- `NFR-006` Não carregar áudios longos integralmente em memória.
- `NFR-007` Preservar checkpoints confirmados após encerramento forçado.
- `NFR-008` Processar dados localmente depois do download do modelo.
- `NFR-009` Não registrar conteúdo sensível integral nos logs por padrão.
- `NFR-010` Ser utilizável em 1366x768 e escalas do Windows de 100% a 200%.
- `NFR-011` Permitir navegação por teclado e foco visível.
- `NFR-012` Manter uso de CPU configurável e não usar prioridade alta.
- `NFR-013` Modelos não podem ser versionados no Git.
- `NFR-014` Builds reproduzíveis devem usar dependências fixadas.

## 3. Critérios de aceite do MVP

- `AC-001` Instalação limpa em Windows x64 sem Python e inicialização bem-sucedida.
- `AC-002` Inicialização e transcrição por CPU em máquina sem CUDA.
- `AC-003` Falha simulada de CUDA produz fallback para CPU e mensagem compreensível.
- `AC-004` Uma amostra válida de cada formato suportado é aberta e transcrita.
- `AC-005` Arquivo inválido, corrompido ou sem áudio apresenta erro acionável.
- `AC-006` Trabalho interrompido após checkpoint pode ser retomado sem perder segmentos confirmados.
- `AC-007` Áudio de oito horas não provoca crescimento contínuo de memória.
- `AC-008` Interface permanece responsiva durante transcrição, download e exportação.
- `AC-009` Pausa conclui o trecho atual e preserva o estado.
- `AC-010` Cancelamento não apaga resultado parcial nem áudio original.
- `AC-011` Edição preserva o texto reconhecido original.
- `AC-012` TXT, SRT, VTT e JSON são exportados em ordem cronológica e reabertos por ferramentas de referência.
- `AC-013` Desinstalação não apaga dados do usuário sem escolha explícita.
- `AC-014` Testes, documentação, instalador e checksum acompanham a release.

## 4. Requisitos de hardware comunicados ao usuário

Mínimo:

- CPU Intel/AMD x64 com quatro threads.
- 8 GB de RAM.
- 8 GB livres.
- GPU não obrigatória.

Recomendado:

- CPU com seis núcleos e doze threads.
- 16 GB de RAM.
- SSD com 15 GB livres.
- NVIDIA com 6 GB ou mais de VRAM para aceleração.
