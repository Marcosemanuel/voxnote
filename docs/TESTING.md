# Estratégia de testes

## 1. Regra

Nenhuma funcionalidade está pronta apenas porque foi implementada. Deve existir evidência proporcional ao risco.

## 2. Pirâmide

### Unitários

- Estados e transições.
- Seleção de perfil.
- Validação de parâmetros.
- Regras de revisão.
- Geração de exportações.
- Resolução de caminhos.
- Tratamento de erros.

### Integração

- SQLite e migrações.
- PyAV e formatos.
- Engine com amostras curtas.
- Download, retomada e hash.
- Checkpoint e retomada.
- Exportadores.

### Interface

- Registro da Manrope embutida e ausência de fontes substitutas na folha de estilo.
- Números tabulares em timestamps, durações e percentuais.
- Navegação.
- Validação e mensagens.
- Responsividade durante worker.
- Pausa e cancelamento.
- Edição e salvamento.
- Teclado e foco.
- Carregamento do shell QML e contrato do `QmlController`.
- `pyside6-qmlformat` e `pyside6-qmllint` sobre os arquivos QML.
- Capturas com `QQuickWindow.grabWindow()` para comparação visual independente do utilitário de captura do Windows.

### Sistema/instalador

- Instalação limpa.
- Inicialização sem Python.
- CPU sem CUDA.
- GPU compatível.
- GPU incompatível com fallback.
- Atualização preservando dados.
- Desinstalação preservando dados.

## 3. Matriz mínima de máquinas

| Perfil | RAM | GPU | Propósito |
|---|---:|---|---|
| Mínimo | 8 GB | nenhuma | Compatibilidade básica |
| Comum | 16 GB | nenhuma | CPU normal |
| CPU forte | 32 GB | nenhuma | Alta precisão em CPU |
| GPU limitada | 16 GB | 4 GB | Fallback e memória |
| GPU comum | 16 GB | 6-8 GB | Uso acelerado |
| GPU forte | 32 GB | 12 GB+ | Lote e desempenho |

## 4. Corpus de áudio

Manter fixtures redistribuíveis, pequenas e documentadas. Não versionar material privado.

Cobertura:

- Um arquivo de cada formato.
- Português limpo.
- Celular.
- Reunião.
- Voz distante.
- Ruído.
- Voz baixa.
- Sobreposição de falantes.
- Termos técnicos.
- Silêncio prolongado.
- Arquivo corrompido.
- Arquivo sem áudio.
- Cenário sintético equivalente a oito horas para memória e retomada.

## 5. Precisão

Medir:

- WER.
- CER.
- Omissões.
- Repetições.
- Alucinações em silêncio.
- Erro de timestamp.
- Diferença entre original e referência.

Resultados devem registrar modelo, engine, idioma, hardware e parâmetros. Não comparar execuções sem esses dados.

## 6. Desempenho

Medir:

- Tempo por hora de áudio.
- Pico e estabilização de RAM.
- Pico de VRAM.
- Uso de CPU.
- Tempo de carregamento do modelo.
- Velocidade de exportação.
- Responsividade da UI.

Não aprovar áudio longo se a memória crescer continuamente.

## 7. Recuperação

Testar:

- Fechamento normal.
- Encerramento pelo Gerenciador de Tarefas.
- Reinício do Windows.
- Falta de espaço.
- Falta de memória.
- Arquivo movido.
- Modelo removido.
- Download interrompido.
- Erro de CUDA.
- Pausas repetidas.
- Cancelamento durante segmento.

## 8. Acessibilidade e visual

- Teclado completo.
- Foco visível.
- Leitor de tela nos controles principais.
- 1366x768 e 1920x1080.
- Escalas de 100%, 125%, 150% e 200%.
- Texto e estado compreensíveis sem depender de cor.

## 9. Gates

Antes de merge:

```text
ruff check
ruff format --check
mypy
pytest
pyside6-qmllint --unqualified=disable src/transcritor/qml/**/*.qml
pyside6-qmlformat -i src/transcritor/qml/**/*.qml
```

Os comandos poderão ser ajustados quando o projeto for inicializado, mas qualquer alteração deve ser atualizada aqui e no CI.

Antes de release:

- Todos os critérios `AC-001` a `AC-014` aplicáveis.
- Smoke test do instalador em VM limpa.
- Checksum conferido.
- Licenças conferidas.
- Changelog conferido.
- `docs/STATUS.md` sem afirmação não comprovada.

## 10. Landing pública

- `npm run build` deve concluir dentro de `landing/`.
- Verificar a primeira dobra em desktop e em 390x844, incluindo bordas, espaçamentos, texto, botão e onda Canvas 2D.
- Conferir que a landing não solicita permissões de microfone nem acessa conteúdo de áudio.
- Sem `VITE_DOWNLOAD_URL`, o CTA deve ficar desabilitado; com a variável configurada, ele deve apontar para o instalador publicado.
