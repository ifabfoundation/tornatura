import { useEffect, useRef } from "react";

interface AutoHeightIframeProps {
  src: string;
  className?: string;
}
export function AutoHeightIframe({ src, className }: AutoHeightIframeProps) {
  const iframeRef = useRef<HTMLIFrameElement | null>(null);

  // Resize on initial load (same‑origin only)
  useEffect(() => {
    const iframe = iframeRef.current;
    if (!iframe) return;

    const handleLoad = () => {
      try {
        const doc = iframe.contentDocument || iframe.contentWindow?.document;
        if (!doc) return;

        const height = doc.documentElement.scrollHeight;
        iframe.style.height = `${height}px`;
      } catch {
        // Cross-origin → cannot access height
      }
    };

    iframe.addEventListener("load", handleLoad);
    return () => iframe.removeEventListener("load", handleLoad);
  }, []);

  // Listen for postMessage height updates (for dynamic content)
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      const data = event.data as { iframeHeight?: number };
      if (typeof data?.iframeHeight === "number") {
        if (iframeRef.current) {
          iframeRef.current.style.height = `${data.iframeHeight}px`;
        }
      }
    };

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  return (
    <iframe
      ref={iframeRef}
      src={src}
      className={className}
      style={{
        width: "100%",
        border: "none",
        display: "block",
      }}
      scrolling="no"
    />
  );
}
