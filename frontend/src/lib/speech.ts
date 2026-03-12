/**
 * Browser Speech Synthesis fallback when /api/audio is unavailable (e.g. on Vercel).
 * Uses the Web Speech API with Chinese (zh-CN) when supported.
 */
export function playWithSpeechSynthesis(
  text: string,
  lang: string = "zh-CN"
): Promise<void> {
  return new Promise((resolve, reject) => {
    if (!text?.trim()) {
      reject(new Error("No text"));
      return;
    }
    if (typeof window === "undefined" || !window.speechSynthesis) {
      reject(new Error("Speech not supported"));
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text.trim());
    utterance.lang = lang;
    utterance.onend = () => resolve();
    utterance.onerror = () => reject(new Error("Speech failed"));
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  });
}

export function isSpeechSynthesisSupported(): boolean {
  return typeof window !== "undefined" && !!window.speechSynthesis;
}
