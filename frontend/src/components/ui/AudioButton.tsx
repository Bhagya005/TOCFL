"use client";

import { useCallback, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AudioButton({ text, className = "" }: { text: string; className?: string }) {
  const [playing, setPlaying] = useState(false);

  const play = useCallback(() => {
    if (!text || playing) return;
    setPlaying(true);
    const token = typeof window !== "undefined" ? localStorage.getItem("tocfl_token") : null;
    fetch(`${API_URL}/api/audio?text=${encodeURIComponent(text)}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((r) => r.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.onended = () => {
          URL.revokeObjectURL(url);
          setPlaying(false);
        };
        audio.onerror = () => {
          URL.revokeObjectURL(url);
          setPlaying(false);
        };
        audio.play().catch(() => setPlaying(false));
      })
      .catch(() => setPlaying(false));
  }, [text, playing]);

  return (
    <button
      type="button"
      onClick={play}
      className={`
        inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full
        border border-slate-600 bg-slate-700/50 text-slate-200
        hover:bg-slate-600 hover:border-slate-500 transition-colors
        disabled:opacity-50 disabled:pointer-events-none
        ${className}
      `}
      disabled={playing}
      aria-label="Play audio"
    >
      {playing ? (
        <span className="text-amber-400">⟳</span>
      ) : (
        <span className="text-lg leading-none">▶</span>
      )}
    </button>
  );
}
