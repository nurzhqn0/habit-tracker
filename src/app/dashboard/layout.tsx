"use client";

import { Button } from "@radix-ui/themes";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect } from "react";
import { useAuth } from "../../hooks/useAuth";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { isReady, isLoggedIn, email, logout } = useAuth();

  useEffect(() => {
    if (isReady && !isLoggedIn) {
      router.replace("/?login=1");
    }
  }, [isReady, isLoggedIn, router]);

  const onLogout = () => {
    logout();
    router.replace("/");
  };

  if (!isReady) {
    return <div className="grid min-h-screen place-items-center text-slate-600">Preparing dashboard...</div>;
  }

  if (!isLoggedIn) {
    return null;
  }

  const habitsActive = pathname.startsWith("/dashboard/habits");
  const analyticsActive = pathname.startsWith("/dashboard/analytics");

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto flex w-full max-w-[1440px]">
        <aside className="sticky top-0 hidden h-screen w-72 shrink-0 border-r border-slate-200 bg-white lg:flex lg:flex-col">
          <div className="border-b border-slate-200 px-5 py-5">
            <Link href="/" className="text-lg font-bold tracking-tight text-slate-900 no-underline">
              HabitFlow
            </Link>
            <p className="mt-2 text-xs text-slate-500">Focus on consistency, not complexity.</p>
          </div>

          <nav className="px-3 py-4">
            <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">Sections</p>
            <div className="space-y-1">
              <Link
                href="/dashboard/habits"
                className={`block rounded-lg px-3 py-2 text-sm font-medium ${
                  habitsActive ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
                }`}
              >
                Habits
              </Link>
              <Link
                href="/dashboard/analytics"
                className={`block rounded-lg px-3 py-2 text-sm font-medium ${
                  analyticsActive ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
                }`}
              >
                Analytics
              </Link>
            </div>
          </nav>
        </aside>

        <div className="min-w-0 flex-1">
          <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
            <div className="flex items-center justify-between gap-3 px-4 py-4 sm:px-6 lg:px-8">
              <div>
                <p className="text-lg font-semibold text-slate-900">Dashboard</p>
                <p className="text-xs text-slate-500">{email}</p>
              </div>

              <div className="flex items-center gap-2">
                <div className="rounded-lg border border-slate-200 p-1 lg:hidden">
                  <Link
                    href="/dashboard/habits"
                    className={`rounded px-2 py-1 text-xs font-medium ${
                      habitsActive ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
                    }`}
                  >
                    Habits
                  </Link>
                  <Link
                    href="/dashboard/analytics"
                    className={`rounded px-2 py-1 text-xs font-medium ${
                      analyticsActive ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
                    }`}
                  >
                    Analytics
                  </Link>
                </div>
                <Button variant="soft" color="gray" radius="full" onClick={onLogout}>
                  Logout
                </Button>
              </div>
            </div>
          </header>

          <main className="px-4 py-5 sm:px-6 lg:px-8">{children}</main>
        </div>
      </div>
    </div>
  );
}
