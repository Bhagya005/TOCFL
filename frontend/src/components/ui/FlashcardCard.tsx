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
        {/* Front */}
        <div className="flip-front card min-h-[280px] md:min-h-[320px] flex flex-col items-center justify-center p-4 sm:p-6 md:p-8">
          <p className="text-5xl sm:text-6xl md:text-7xl font-bold text-center text-slate-100 break-all">
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
          <p className="text-base sm:text-lg md:text-xl text-slate-400 mb-2 text-center break-words max-w-full">
            {word.pinyin} · {word.meaning}
          </p>
          {word.example_sentence && (
            <div className="mt-3 md:mt-4 text-center w-full max-w-full">
              <p className="text-base sm:text-lg text-slate-300 break-words px-1">
                {word.example_sentence}
              </p>
              {word.example_pinyin && (
                <p className="text-sm sm:text-base text-slate-400 mt-1 break-words px-1">
                  {word.example_pinyin}
                </p>
              )}
              {word.example_translation && (
                <p className="text-xs sm:text-sm text-slate-500 mt-1 break-words px-1">
                  {word.example_translation}
                </p>
              )}
              <div className="mt-2">
                <AudioButton text={word.example_sentence} />
              </div>
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
          I knew this
        </button>
        <button type="button" onClick={onDidNotKnow} className="btn-secondary w-full sm:w-auto">
          I didn&apos;t know
        </button>
      </div>
      {onReset && (
        <div className="flex justify-center mt-4">
          <button
            type="button"
            onClick={onReset}
            className="text-sm text-slate-500 hover:text-slate-300 min-h-[44px] px-4 py-2"
          >
            Reset session
          </button>
        </div>
      )}
    </div>
  );
}
