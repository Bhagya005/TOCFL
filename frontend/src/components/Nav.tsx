"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clearToken } from "@/lib/api";

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/flashcards", label: "Today's Flashcards" },
  { href: "/tests", label: "Tests" },
  { href: "/weak-words", label: "Weak Words" },
  { href: "/leaderboard", label: "Leaderboard" },
  { href: "/word-bank", label: "Word Bank" },
  { href: "/progress", label: "Progress" },
];

export default function Nav({ username }: { username: string }) {
  const pathname = usePathname();
  return (
    <nav className="flex flex-col gap-2 border-b border-gray-700 pb-4 mb-6">
      <div className="flex flex-wrap items-center gap-4">
        {links.map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            className={pathname === href ? "text-amber-400 font-medium" : "text-gray-300 hover:text-white"}
          >
            {label}
          </Link>
        ))}
      </div>
      <div className="flex items-center justify-between text-sm text-gray-500">
        <span>Logged in as <strong>{username}</strong></span>
        <button
          type="button"
          onClick={() => {
            clearToken();
            window.location.href = "/login";
          }}
          className="text-gray-400 hover:text-white"
        >
          Log out
        </button>
      </div>
    </nav>
  );
}
