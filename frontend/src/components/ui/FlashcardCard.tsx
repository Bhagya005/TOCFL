"use client";

import AudioButton from "./AudioButton";

export type FlashcardWord = {
  id: number;
  character: string;
  pinyin: string;
  meaning: string;
  example_sentence?: string;
  example_pinyin?: string;
  example_translation?: string;
};

type FlashcardCardProps = {
  word: FlashcardWord;
  flipped: boolean;
  onFlip: () => void;
  onKnew: () => void;
  onDidNotKnow: () => void;
  onReset?: () => void;
};

export default function FlashcardCard({
  word,
  flipped,
  onFlip,
  onKnew,
  onDidNotKnow,
  onReset,
}: FlashcardCardProps) {
  return (
    <div className="flip-root w-full max-w-2xl mx-auto px-0 sm:px-2">
      <div className={`flip-inner ${flipped ? "flipped" : ""}`}>
        {/* Front — Chinese character as clear focal point */}
        <div className="flip-front card min-h-[280px] md:min-h-[320px] flex flex-col items-center justify-center p-4 sm:p-6 md:p-8">
          <p className="text-6xl sm:text-7xl md:text-8xl font-bold text-center text-slate-100 break-all leading-tight">
            {word.character}
          </p>
        </div>
        {/* Back */}
        <div className="flip-back card min-h-[280px] md:min-h-[320px] flex flex-col items-center justify-center p-4 sm:p-6 md:p-8">
          <div className="flex items-center gap-3 mb-3 flex-wrap justify-center">
            <AudioButton text={word.character} />
            <p className="text-4xl sm:text-5xl md:text-6xl font-bold text-slate-100 break-all text-center">
              {word.character}
            </p>
          </div>
          <p className="text-lg sm:text-xl md:text-2xl font-medium text-slate-300 mb-2 text-center break-words max-w-full">
            {word.pinyin} · {word.meaning}
          </p>
          {word.example_sentence && (
            <div className="mt-4 md:mt-5 w-full max-w-full text-center">
              {/* ▶ Chinese sentence — play button inline first */}
              <div className="flex flex-wrap items-center justify-center gap-2 gap-y-1">
                <AudioButton text={word.example_sentence} className="h-10 w-10 shrink-0" />
                <p className="text-xl sm:text-2xl font-semibold text-slate-200 break-words">
                  {word.example_sentence}
                </p>
              </div>
              {word.example_pinyin && (
                <p className="text-lg sm:text-xl font-semibold text-slate-400 mt-3 break-words px-1">
                  {word.example_pinyin}
                </p>
              )}
              {word.example_translation && (
                <p className="text-base sm:text-lg font-semibold text-slate-500 mt-2 break-words px-1">
                  {word.example_translation}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
      {/* Buttons: full-width stacked on mobile, row on desktop */}
      <div className="flex flex-col sm:flex-row flex-wrap gap-3 sm:justify-center mt-4 sm:mt-6">
        <button type="button" onClick={onFlip} className="btn-secondary w-full sm:w-auto">
          Flip
        </button>
        <button type="button" onClick={onKnew} className="btn-primary w-full sm:w-auto">
         Yes
        </button>
        <button type="button" onClick={onDidNotKnow} className="btn-secondary w-full sm:w-auto">
          No
        </button>
      </div>
      {onReset && (
        <div className="flex justify-center mt-4">
          <button
            type="button"
            onClick={onReset}
            className="text-base font-medium text-slate-500 hover:text-slate-300 min-h-[44px] px-4 py-2"
          >
            Reset session
          </button>
        </div>
      )}
    </div>
  );
}
