# Roadmap

O roadmap controla sequência e escopo. Um agente não deve iniciar uma fase futura sem concluir dependências ou receber instrução explícita.

## Fase 0 — Fundação documental

Estado: concluída

- Regras para agentes.
- Produto e escopo.
- Requisitos e aceite.
- Arquitetura.
- UX.
- Desenvolvimento e testes.
- Estado e decisões.

## Fase 1 — Fundação executável

Estado: concluída

- Criar projeto Python 3.12.
- Configurar `pyproject.toml` e lock de dependências.
- Estrutura de camadas.
- Logging e diretórios Windows.
- SQLite e migrações.
- Shell PySide6 Qt Quick/QML com navegação; Widgets preservados temporariamente como fallback de validação.
- CI com lint, tipos e testes.

Saída: aplicativo abre em Windows x64, navega e persiste configurações.

## Fase 2 — Entrada e diagnóstico

Estado: concluída

- Seleção e drag-and-drop.
- Validação PyAV.
- Metadados.
- Diagnóstico de CPU, RAM, disco e NVIDIA.
- Seleção automática de perfil.

Saída: usuário adiciona arquivos válidos e recebe recomendação verificável.

## Fase 3 — Modelos e motor

Estado: funcional, validação ampla pendente

- Gerenciador de modelos.
- Download retomável e hash.
- Backend CPU.
- Backend NVIDIA opcional.
- Teste real e fallback.
- Transcrição curta end-to-end.

Saída: um áudio curto é transcrito localmente em CPU e, quando disponível, GPU.

## Fase 4 — Áudio longo e recuperação

Estado: funcional, teste de áudio longo pendente

- Jobs e estados.
- Fila sequencial.
- VAD conservador.
- Checkpoints.
- Pausa, cancelamento e retomada.
- Progresso e estimativas.
- Controle de memória.

Saída: áudio longo sobrevive a interrupção e retoma corretamente.

## Fase 5 — Revisão

Estado: concluída para revisão básica

- Player sincronizado.
- Segmentos e timestamps.
- Texto original e revisado.
- Sinalização de trechos.
- Busca, substituição e atalhos.

Saída: usuário revisa eficientemente sem perder o reconhecimento original.

## Fase 6 — Exportação e histórico

Estado: concluída para exportação e histórico básicos

- TXT, SRT, VTT e JSON.
- Histórico, busca e filtros.
- Ações sobre projetos.
- Diagnóstico sanitizado.

Saída: transcrição revisada é exportada e reaberta.

## Fase 7 — Instalador e release

Estado: concluída localmente

- PyInstaller `onedir`.
- Inno Setup x64.
- GitHub Actions Windows.
- GitHub Release e checksum.
- Aviso de versão disponível pelo GitHub Releases, sem download automático.
- Licenças de terceiros.
- Testes em VM limpa.

Saída: instalador público reproduzível para Windows x64.

## Fase 8 — Landing pública de download

Estado: funcional localmente, publicação pendente

- Landing curta em React/Vite pronta para Vercel.
- Onda Canvas 2D decorativa de gravação e comportamento adaptado para mobile.
- Download configurável para GitHub Releases.

Saída: página Vercel publicada apontando para o instalador de uma release pública.

## Pós-MVP não aprovado para implementação

- Diarização.
- Microfone/tempo real.
- Tradução.
- DOCX/PDF.
- Atualização automática.
- Projeto portátil.
