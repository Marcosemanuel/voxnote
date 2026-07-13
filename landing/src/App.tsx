import SonicWaveform from "./components/SonicWaveform";

const features = [
  {
    icon: "/icons/file-text.svg",
    motion: "feature--document",
    title: "Transcrição de áudios longos",
    text: "Processe entrevistas, reuniões e aulas com checkpoints recuperáveis.",
  },
  {
    icon: "/icons/mic.svg",
    motion: "feature--recording",
    title: "Privacidade por padrão",
    text: "O áudio e o processamento permanecem no seu computador.",
  },
  {
    icon: "/icons/sparkles.svg",
    motion: "feature--review",
    title: "Revisão e exportação",
    text: "Revise o texto e exporte em TXT, SRT, VTT ou JSON.",
  },
];

const steps = [
  { icon: "/icons/audio-lines.svg", title: "Instale no Windows", text: "Baixe o Voxnote e instale no seu Windows 10 ou 11 (64 bits).", motion: "step--audio" },
  { icon: "/icons/mic.svg", title: "Configure e transcreva", text: "Adicione o áudio, escolha o idioma e inicie o processamento.", motion: "step--recording" },
  { icon: "/icons/file-text.svg", title: "Revise e exporte", text: "Revise o texto e salve no formato adequado ao seu trabalho.", motion: "step--document" },
];

const releaseDownloadUrl =
  "https://github.com/Marcosemanuel/voxnote/releases/latest/download/TranscritorLocal-Setup-0.1.0-win64.exe";
const downloadUrl = (import.meta.env.VITE_DOWNLOAD_URL as string | undefined) || releaseDownloadUrl;

function Brand() {
  return (
    <a className="brand" href="#inicio" aria-label="Voxnote, início">
      <span className="brand-mark"><img src="/brand/voxnote-symbol.png" alt="" /></span>
      <span>Voxnote</span>
    </a>
  );
}

function DownloadButton() {
  return <a className="download-button" href={downloadUrl}>Baixar para Windows 64 bits</a>;
}

export default function App() {
  return (
    <main id="inicio">
      <header className="site-header shell">
        <Brand />
      </header>

      <section className="hero shell" aria-labelledby="hero-title">
        <div className="scene-wrap"><SonicWaveform /></div>
        <div className="recording-status"><span /> LOCAL <time>ATIVO</time></div>
        <div className="hero-copy">
          <h1 id="hero-title">Transcrição local.<br />Privacidade para o seu trabalho.</h1>
          <p>O Voxnote transforma áudios longos em texto revisável, diretamente no seu computador. Simples de usar, seguro por padrão e desenvolvido para Windows.</p>
          <DownloadButton />
          <small>Gratuito · Windows 10 e 11 (64 bits) · Sem envio de áudio</small>
        </div>
      </section>

      <section className="features shell" id="recursos" aria-labelledby="features-title">
        <h2 id="features-title">Recursos essenciais</h2>
        <div className="feature-grid">
          {features.map((feature) => <article className={`feature ${feature.motion}`} key={feature.title}><img src={feature.icon} alt="" /><h3>{feature.title}</h3><p>{feature.text}</p></article>)}
        </div>
      </section>

      <section className="steps shell" id="como-usar" aria-labelledby="steps-title">
        <h2 id="steps-title">Do áudio ao texto</h2>
        <ol>
          {steps.map((step, index) => <li className={step.motion} key={step.title}><span className="step-number">{index + 1}</span><img src={step.icon} alt="" /><h3>{step.title}</h3><p>{step.text}</p></li>)}
        </ol>
      </section>

      <footer className="site-footer shell"><Brand /><p>Transcrição local e gratuita para Windows 10 e 11 (64 bits).</p></footer>
    </main>
  );
}
