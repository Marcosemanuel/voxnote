# Desenvolvimento por agentes

## 1. Fluxo de trabalho

Para cada tarefa:

1. Ler `AGENTS.md` e documentos aplicáveis.
2. Inspecionar repositório e `git status`.
3. Relacionar a tarefa a requisitos e critérios de aceite.
4. Planejar a menor entrega vertical verificável.
5. Implementar código e testes.
6. Executar verificações.
7. Atualizar documentação, estado, roadmap e decisões.
8. Relatar evidências.

## 2. Entrega vertical

Prefira implementar um fluxo completo pequeno, por exemplo:

`selecionar arquivo -> validar -> apresentar resultado`

Evite criar todas as classes ou telas vazias antes de haver comportamento verificável.

## 3. Convenções

- Código, identificadores e nomes de arquivo em inglês.
- Interface, ajuda e mensagens ao usuário em português brasileiro.
- Type hints obrigatórios em código novo.
- `pathlib.Path` para caminhos.
- `logging` estruturado; não usar `print` em produção.
- Erros de domínio próprios; não expor stack trace na UI.
- Dependências externas atrás de ports/adapters quando relevante.
- Funções pequenas e com responsabilidade única.
- Evitar singletons globais e estado mutável compartilhado.

## 4. Dependências

Antes de adicionar uma dependência:

1. Demonstrar necessidade.
2. Verificar manutenção, licença, tamanho e impacto no instalador.
3. Preferir biblioteca já aprovada.
4. Fixar versão.
5. Registrar licença.
6. Atualizar arquitetura se houver impacto estrutural.

## 5. Banco de dados

- Toda mudança de schema exige migração.
- Nunca editar banco do usuário diretamente sem migração.
- Migração deve ser idempotente no controle de versão e testada em banco anterior.
- Fazer backup antes de migração destrutiva.
- Não abrir transação durante inferência.

## 6. Threading e workers

- Qt main thread apenas para UI.
- Workers comunicam por signals/slots ou filas controladas.
- Cancelamento por token/evento cooperativo.
- Worker deve emitir progresso, conclusão e falha tipada.
- Recursos devem ser liberados em sucesso, erro e cancelamento.

## 7. Erros

Cada erro precisa ter:

- Código estável para diagnóstico.
- Mensagem técnica no log.
- Mensagem amigável na UI.
- Indicação se o progresso foi preservado.
- Próxima ação possível.

## 8. Git e releases

- Branches: prefixo `codex/` para trabalho de agentes, salvo instrução contrária.
- Commits pequenos, intencionais e coerentes.
- Não versionar modelos, áudios de usuário, bancos locais, logs, builds ou segredos.
- Release nasce de tag versionada e pipeline limpa.
- Publicar instalador, checksum SHA-256, changelog e licenças.

## 9. Documentação obrigatória por tipo de mudança

| Mudança | Documentos mínimos |
|---|---|
| Funcionalidade | REQUIREMENTS, STATUS, ROADMAP, CHANGELOG |
| Arquitetura/stack | ARCHITECTURE, DECISIONS, STATUS |
| Interface/fluxo | UX, REQUIREMENTS, STATUS, CHANGELOG |
| Schema | ARCHITECTURE, DECISIONS, STATUS |
| Build/instalador | ARCHITECTURE, TESTING, STATUS, CHANGELOG |
| Correção interna | STATUS; CHANGELOG se visível |
| Novo risco | STATUS e documento relacionado |

## 10. Relatório de entrega

Formato mínimo:

```text
Objetivo:
Requisitos afetados:
Alterações:
Testes executados:
Resultado:
Documentação atualizada:
Pendências/limitações:
```

## 11. Captura local de reuniões

- PyAudioWPatch é a implementação inicial do adaptador WASAPI. Antes de mudar de biblioteca ou adotar helper nativo, executar prova técnica de 60 minutos em alto-falante, USB e Bluetooth.
- A implementação deve ficar atrás de port; não chamar APIs de captura diretamente da UI ou do motor de transcrição.
- A mudança de schema deve registrar sessões e blocos por migração versionada.
- Nenhuma dependência nativa entra no instalador sem análise de licença, tamanho, fallback e teste empacotado.
