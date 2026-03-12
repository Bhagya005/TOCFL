"use client";

import type { ReactNode } from "react";

type QuizCardProps = {
  title: string;
  questionProgress: string;
  progressPercent: number;
  children: ReactNode;
  footer: ReactNode;
};

export default function QuizCard({
  title,
  questionProgress,
  progressPercent,
  children,
  footer,
}: QuizCardProps) {
  return (
    <div className="max-w-2xl mx-auto w-full min-w-0">
      <div className="mb-4 md:mb-6">
        <h1 className="text-xl sm:text-2xl font-bold text-slate-100 mb-2 break-words">{title}</h1>
        <p className="text-slate-400 text-sm mb-3">{questionProgress}</p>
        <div className="h-2 rounded-full bg-slate-700 overflow-hidden">
          <div
            className="h-full bg-amber-500 rounded-full transition-all duration-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>
      <div className="card p-4 sm:p-6 md:p-8 mb-4 md:mb-6 min-h-[180px] md:min-h-[200px] flex flex-col justify-center">
        {children}
      </div>
      <div className="flex flex-col-reverse sm:flex-row gap-3 sm:gap-4 sm:justify-between">
        {footer}
      </div>
    </div>
  );
}
