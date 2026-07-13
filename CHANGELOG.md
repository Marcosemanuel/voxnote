# Changelog

## 0.1.0 - Correções pós-revisão

- Corrigido fallback de CUDA para CPU também durante a inferência.
- Corrigido encerramento cooperativo após cancelamento de uma transcrição.
- Movida a exportação para worker de segundo plano.
- Adicionada verificação SHA-256 e troca atômica para downloads de modelos.
- Removidos diálogos QWidget do fluxo padrão QML.
- Adicionada validação QML por lint ao build.
- Landing passou a apontar para o instalador publicado no GitHub Releases.
- Ícone oficial do Windows passou a incluir frames de 16 a 256 px com transparência.

Todas as mudanças visíveis ao usuário serão registradas aqui.

O formato segue categorias `Adicionado`, `Alterado`, `Corrigido`, `Removido` e `Segurança`.

## Não lançado

### Adicionado

- Aviso de atualização disponível, consultado em segundo plano no GitHub Releases e com abertura manual da página da release.
- Landing pública Voxnote pronta para Vercel, com página de download, cena de gravação em Three.js e adaptação específica para mobile.
- Conjunto de ícones SVG Lucide para áudio, documento, notas, destaque, microfone, menu e busca.
- Identidade visual Voxnote: símbolo, ícone do aplicativo, paleta de marca e nome exibido no aplicativo e instalador.

### Alterado

- Copy da landing revisada para reforçar posicionamento profissional, privacidade por padrão, compatibilidade Windows 10/11 (64 bits) e fluxo de uso.

- O componente QML `VxComboBox` passou a renderizar o próprio menu de opções. O popup não herda mais a paleta escura do controle nativo do Windows: usa superfície branca, texto escuro, borda neutra e destaque azul-claro.
- Interface principal migrada de QWidget/QSS para Qt Quick/QML, preservando os serviços Python e mantendo fallback interno controlado.
- PySide6 atualizado para 6.11.1 e build preparado para empacotar arquivos QML.
- Ícone do executável e do instalador substituído pelo arquivo oficial Voxnote fornecido pelo proprietário.
- Telas Nova transcrição, Transcrições, Modelos, Configurações e Ajuda adotaram o padrão Voxnote de cartões, elevação suave, navegação com ícones e ações visuais padronizadas.
- Formulário de Nova transcrição reorganizado como seção direta, sem cartão redundante; Histórico e Modelos receberam colunas, progresso, estados e ações proporcionais às telas de referência.
- Documentação inicial de produto, requisitos, arquitetura, UX, desenvolvimento, testes, roadmap e governança para agentes de IA.
- Aplicativo desktop PySide6 com fluxo Adicionar, Transcrever, Revisar e Exportar.
- Validação dos dez formatos por conteúdo com PyAV.
- Perfis de qualidade e recomendação automática de hardware.
- Motor faster-whisper com backend CPU e fallback de GPU para CPU.
- Glossário enviado ao motor de transcrição.
- Checkpoints SQLite, pausa, cancelamento e fila sequencial.
- Player de revisão, edição sem sobrescrever o texto original e busca.
- Exportações TXT, SRT, VTT e JSON.
- Build PyInstaller, instalador Inno Setup x64 e CI para Windows.
- Gerenciador de modelos com download, verificação e remoção.
- Ação `Continuar` para trabalhos interrompidos.

### Corrigido

- Atualizações do Voxnote agora renovam o ícone do atalho existente da área de trabalho usando uma cópia versionada do ativo oficial.
- Atalho do Voxnote na área de trabalho passou a referenciar explicitamente o ícone oficial em todas as novas instalações e atualizações.
- Link de download da landing estabilizado: agora usa o ativo permanente `Voxnote-Setup-win64.exe` da Release mais recente, sem depender do número da versão.
- Landing publicada em produção na Vercel com domínio padrão `voxnote-alpha.vercel.app`.

- Botões QML passaram a definir explicitamente as cores de texto e de fundo para os estados normal, hover e pressionado, sem depender da paleta nativa do Windows.
- As opções dos seletores de idioma e qualidade deixaram de usar `ItemDelegate` nativo; cada item agora usa texto `#111111` e superfície branca definidos pelo Voxnote.
- Diagramação da landing reorganizada com gutter único, hierarquia de títulos definida, cards com bordas/raios padronizados e espaçamento responsivo consistente.

- Cena de gravação da landing simplificada: removidos os anéis orbitais e movimentos visuais excessivos; barras, base e onda agora têm leitura clara.
- Onda decorativa da landing ajustada para 30 fps, cadência moderada, interação suavizada e densidade responsiva em telas pequenas.
- Contraste e amplitude da onda aumentados para melhorar a leitura contra o fundo claro, mantendo o custo de renderização limitado.
- Tipografia padronizada em Manrope, usando somente os pesos 400, 500, 600 e 700; a fonte é embutida no executável para funcionar offline.
- Escala de títulos, corpo, botões, inputs, labels, tabelas e transcrições ajustada; durações e timestamps agora usam números tabulares.
- Migração de bancos criados antes do campo de glossário.
- Retomada agora inicia no último timestamp confirmado.
- Checkpoints não sobrescrevem revisões humanas.
- Cancelamento não é mais apresentado como conclusão.
- Fila aguarda a thread finalizar antes de iniciar o próximo trabalho.
- Fechamento durante transcrição ocorre de forma cooperativa.
- Trabalhos ativos não podem ser excluídos.
- Recomendação de alta precisão considera VRAM e compatibilidade CUDA.
- Páginas de Configurações e Ajuda agora mantêm fundo claro e texto legível.
- Lista vazia da nova transcrição não ocupa mais área visual nem usa superfície escura.
- Redesign completo: sistema de cores, tipografia, navegação, formulários, tabelas, cartões, estados vazios e ações padronizados.
- Ícones raster de ações recortados no carregamento para eliminar margem interna e preservar o tamanho visual correto em botões de tabela.
