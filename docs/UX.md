# Frontend e experiência do usuário

## 1. Objetivo

A interface deve parecer um utilitário profissional, não uma ferramenta técnica de IA.

Fluxo dominante:

`Adicionar -> Transcrever -> Revisar -> Exportar`

## 2. Navegação

Barra lateral com apenas:

1. Nova transcrição
2. Transcrições
3. Modelos
4. Configurações
5. Ajuda

## 3. Telas obrigatórias

### Nova transcrição

- Área ampla de arrastar e soltar.
- Botão `Selecionar arquivos`.
- Lista com nome, duração, formato, tamanho e remoção, exibida somente após selecionar arquivos.
- Idioma.
- Qualidade em nomes amigáveis.
- Glossário opcional.
- Recomendação automática de hardware.
- Uma ação primária: `Iniciar transcrição`.

### Processamento

- Arquivo atual e posição na fila.
- Percentual por duração.
- Tempo processado, total, decorrido e restante estimado.
- Perfil e dispositivo em linguagem amigável.
- Último trecho concluído.
- Confirmação de salvamento automático.
- Pausar e cancelar.

### Transcrições

- Busca e filtros.
- Estado textual e visual.
- Continuar, revisar e exportar.
- Exclusão explica que o áudio original será preservado.

### Revisão

- Player fixo.
- Lista de segmentos com timestamps.
- Texto editável.
- Filtro de trechos para revisar.
- Busca e substituição.
- Original e revisado separados.
- Atalhos de teclado.

### Modelos

- Nome amigável, finalidade, tamanho e estado.
- Baixar com retomada automática em nova tentativa, verificar integridade e remover.
- Nome técnico somente em detalhes.

### Retomada

- Trabalhos prontos, pausados, cancelados ou falhos exibem `Continuar` no histórico.
- A retomada começa depois do último trecho confirmado.
- Fechar durante transcrição solicita cancelamento cooperativo e aguarda o worker terminar.

### Configurações

- Geral, Processamento, Armazenamento, Privacidade e Avançado.
- Avançado recolhido por padrão.

### Ajuda

- Conteúdo offline para fluxo principal, precisão, glossário, revisão, exportação, arquivos, GPU, formatos, privacidade e diagnóstico.

## 4. Linguagem

Use:

| Técnico | Texto da interface |
|---|---|
| Inferência | Transcrição |
| Backend CUDA | Aceleração NVIDIA |
| Fallback CPU | Continuar usando o processador |
| OOM | Memória insuficiente |
| Job | Transcrição |
| Chunk | Trecho |
| Low confidence | Verifique este trecho |
| Resume | Continuar |

Não mostrar batch, quantização, VAD, tokens ou probabilidades no fluxo normal.

## 5. Mensagens de erro

Toda mensagem deve informar:

1. O que aconteceu.
2. Se o progresso foi preservado.
3. O que o usuário pode fazer.

Exemplo:

> A transcrição foi pausada por falta de memória. Todo o progresso foi salvo. Recomendamos continuar no modo Equilibrado.

## 6. Estados visuais

| Estado | Rótulo |
|---|---|
| pending | Aguardando |
| validating | Verificando arquivo |
| downloading_model | Baixando modelo |
| transcribing | Em andamento |
| paused | Pausada |
| completed | Concluída |
| failed | Não concluída |
| cancelled | Interrompida |

Cor nunca é o único indicador; use ícone e texto.

## 7. Acessibilidade

- Navegação completa por teclado.
- Ordem de tabulação lógica.
- Foco visível.
- Labels programáticos.
- Compatibilidade com leitor de tela.
- Área clicável mínima de 40x40 px.
- Fonte mínima de 14 px.
- Contraste adequado.
- Escala de 100% a 200%.
- Layout mínimo de 1366x768.
- Redimensionamento sem esconder ações.

## 8. Hierarquia visual

- Uma ação primária por tela.
- Ações destrutivas somente em vermelho.
- Ícones importantes acompanhados por texto.
- Fundo claro, superfícies brancas, azul como primária, âmbar para atenção, verde para sucesso e vermelho para erro.
- Sem decoração, animação ou informação técnica desnecessária.
- Páginas informativas devem usar superfície branca explícita e texto escuro; nunca depender da paleta padrão do Qt.
- Estados vazios não podem reservar grandes áreas sem conteúdo nem herdar superfícies escuras do Qt.

### Sistema visual aprovado

