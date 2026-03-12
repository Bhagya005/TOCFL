"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clearToken } from "@/lib/api";
import { useSidebar } from "@/context/SidebarContext";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/flashcards", label: "Flashcards", icon: "🃏" },
  { href: "/tests", label: "Tests", icon: "📋" },
  { href: "/weak-words", label: "Weak Words", icon: "⚠️" },
  { href: "/word-bank", label: "Word Bank", icon: "📚" },
  { href: "/leaderboard", label: "Leaderboard", icon: "🏆" },
  { href: "/progress", label: "Progress", icon: "📈" },
];

export default function Sidebar({ username }: { username: string }) {
  const pathname = usePathname();
  const { collapsed, setCollapsed, mobileOpen, setMobileOpen } = useSidebar();

  const closeMobile = () => setMobileOpen(false);

  return (
    <>
      {/* Desktop: always visible. Mobile: slide-out drawer, hidden by default */}
      <aside
        className={`
          fixed left-0 top-0 z-50 flex h-screen flex-col border-r border-slate-700/50 bg-slate-800/95 shadow-card
          transition-[transform,width] duration-300 ease-in-out
          w-72
          ${mobileOpen ? "translate-x-0" : "-translate-x-full"}
          md:translate-x-0
          ${collapsed ? "md:w-[4.5rem]" : "md:w-56"}
        `}
      >
        <div className="flex h-14 shrink-0 items-center justify-between border-b border-slate-700/50 px-3">
          {(!collapsed || mobileOpen) && (
            <span className="truncate text-sm font-semibold text-slate-100">
              TOCFL A1
            </span>
          )}
          <div className="flex items-center gap-1">
            {/* Mobile: close button. Desktop: collapse toggle */}
            <button
              type="button"
              onClick={() => { if (mobileOpen) closeMobile(); else setCollapsed(!collapsed); }}
              className="rounded-button p-2.5 text-slate-400 hover:bg-slate-700/50 hover:text-slate-100 min-w-[44px] min-h-[44px] md:min-w-0 md:min-h-0 flex items-center justify-center"
              aria-label={mobileOpen ? "Close menu" : collapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {mobileOpen ? "✕" : collapsed ? "→" : "←"}
            </button>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto py-4">
          <ul className="space-y-0.5 px-2">
            {navItems.map(({ href, label, icon }) => {
              const isActive =
                href === "/tests" ? pathname.startsWith("/tests") : pathname === href;
              return (
                <li key={href}>
                  <Link
                    href={href}
                    onClick={closeMobile}
                    className={`
                      flex items-center gap-3 rounded-button px-3 py-3 text-sm font-medium transition-colors min-h-[44px]
                      ${isActive
                        ? "bg-amber-500/20 text-amber-400"
                        : "text-slate-300 hover:bg-slate-700/50 hover:text-slate-100"
                      }
                      ${collapsed && !mobileOpen ? "justify-center px-2" : ""}
                    `}
                    title={collapsed && !mobileOpen ? label : undefined}
                  >
                    <span className="text-lg leading-none shrink-0" aria-hidden>{icon}</span>
                    {(!collapsed || mobileOpen) && <span>{label}</span>}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        <div
          className={`
        border-t border-slate-700/50 p-3
        ${collapsed && !mobileOpen ? "flex flex-col items-center gap-2" : "space-y-2"}
      `}
        >
          {(!collapsed || mobileOpen) && (
            <p className="truncate text-xs text-slate-500">
              Logged in as <strong className="text-slate-400">{username}</strong>
            </p>
          )}
          <button
            type="button"
            onClick={() => {
              clearToken();
              window.location.href = "/login";
            }}
            className={`
            text-sm text-slate-400 hover:text-slate-100 min-h-[44px] min-w-[44px] md:min-w-0 md:min-h-0
            ${collapsed && !mobileOpen ? "rounded-button p-2 hover:bg-slate-700/50 flex items-center justify-center" : "w-full text-left py-2"}
          `}
          >
            {collapsed && !mobileOpen ? "⎋" : "Log out"}
          </button>
        </div>
      </aside>
    </>
  );
}
