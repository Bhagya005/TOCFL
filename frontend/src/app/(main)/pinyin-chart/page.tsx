"use client";

export default function PinyinChartPage() {
  return (
    <main className="flex flex-1 flex-col min-h-0 min-w-0 overflow-auto">
      <h1 className="text-xl sm:text-2xl font-semibold text-slate-100 mb-4 shrink-0">
        Pinyin Chart
      </h1>
      <div className="w-full min-w-0 rounded-card bg-slate-800/50 border border-slate-700/50 overflow-hidden min-h-[80vh]">
        <iframe
          src="https://chinese.yabla.com/chinese-pinyin-chart.php"
          width="100%"
          height={900}
          style={{ border: "none" }}
          className="w-full min-h-[80vh]"
          title="Yabla Chinese Pinyin Chart"
        />
      </div>
    </main>
  );
}
