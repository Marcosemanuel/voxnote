# Landing Voxnote

Landing estática em React + Vite, pronta para Vercel. A animação do hero usa Canvas 2D e não requisita microfone, áudio ou dados do visitante.

## Desenvolvimento

```powershell
npm install
npm run dev
```

## Download real

O botão aponta por padrão para o ativo permanente `Voxnote-Setup-win64.exe` da Release pública mais recente. O endereço usa `releases/latest/download`, portanto não contém número de versão e continua válido nas próximas Releases. Copie `.env.example` para `.env` apenas se precisar substituir esse endereço em outro ambiente.

## Vercel

1. Publique o repositório no GitHub.
2. Importe-o na Vercel e selecione `landing` como Root Directory.
3. Configure `VITE_DOWNLOAD_URL` em Production com o ativo permanente `https://github.com/Marcosemanuel/voxnote/releases/latest/download/Voxnote-Setup-win64.exe` ou remova a variável para usar o mesmo padrão incorporado no código.
4. Faça o deploy. Cada push no repositório criará um preview e o branch de produção publicará a versão final.
