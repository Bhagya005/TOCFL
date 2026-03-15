"use client";

import { useSearchParams } from "next/navigation";

export default function LoginSessionMessage() {
  const searchParams = useSearchParams();
  if (searchParams.get("reason") !== "session") return null;
  return (
    <p className="text-amber-400 text-sm text-center mb-4">
      Your session expired or you weren&apos;t logged in. Please log in again.
    </p>
  );
}
