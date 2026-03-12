type EmptyStateProps = {
  title: string;
  description?: string;
  icon?: string;
  action?: React.ReactNode;
};

export default function EmptyState({ title, description, icon = "📭", action }: EmptyStateProps) {
  return (
    <div className="card flex flex-col items-center justify-center rounded-card py-16 px-6 text-center">
      <span className="text-4xl mb-4" aria-hidden>{icon}</span>
      <h3 className="text-xl font-semibold text-slate-200 mb-1">{title}</h3>
      {description && <p className="text-slate-400 text-base font-medium max-w-sm mb-6">{description}</p>}
      {action}
    </div>
  );
}
