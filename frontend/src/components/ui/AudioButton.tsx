"use client";

import { useCallback, useState } from "react";
import { playWithSpeechSynthesis } from "@/lib/speech";

function getOrigin(): string {
  if (typeof window !== "undefined") return window.location.origin;
  return "";
}

export default function AudioButton({ text, className = "" }: { text: string; className?: string }) {
  const [playing, setPlaying] = useState(false);

  const play = useCallback(() => {
    if (!text || playing) return;
    setPlaying(true);
    const origin = getOrigin();
    const token = typeof window !== "undefined" ? localStorage.getItem("tocfl_token") : null;
    const url = origin ? `${origin}/api/audio?text=${encodeURIComponent(text)}` : `/api/audio?text=${encodeURIComponent(text)}`;
    fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((r) => {
        if (!r.ok) throw new Error("Audio not available");
        return r.blob();
      })
      .then((blob) => {
        const blobUrl = URL.createObjectURL(blob);
        const audio = new Audio(blobUrl);
        audio.onended = () => {
          URL.revokeObjectURL(blobUrl);
          setPlaying(false);
        };
        audio.onerror = () => {
          URL.revokeObjectURL(blobUrl);
          setPlaying(false);
        };
        audio.play().catch(() => setPlaying(false));
      })
      .catch(() => {
        playWithSpeechSynthesis(text)
          .then(() => setPlaying(false))
          .catch(() => setPlaying(false));
      });
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
