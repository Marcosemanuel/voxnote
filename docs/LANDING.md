# Landing pública Voxnote

## Objetivo

Apresentar o Voxnote e conduzir ao download gratuito do instalador Windows x64.
Não é uma aplicação de transcrição, não recebe arquivos de áudio e não coleta áudio de microfone.

## Estrutura aprovada

1. Hero: o que é o Voxnote, botão de download e animação decorativa de gravação.
2. O que faz: transcrição de áudios longos, processamento local e exportação.
3. Como utilizar: baixar e instalar, adicionar áudio, revisar e exportar.

## Implementação

- Código isolado em `landing/`, com React, Vite e Canvas 2D.
- A onda decorativa é desenhada em Canvas 2D, com no máximo 30 fps, densidade adaptativa e movimento reduzido. Não usa `getUserMedia`, microfone, arquivos do visitante ou transmissão de dados.
- Em telas com largura menor que 560px, a cena reduz linhas, amplitude e pontos desenhados para evitar corte e trabalho visual desnecessário.
- A landing usa Manrope empacotada em `landing/public/fonts/`; não depende de Google Fonts.
- A interface móvel usa uma coluna, botões de largura segura, cartões com borda leve e espaçamento de 16px entre itens para manter leitura e toque confortáveis.
- A onda ocupa a largura total do viewport, mantém 30 fps e usa amplitude/contraste reforçados para leitura clara sobre o fundo `#F5F5F3`.

### Regras de diagramação

- Gutter único com `--page-gutter`, largura máxima de conteúdo de 1120 px e ritmo vertical definido por seção.
- Cartões usam borda de 1 px, raio de 20 px e espaçamento interno consistente.
- Recursos e passos usam três colunas e gap de 20 px no desktop; em telas menores viram uma coluna com gap de 16 px.

## Download e deploy

### Copy aprovada

- Promessa principal: transcrição local com privacidade para uso profissional.
- Benefícios: áudios longos, processamento local e revisão/exportação em formatos usuais.
- CTA: download explícito para Windows 10 e 11 (64 bits), sem prometer recurso não disponível.

O botão usa `VITE_DOWNLOAD_URL`. O valor de produção deve apontar diretamente para o arquivo `.exe` publicado em GitHub Releases. Se a variável não existir, o botão fica desabilitado para não prometer um download inexistente.

Na Vercel, importe o repositório, defina `landing` como Root Directory e configure `VITE_DOWNLOAD_URL` no ambiente Production. A hospedagem serve somente a página estática; o instalador continua no GitHub Releases.

Deploy atual: https://voxnote-alpha.vercel.app/

## Verificação

- `npm run build` dentro de `landing/`.
- Conferir desktop e viewport 390x844 no navegador.
- Confirmar que a página carrega, que não há erro no console, que o botão sem URL está desabilitado e que o layout não possui cortes ou sobreposição.
