export default function LoadingSpinner({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const sizeClass =
    size === "sm" ? "h-6 w-6 border-2" : size === "lg" ? "h-12 w-12 border-4" : "h-10 w-10 border-2";
  return (
    <div
      className={`animate-spin rounded-full border-slate-600 border-t-amber-500 ${sizeClass}`}
      role="status"
      aria-label="Loading"
    />
  );
}
