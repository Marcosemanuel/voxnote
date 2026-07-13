# AGENTS.md — Regras obrigatórias do projeto

Este arquivo governa todo agente de IA que analise, planeje, implemente, teste, revise ou publique este projeto.

## 1. Objetivo imutável

Construir um aplicativo desktop local, simples e confiável para transcrição de áudios longos, exclusivo para Windows 10/11 x64, distribuído por instalador no GitHub. A prioridade é precisão, preservação do trabalho, compatibilidade com a maioria das máquinas e revisão humana assistida.

O fluxo principal do usuário é:

`Adicionar áudio -> Transcrever -> Revisar -> Exportar`

## 2. Ordem obrigatória de leitura

Antes de propor ou executar qualquer alteração, leia integralmente:

1. `AGENTS.md`
2. `docs/PRODUCT.md`
3. `docs/REQUIREMENTS.md`
4. `docs/ARCHITECTURE.md`
5. `docs/UX.md` quando a tarefa afetar interface ou fluxo
6. `docs/DEVELOPMENT.md`
7. `docs/TESTING.md`
8. `docs/ROADMAP.md`
9. `docs/STATUS.md`
10. `docs/DECISIONS.md`

Leia também arquivos `AGENTS.md` mais específicos caso sejam criados dentro de subdiretórios.

## 3. Regras inegociáveis

- Seja pragmático, objetivo, concreto e didático.
- Não crie funcionalidades não solicitadas ou fora do roadmap aprovado.
- Não implemente antes de entender os requisitos e contratos afetados.
- Não declare conclusão sem executar verificações proporcionais ao risco.
- Não esconda falhas, testes não executados, limitações ou comportamento não comprovado.
- Não altere silenciosamente decisões registradas.
- Preserve alterações existentes que não pertençam à tarefa.
- Nunca apague dados, projetos, modelos ou arquivos do usuário sem confirmação explícita.
- O aplicativo deve funcionar em CPU mesmo sem CUDA, driver NVIDIA ou internet.
- Falhas de GPU devem resultar em fallback seguro para CPU, não em encerramento do aplicativo.
- Inferência e I/O pesado nunca podem bloquear a thread da interface.
- Transcrições longas devem usar checkpoints recuperáveis.
- O áudio original é a fonte de verdade e não deve ser modificado.
- Texto reconhecido e texto revisado devem ser preservados separadamente.
- Não exiba percentuais de confiança como se fossem probabilidade absoluta de correção.
- Não use LLM para alterar silenciosamente o conteúdo reconhecido.
- Não inclua suporte a Linux, macOS, Windows ARM ou Windows 32 bits.

## 4. Fonte de verdade

Em caso de divergência, siga esta prioridade:

1. Pedido explícito atual do proprietário do projeto
2. `AGENTS.md`
3. `docs/DECISIONS.md`
4. `docs/REQUIREMENTS.md`
5. `docs/ARCHITECTURE.md`
6. `docs/UX.md`
7. `docs/ROADMAP.md`
8. Código e testes existentes

Se código e documentação divergirem, não escolha silenciosamente. Identifique a divergência, determine o comportamento aprovado e atualize ambos na mesma tarefa.

## 5. Protocolo obrigatório para toda alteração

### Antes de editar

1. Leia os documentos aplicáveis.
2. Inspecione o estado real do repositório.
3. Declare o objetivo e o limite da tarefa.
4. Identifique requisitos e critérios de aceite afetados.
5. Verifique mudanças locais para não sobrescrever trabalho alheio.

### Durante a edição

1. Faça a menor alteração completa que resolva o objetivo.
2. Mantenha UI, domínio, infraestrutura e persistência desacoplados.
3. Adicione ou ajuste testes junto com o comportamento.
4. Use mensagens de erro que expliquem o problema, a preservação do progresso e a próxima ação.
5. Atualize a documentação no mesmo conjunto de alterações.

### Antes de concluir

1. Execute os testes aplicáveis.
2. Execute lint e análise de tipos quando disponíveis.
3. Verifique manualmente o fluxo afetado quando houver interface.
4. Atualize `docs/STATUS.md`.
5. Atualize `docs/ROADMAP.md` se o estado de uma etapa mudou.
6. Atualize `docs/DECISIONS.md` se houve decisão arquitetural ou mudança de contrato.
7. Atualize `CHANGELOG.md` para mudança visível ao usuário.
8. Informe exatamente o que foi verificado e o que não foi.

Uma tarefa não está concluída se a documentação correspondente estiver desatualizada.

## 6. Controle de escopo

O MVP está definido em `docs/REQUIREMENTS.md`. Qualquer item não listado como requisito aprovado deve ser tratado como fora de escopo.

Para adicionar uma nova funcionalidade:

1. Registrar a necessidade.
2. Definir requisito verificável.
3. Avaliar impacto em arquitetura, UX, armazenamento, instalador e testes.
4. Obter aprovação do proprietário.
5. Atualizar documentação antes ou junto da implementação.

## 7. Identificadores e rastreabilidade

- Requisitos funcionais: `FR-###`
- Requisitos não funcionais: `NFR-###`
- Critérios de aceite: `AC-###`
- Decisões arquiteturais: `ADR-###`
- Riscos: `RISK-###`

Commits, PRs, planos e relatórios devem citar os identificadores afetados quando existirem.

## 8. Definição de pronto

Uma alteração só está pronta quando:

- O comportamento solicitado foi implementado integralmente.
- Os critérios de aceite afetados foram satisfeitos.
- Casos de erro e recuperação foram tratados.
- Testes relevantes passaram.
- A interface permaneceu responsiva, quando aplicável.
- Não houve regressão conhecida omitida.
- A documentação foi atualizada.
- `docs/STATUS.md` representa o estado real.
- Limitações restantes foram registradas de forma explícita.

## 9. Proibições técnicas

- Não usar operações longas na thread principal do Qt.
- Não executar várias inferências pesadas simultaneamente.
- Não carregar o áudio inteiro na memória sem justificativa e teste.
- Não gerar WAV integral intermediário para arquivos longos.
- Não manter transação SQLite aberta durante inferência.
- Não depender da extensão para validar áudio.
- Não exigir instalação manual de Python, FFmpeg, CUDA Toolkit ou cuDNN.
- Não armazenar modelos grandes no Git.
- Não registrar conteúdo integral da transcrição nos logs por padrão.
- Não usar `HIGH_PRIORITY_CLASS` no Windows.
- Não apagar o áudio original ao excluir uma transcrição.

## 10. Comunicação final do agente

Toda entrega deve informar, de forma curta e concreta:

- Resultado produzido.
- Arquivos principais alterados.
- Testes e verificações executados.
- Documentação atualizada.
- Limitações ou pendências reais.

