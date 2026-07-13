# Estudo de ferramentas para o frontend Voxnote

Data: 2026-07-12

## Decisão

Migrar somente a camada visual de `PySide6.QtWidgets` para **Qt Quick/QML + Qt Quick Controls 2**.

O motor de transcrição, SQLite, downloads, hardware, exportadores e regras de domínio continuam em Python. A
interface QML conversa com esses serviços por uma camada pequena de `QObject`, propriedades, sinais e slots.

Base recomendada:

- PySide6 6.11.1 para Windows x64.
- `QQmlApplicationEngine` para carregar a aplicação.
- Qt Quick Controls 2 com estilo `Basic` como fallback previsível.
- Biblioteca própria `Voxnote.Controls`, construída com os tokens e referências visuais já aprovados.
- `QtQuick.Layouts`, `ScrollView`, `StackLayout`, `ListView` e `TableView` para composição responsiva.
- Manrope incorporada e SVGs Lucide já presentes no repositório.
- `qmllint`, `qmlformat`, pytest-qt e regressão visual por screenshot.

## Diagnóstico comprovado

O executável atual foi capturado em Windows com 144 DPI, equivalente a escala de 150%. As imagens estão em
`.codex-audit/frontend-2026-07-12/`.

Problemas estruturais encontrados:

1. `ui.py` concentra estilo global, componentes, páginas e navegação em um único arquivo com mais de mil linhas.
2. Há larguras fixas para sidebar, busca e colunas de tabela. Em escala alta, conteúdo e ações saem da área visível.
3. As páginas não têm uma política uniforme de `ScrollView`/reflow para altura reduzida ou escala de 150% a 200%.
4. `QTableWidget` impõe aparência de tabela clássica. Estados, ações, badges e progresso exigem widgets inseridos célula por célula.
5. O QSS controla cor e borda, mas não resolve composição, transição, reflow, estados e delegates complexos.
6. Componentes semelhantes são recriados em cada página, permitindo diferenças de margem, altura e comportamento.
7. A barra de título nativa clássica e os controles internos modernos não formam uma linguagem visual única.

## Comparação das alternativas

| Alternativa | Ganho imediato | Problema | Decisão |
|---|---:|---|---|
| Continuar com QWidget + QSS | Baixo | Mantém limitações de layout, tabela e composição atuais | Rejeitada |
| `qt-material` | Médio e rápido | Troca o tema, mas não corrige arquitetura, clipping ou identidade Voxnote | Não usar como base |
| PyQt/PySide Fluent Widgets | Alto | GPLv3 para uso não comercial; licença comercial separada; cria dependência central externa | Não adotar |
| Qt Quick `FluentWinUI3` | Alto | Bom ponto de referência, porém alguns controles usam fallback e partes baseadas em imagem limitam customização | Usar para comparação, não como design final |
| Qt Quick/QML + Voxnote Controls | Alto | Exige migração controlada da camada visual | **Escolhida** |
| React/Tauri + processo Python | Alto | Dois runtimes, IPC, empacotamento e superfície operacional maiores | Rejeitada para este produto |
| WinUI 3/.NET + processo Python | Alto | Reescrita completa da UI e nova fronteira de integração | Rejeitada |

## Por que Qt Quick/QML

- Permanece no ecossistema oficial Qt/PySide6 e preserva a distribuição local.
- Layouts redimensionam os itens e aceitam mínimos, preferidos, máximos e stretch factors.
- QML facilita componentes visuais pequenos e reutilizáveis, sem duplicar configuração em cada tela.
- Estados `hovered`, `pressed`, `focused`, `disabled`, `loading`, `success` e `error` podem ser definidos no componente.
- Listas e tabelas usam delegates, evitando centenas de widgets incorporados em células.
- A interface pode usar aceleração gráfica sem interferir no motor de transcrição executado em workers Python.

Fontes oficiais:

