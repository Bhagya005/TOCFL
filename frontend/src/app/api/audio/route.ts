import { NextResponse } from "next/server";
import * as googleTTS from "google-tts-api";

/**
 * TTS audio endpoint. Uses Google Translate TTS (same source as gTTS) for natural
 * Chinese speech. Falls back to 501 if the request fails (client can use browser SpeechSynthesis).
 */
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const text = searchParams.get("text") ?? "";

  if (!text.trim()) {
    return NextResponse.json({ detail: "Missing text" }, { status: 400 });
  }

  // Optional: custom TTS proxy if env is set
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
      // fall through to Google TTS
    }
  }

  // Default: Google Translate TTS (same natural voice as gTTS)
  try {
    const trimmed = text.trim();
    let base64: string;
    if (trimmed.length <= 200) {
      base64 = await googleTTS.getAudioBase64(trimmed, {
        lang: "zh-CN",
        slow: false,
        timeout: 10000,
      });
    } else {
      const segments = await googleTTS.getAllAudioBase64(trimmed, {
        lang: "zh-CN",
        slow: false,
        timeout: 10000,
        splitPunct: "，。、；！？",
      });
      base64 = segments[0]?.base64 ?? "";
      if (!base64) throw new Error("No audio");
    }
    const buf = Buffer.from(base64, "base64");
    return new NextResponse(buf, {
      headers: { "Content-Type": "audio/mpeg" },
    });
  } catch {
    return NextResponse.json(
      { detail: "Audio not available; try again or use browser play." },
      { status: 501 }
    );
  }
}
