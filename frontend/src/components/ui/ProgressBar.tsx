type ProgressBarProps = {
  current: number;
  total: number;
  label?: string;
};

export default function ProgressBar({ current, total, label }: ProgressBarProps) {
  const percent = total > 0 ? Math.min(100, (current / total) * 100) : 0;
  return (
    <div className="w-full">
      {label != null && (
        <p className="text-base font-medium text-slate-400 mb-2">{label}</p>
      )}
      <div className="h-2 rounded-full bg-slate-700 overflow-hidden">
        <div
          className="h-full bg-amber-500 rounded-full transition-all duration-300"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