- [Qt Quick Controls styles](https://doc.qt.io/qtforpython-6/overviews/qtquickcontrols-styles.html)
- [Customização de Qt Quick Controls](https://doc.qt.io/qtforpython-6/overviews/qtquickcontrols-customize.html)
- [Qt Quick Layouts](https://doc.qt.io/qtforpython-6/overviews/qtquicklayouts-overview.html)
- [Layouts responsivos](https://doc.qt.io/qtforpython-6/overviews/qtquicklayouts-responsive.html)
- [QQmlApplicationEngine](https://doc.qt.io/qtforpython-6/PySide6/QtQml/QQmlApplicationEngine.html)

## Biblioteca visual Voxnote

Estrutura proposta:

```text
src/transcritor/ui_qml/
  Main.qml
  Theme.qml
  components/
    AppShell.qml
    Sidebar.qml
    NavItem.qml
    PageHeader.qml
    Surface.qml
    PrimaryButton.qml
    SecondaryButton.qml
    IconButton.qml
    FormField.qml
    SelectField.qml
    TextArea.qml
    StatusBadge.qml
    ProgressIndicator.qml
    DataTable.qml
    EmptyState.qml
  pages/
    NewTranscriptionPage.qml
    TranscriptionsPage.qml
    ModelsPage.qml
    SettingsPage.qml
    HelpPage.qml
    ProgressPage.qml
    ReviewPage.qml
```

Regras obrigatórias:

- Tokens definidos uma vez em `Theme.qml`.
- Conteúdo com largura máxima e margem responsiva; nenhuma página pode depender da largura absoluta da janela.
- Sidebar completa em telas largas e compacta quando o espaço útil for insuficiente.
- Toda página longa usa rolagem; o rodapé de ação permanece acessível.
- Tabelas usam proporções e largura mínima, não somas de colunas fixas.
- Estados vazios, carregando, sucesso e erro são componentes, não textos improvisados.
- Ícones somente da coleção adotada, com tamanho 20/24px e cor contextual.
- Manrope 400/500/600/700; nenhuma fonte abaixo de 11px.

## Instrumentos de qualidade

### Código QML

- `qmlformat --check`: padronização mecânica.
- `qmllint --max-warnings 0`: sintaxe, propriedades inválidas, imports e antipadrões.
- QML Language Server: diagnóstico em tempo real no editor.

### Regressão visual

Capturar cada página nos estados essenciais em:

- 1366x768: 100%, 125%, 150% e 200%.
- 1920x1080: 100%, 150% e 200%.
- Janela mínima definida pelo layout.

Cada captura deve ser comparada à referência aprovada. O build falha quando houver clipping, controle fora da área,
texto truncado sem regra ou mudança visual acima da tolerância definida.

### Acessibilidade

- Ordem completa por teclado e foco visível.
- Nome e descrição acessíveis em todos os controles.
- Área interativa mínima de 44x44px.
- Accessibility Insights for Windows: FastPass por release.
- Narrator e UI Automation para o fluxo adicionar, transcrever, revisar e exportar.

## Plano de migração

1. Criar um protótipo QML isolado da tela `Nova transcrição`, sem remover a UI atual.
2. Validar identidade, 100% a 200% de escala, teclado, tempo de abertura e consumo de memória.
3. Criar a ponte Python/QML para seleção de arquivos, hardware e início da fila.
4. Migrar `Transcrições` e `Modelos`, incluindo delegates e estados.
5. Migrar processamento e revisão, que possuem maior risco funcional.
6. Migrar Configurações e Ajuda.
7. Rodar os dois frontends temporariamente por uma flag interna até o fluxo QML atingir paridade.
8. Remover a UI QWidget somente após testes e regressão visual aprovados.

## Critérios de aceite

- Nenhum clipping em 100%, 125%, 150% e 200%.
- Todas as telas seguem a mesma grade, tokens e componentes.
- Fluxo principal funciona apenas por teclado.
- Todos os estados importantes possuem texto e representação visual.
- Tempo de abertura e consumo de memória medidos contra a versão QWidget.
- Build Windows x64 contém todos os módulos QML necessários e funciona em máquina limpa.
- Testes Python atuais continuam aprovados.

## Estado

Estudo concluído e decisão implementada. O shell Qt Quick/QML é a interface padrão; a versão QWidget permanece
temporariamente disponível por `VOXNOTE_LEGACY_UI=1` até a matriz visual e funcional ser concluída.
