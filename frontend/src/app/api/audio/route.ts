import { NextResponse } from "next/server";

/**
 * TTS audio endpoint. On Vercel, the Python gTTS backend is not available.
 * Options for production:
 * 1. Use a serverless TTS API (e.g. Google Cloud TTS, VoiceRSS) and proxy here.
 * 2. Use client-side SpeechSynthesis in the frontend (see AudioButton fallback).
 * This route returns 501 until a TTS provider is configured.
 */
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const text = searchParams.get("text") ?? "";

  if (!text.trim()) {
    return NextResponse.json({ detail: "Missing text" }, { status: 400 });
  }

  // Optional: call an external TTS API if env is set, e.g. NEXT_PUBLIC_TTS_API_URL
  const ttsUrl = process.env.TTS_API_URL;
  if (ttsUrl) {
    try {
      const res = await fetch(
        `${ttsUrl}?text=${encodeURIComponent(text)}&lang=zh-CN`,
        { headers: request.headers.get("authorization") ? { Authorization: request.headers.get("authorization")! } : {} }
      );
      if (res.ok) {
        const blob = await res.blob();
        return new NextResponse(blob, {
          headers: { "Content-Type": "audio/mpeg" },
        });
      }
    } catch {
      // fall through to 501
    }
  }

  return NextResponse.json(
    {
      detail:
        "Audio not available. Configure TTS_API_URL or use client-side speech synthesis.",
    },
    { status: 501 }
  );
}
