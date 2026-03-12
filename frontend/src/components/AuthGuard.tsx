"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, type User } from "@/lib/api";
import { UserProvider } from "@/context/UserContext";
import { SidebarProvider, useSidebar } from "@/context/SidebarContext";
import Sidebar from "./Sidebar";
import LoadingSpinner from "./ui/LoadingSpinner";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<User>("/api/me")
      .then(setUser)
      .catch(() => router.replace("/login"))
      .finally(() => setLoading(false));
  }, [router]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }
  if (!user) return null;
  return (
    <UserProvider user={user}>
      <SidebarProvider>
        <div className="flex min-h-screen overflow-x-hidden">
          <Sidebar username={user.username} />
          {/* Mobile backdrop: tap to close drawer */}
          <Backdrop />
          <MainContent>{children}</MainContent>
        </div>
      </SidebarProvider>
    </UserProvider>
  );
}

function Backdrop() {
  const { mobileOpen, setMobileOpen } = useSidebar();
  return (
    <button
      type="button"
      aria-label="Close menu"
      onClick={() => setMobileOpen(false)}
      className={`
        fixed inset-0 z-40 bg-black/50 transition-opacity duration-300 md:hidden
        ${mobileOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"}
      `}
      tabIndex={mobileOpen ? 0 : -1}
    />
  );
}

function MainContent({ children }: { children: React.ReactNode }) {
  const { collapsed, setMobileOpen } = useSidebar();
  return (
    <main
      className={`
        flex-1 min-h-screen transition-[margin] duration-300
        ml-0
        ${collapsed ? "md:ml-[4.5rem]" : "md:ml-56"}
      `}
    >
      {/* Mobile: sticky header with hamburger */}
      <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-slate-700/50 bg-slate-900/95 px-4 md:hidden">
        <button
          type="button"
          onClick={() => setMobileOpen(true)}
          className="flex h-11 min-h-[44px] w-11 min-w-[44px] items-center justify-center rounded-button text-slate-300 hover:bg-slate-700/50 hover:text-slate-100"
          aria-label="Open menu"
        >
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <span className="text-sm font-semibold text-slate-200 truncate">TOCFL A1</span>
      </header>
      <div className="p-3 sm:p-4 md:p-6 lg:p-8 xl:p-10 max-w-6xl mx-auto w-full min-w-0">{children}</div>
    </main>
  );
}