- Marca: Voxnote. O símbolo oficial é usado na barra lateral e no ícone do executável; o nome da marca na interface usa Manrope e não tenta reproduzir a tipografia proprietária do logotipo a partir de imagem raster.
- Paleta oficial: `#111111` (texto principal), `#2B2B2B` (texto secundário escuro), `#D9D9D6` (bordas e neutros), `#F5F5F3` (fundo) e `#3B82F6` (ação, foco e destaque).
- Superfícies de leitura e edição permanecem brancas; a barra lateral e a tela usam `#F5F5F3`. Azul é reservado a ações, foco, seleção e indicador do símbolo.
- Navegação selecionada usa fundo azul claro derivado e borda esquerda `#3B82F6`; erros permanecem em vermelho sem disputar o papel do azul de marca.
- Ícones de interface usam Lucide em SVG, base 24px, traço de 2px, `round` em pontas e junções, e cor herdada do contexto. Não misturar ícones preenchidos, emoji ou estilos de traço diferentes.
- A interface usa exclusivamente Manrope, incorporada ao aplicativo e sem dependência de fonte instalada no Windows.
- Pesos permitidos: 400, 500, 600 e 700. Pesos 300 e 800 não são permitidos.
- Escala: título principal 32/40px peso 700 (-0,5px); título de seção 20/28px peso 600 (-0,2px); subtítulo 16/24px peso 600; corpo 16/24px peso 400; secundário 14/20px peso 400; labels 13/18px peso 600; legenda e timestamp 12/16px peso 500.
- Botões usam 14/20px peso 600 e espaçamento de 0,2px. Navegação usa 14/20px peso 500, ou 600 no item ativo. Inputs usam 16/24px peso 400. Tabelas usam 14/20px peso 400 e cabeçalhos peso 600.
- Texto transcrito usa 16/26px peso 400. Durações, percentuais e timestamps usam Manrope com o recurso OpenType `tnum` para números tabulares.
- Gutter de conteúdo: 40px; seções: 20px; controles: 42px; raios: 8px a 12px.
- A navegação é uma faixa branca com divisor direito e estado ativo em azul claro com borda esquerda.
- Formulários longos devem usar divisores e alinhamento de rótulos; não empilhar cartões sem necessidade.
- Padrão de telas Voxnote: barra lateral de 260px, ícones de contorno 2px, cartões brancos com raio de 20px e sombra discreta, canvas `#F5F5F3` e espaçamento de página de 48px.
- O painel de upload deve ter um cartão externo e uma área tracejada interna. Configurações, Ajuda, Modelos e Histórico devem usar superfícies únicas elevadas, em vez de blocos HTML ou tabelas sem contexto.
- Na tela Nova transcrição, `Configurações` é uma seção direta abaixo do upload: título fora de cartão, labels em uma coluna fixa e controles alinhados. Não criar um segundo cartão em torno do formulário.
- Histórico usa ícone de arquivo, estado textual com cor de apoio, percentual tabular e barra de progresso no mesmo campo; as ações são ícones com tooltip. Modelos usa uma única tabela elevada e botões de download com contorno azul.
- Navegação, busca, upload e ações de tabela usam ícones Lucide monocromáticos; azul apenas em item ativo, destaque, foco e ação primária. Ações somente por ícone devem ter tooltip e nome acessível.
- O shell oficial usa Qt Quick/QML. Margens, colunas e sidebar reagem à largura disponível; páginas longas usam `ScrollView` e tabelas usam delegates proporcionais.
- Componentes básicos ficam em `src/transcritor/qml/components`; correções visuais devem ocorrer no componente compartilhado antes de criar exceções na página.

## 9. Atalhos mínimos da revisão

| Ação | Atalho |
|---|---|
| Reproduzir/pausar | Espaço |
| Voltar 5 segundos | Ctrl+Seta esquerda |
| Avançar 5 segundos | Ctrl+Seta direita |
| Segmento anterior | Alt+Seta acima |
| Próximo segmento | Alt+Seta abaixo |
| Próximo aviso | Ctrl+Seta abaixo |
| Marcar revisado | Ctrl+Enter |
| Buscar | Ctrl+F |
| Exportar | Ctrl+E |

## 10. Regra de alteração de frontend

Toda mudança de UI deve:

1. Identificar o fluxo afetado.
2. Preservar o caminho principal.
3. Incluir estados vazio, carregando, sucesso, pausa e erro quando aplicáveis.
4. Ser testada por teclado e em 1366x768, 1920x1080, escala 100% e 200%.
5. Atualizar este documento se modificar comportamento ou navegação.

## 11. Landing pública

- A cena decorativa da landing é Canvas 2D e deve ser ignorada por tecnologias assistivas.

- Ordem fixa: hero, recursos, passos e rodapé.
- O hero exibe a marca, a cena decorativa de gravação, a promessa de processamento local e o botão de download.
- Em mobile, a largura útil é a viewport menos 32px; recursos e passos passam para uma coluna com cartões de borda `#DEDED9`, raio de 18px e espaçamento de 16px.
- O botão de download ocupa no máximo 330px e tem 58px de altura em mobile.
- A cena Canvas 2D é decorativa e deve ser ignorada por tecnologias assistivas.

## 12. Captura de reunião

- Entrada explícita `Capturar reunião`; não detectar nem iniciar captura automaticamente.
- Tela de preparação: consentimento, seleção da saída do Windows, microfone opcional e teste de sinal, sem dividir o início em um assistente desnecessário.
- Durante a captura: indicador visível, duração, sinal da saída/microfone, último bloco salvo e estado de finalização.
- Ao encerrar: executar o reconhecimento final antes da revisão; não substituir silenciosamente a versão provisória ou texto revisado.
- A tela mostra reuniões salvas e permite retomar a revisão e a exportação de uma transcrição concluída após reiniciar o aplicativo. Sessões com blocos preservados exibem `Transcrever` ou `Reprocessar`, inclusive após falha; a ação cria uma nova versão sem substituir a anterior.
- Se o monitoramento detectar variação superior a 250 ms entre as trilhas, a tela informa que os timestamps devem ser revisados antes da exportação. As trilhas não são combinadas automaticamente.
- Todos os controles da captura usam o sistema Voxnote: `VxCheckBox`, `VxComboBox`, `VxProgressBar`, `VxTextArea` e `VxButton`; cartões de preparação, andamento, conclusão e reuniões salvas preservam a mesma hierarquia, borda, raio e espaçamento.

O fluxo completo de telas, estados, componentes, copy, responsividade e acessibilidade está especificado em `docs/MEETING_CAPTURE_STACK_FRONTEND.md`. O modo universal será `Capturar e transcrever ao final`; acompanhamento provisório só aparece quando o benchmark local aprovar o hardware.
