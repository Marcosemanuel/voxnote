# Produto

## 1. Visão

O Voxnote transforma arquivos de áudio longos em texto revisável, totalmente na máquina do usuário. O aplicativo deve esconder a complexidade técnica e conduzir o usuário por um fluxo direto.

## 2. Usuário principal

Pessoa que precisa transcrever entrevistas, reuniões, aulas, gravações profissionais ou materiais extensos, sem configurar ambiente de programação e sem enviar o áudio a um servidor.

## 3. Proposta de valor

- Processamento local e privado.
- Precisão priorizada.
- Funcionamento em máquinas sem GPU.
- Aceleração opcional em GPU NVIDIA.
- Trabalho preservado em áudios longos.
- Revisão humana focada em trechos suspeitos.
- Instalador convencional para Windows x64.

## 4. Princípios do produto

1. O aplicativo sempre deve ter um caminho funcional em CPU.
2. Precisão vem antes de velocidade, mas o hardware deve ser respeitado.
3. O usuário vê nomes compreensíveis, não parâmetros de IA.
4. O progresso deve sobreviver a interrupções.
5. O áudio original é a fonte de verdade.
6. A revisão é parte do produto, não uma exceção.
7. Nenhuma automação pode mascarar incerteza como certeza.

## 5. Fluxo principal

1. Usuário adiciona um ou mais áudios.
2. Aplicativo valida os arquivos.
3. Aplicativo recomenda qualidade conforme o hardware.
4. Usuário confirma idioma e glossário opcional.
5. Aplicativo baixa o modelo necessário, se ausente.
6. Transcrição ocorre sequencialmente com checkpoints.
7. Usuário revisa trechos sinalizados.
8. Usuário exporta TXT, SRT, VTT ou JSON.

## 6. Escopo do MVP

- Windows 10/11 x64.
- Entrada MP3, WAV, M4A, AAC, FLAC, OGG, OPUS, WMA, AIFF/AIF e WEBM.
- CPU obrigatória e NVIDIA opcional.
- Perfis Leve, Equilibrado, Alta precisão e Rápido.
- Modelos baixados sob demanda.
- Fila sequencial.
- Pausa, cancelamento e retomada.
- Checkpoints SQLite.
- Glossário.
- Timestamps por segmento e palavra quando disponíveis.
- Revisão sincronizada com o áudio.
- Texto original e revisado separados.
- Exportações TXT, SRT, VTT e JSON.
- Instalador e releases no GitHub.
- Aviso de nova versão com atualização manual.

## 7. Fora do MVP

- Outros sistemas operacionais ou arquiteturas.
- Microfone e transcrição em tempo real.
- Diarização de locutores.
- Tradução.
- Nuvem ou contas de usuário.
- LLM para reescrever automaticamente a transcrição.
- DOCX e PDF.
- Download ou instalação automática de atualizações.
- Processamento paralelo de múltiplos áudios.

## 8. Métricas do produto

- Taxa de sucesso ao abrir os formatos suportados.
- WER e CER por categoria de áudio.
- Omissões, repetições e alucinações em silêncio.
- Percentual de trabalhos recuperados após interrupção.
- Pico de RAM e VRAM.
- Tempo de processamento por hora de áudio.
- Quantidade de segmentos sinalizados e revisados.
- Falhas de GPU recuperadas por fallback para CPU.
