# Landing Voxnote

Landing estática em React + Vite, pronta para Vercel. A animação do hero usa Canvas 2D e não requisita microfone, áudio ou dados do visitante.

## Desenvolvimento

```powershell
npm install
npm run dev
```

## Download real

O botão aponta por padrão para a Release pública atual do Voxnote. Copie `.env.example` para `.env` e defina `VITE_DOWNLOAD_URL` somente se precisar substituir o URL de download do instalador no GitHub Releases.

## Vercel

1. Publique o repositório no GitHub.
2. Importe-o na Vercel e selecione `landing` como Root Directory.
3. Configure `VITE_DOWNLOAD_URL` nas variáveis de ambiente de Production.
4. Faça o deploy. Cada push no repositório criará um preview e o branch de produção publicará a versão final.
