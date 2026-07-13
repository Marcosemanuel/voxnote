import { useEffect, useRef } from "react";

const MAX_PIXEL_RATIO = 1.5;
const MAX_FPS = 30;
const MOBILE_BREAKPOINT = 560;

function clamp(value: number, minimum: number, maximum: number) {
  return Math.min(Math.max(value, minimum), maximum);
}

export default function SonicWaveform() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const context = canvas.getContext("2d");
    if (!context) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const pointer = { currentX: 0.5, currentY: 0.5, targetX: 0.5, targetY: 0.5 };
    let frame = 0;
    let width = 0;
    let height = 0;
    let time = 0;
    let lastTimestamp = 0;

    const resize = () => {
      const bounds = canvas.getBoundingClientRect();
      const pixelRatio = Math.min(window.devicePixelRatio, MAX_PIXEL_RATIO);
      width = Math.max(1, Math.round(bounds.width));
      height = Math.max(1, Math.round(bounds.height));
      canvas.width = Math.round(width * pixelRatio);
      canvas.height = Math.round(height * pixelRatio);
      context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
    };

    const draw = () => {
      context.clearRect(0, 0, width, height);
      const centerY = height * 0.52;
      const compact = width < MOBILE_BREAKPOINT;
      const lineCount = compact ? 12 : 18;
      const segmentCount = Math.round(clamp(width / (compact ? 13 : 16), 32, 54));
      const maxAmplitude = Math.min(height * (compact ? 0.26 : 0.3), compact ? 62 : 88);

      for (let line = 0; line < lineCount; line += 1) {
        const progress = line / (lineCount - 1);
        const distanceFromCenter = Math.abs(progress - 0.5) * 2;
        const alpha = (1 - distanceFromCenter) * 0.31 + 0.045;
        context.beginPath();
        context.strokeStyle = `rgb(59 130 246 / ${alpha})`;
        context.lineWidth = compact ? 1.15 : 1.3;
        context.lineCap = "round";

        for (let segment = 0; segment <= segmentCount; segment += 1) {
          const x = (segment / segmentCount) * width;
          const mouseDistance = Math.hypot(x - pointer.currentX * width, centerY - pointer.currentY * height);
          const mouseInfluence = Math.max(0, 1 - mouseDistance / Math.max(width * 0.36, 180));
          const carrier = Math.sin(segment * 0.18 + time * 0.95 + line * 0.31);
          const detail = Math.sin(segment * 0.61 - time * 0.54 + line * 0.12);
          const amplitude = maxAmplitude * (0.34 + progress * 0.66) * (1 + mouseInfluence * 0.16);
          const y = centerY + carrier * amplitude * 0.66 + detail * amplitude * 0.16;

          if (segment === 0) context.moveTo(x, y);
          else context.lineTo(x, y);
        }

        context.stroke();
      }
    };

    const render = (timestamp: number) => {
      const frameDuration = 1000 / MAX_FPS;
      if (reducedMotion || timestamp - lastTimestamp >= frameDuration) {
        const elapsed = Math.min(timestamp - lastTimestamp || frameDuration, 100);
        lastTimestamp = timestamp;
        pointer.currentX += (pointer.targetX - pointer.currentX) * 0.08;
        pointer.currentY += (pointer.targetY - pointer.currentY) * 0.08;
        time += elapsed * 0.00085;
        draw();
      }
      if (!reducedMotion) frame = window.requestAnimationFrame(render);
    };

    const onPointerMove = (event: PointerEvent) => {
      const bounds = canvas.getBoundingClientRect();
      pointer.targetX = clamp((event.clientX - bounds.left) / bounds.width, 0, 1);
      pointer.targetY = clamp((event.clientY - bounds.top) / bounds.height, 0, 1);
    };

    const observer = new ResizeObserver(resize);
    observer.observe(canvas);
    canvas.addEventListener("pointermove", onPointerMove, { passive: true });
    resize();
    draw();
    if (!reducedMotion) frame = window.requestAnimationFrame(render);

    return () => {
      window.cancelAnimationFrame(frame);
      observer.disconnect();
      canvas.removeEventListener("pointermove", onPointerMove);
    };
  }, []);

  return <canvas ref={canvasRef} className="sonic-waveform" aria-hidden="true" />;
}
