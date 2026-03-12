type StatCardProps = {
  title: string;
  value: string | number;
  icon: string;
  subtitle?: string;
};

export default function StatCard({ title, value, icon, subtitle }: StatCardProps) {
  return (
    <div className="card p-4 md:p-6 transition-shadow hover:shadow-cardHover min-w-0">
      <div className="flex items-start justify-between gap-3 md:gap-4">
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-400 mb-1">{title}</p>
          <p className="text-xl sm:text-2xl md:text-3xl font-bold text-slate-100 tracking-tight">{value}</p>
          {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
        </div>
        <span className="text-3xl opacity-80" aria-hidden>{icon}</span>
      </div>
    </div>
  );
}
