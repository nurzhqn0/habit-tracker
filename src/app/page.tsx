"use client";

import { Button } from "@radix-ui/themes";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";
import AuthModal from "../components/auth/AuthModal";
import { useAuth } from "../hooks/useAuth";
import styles from "./page.module.css";

function HomePageContent() {
  const { isReady, isLoggedIn } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    setModalOpen(searchParams.get("login") === "1");
  }, [searchParams]);

  const onModalOpenChange = useCallback(
    (open: boolean) => {
      setModalOpen(open);
      const params = new URLSearchParams(searchParams.toString());

      if (open) {
        params.set("login", "1");
      } else {
        params.delete("login");
      }

      const query = params.toString();
      router.replace(query ? `${pathname}?${query}` : pathname, {
        scroll: false,
      });
    },
    [pathname, router, searchParams],
  );

  return (
    <div className={`${styles.page} min-h-screen grid grid-rows-[1fr_auto]`}>
      <main className="relative isolate overflow-hidden">
        <div className={styles.bgGlowTop} />
        <div className={styles.bgGlowBottom} />

        <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
          <header
            className={`${styles.fadeIn} flex items-center justify-between py-4`}
          >
            <p
              className="text-base font-bold tracking-tight text-slate-900"
              style={{
                fontFamily: '"Sora", "Avenir Next", "Segoe UI", sans-serif',
              }}
            >
              HabitFlow
            </p>
            <div>
              {!isReady ? null : isLoggedIn ? (
                <Button asChild radius="full">
                  <Link href="/dashboard">Dashboard</Link>
                </Button>
              ) : (
                <Button radius="full" onClick={() => onModalOpenChange(true)}>
                  Login
                </Button>
              )}
            </div>
          </header>

          <section className="mt-6 grid items-center gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:gap-12">
            <div className={styles.fadeInUp}>
              <p className="mb-4 inline-flex rounded-full border border-cyan-200 bg-cyan-50 px-4 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-700">
                Daily Habit Engine
              </p>
              <h1
                className="text-5xl leading-[0.96] font-bold tracking-tight text-slate-900 sm:text-6xl lg:text-7xl"
                style={{
                  fontFamily: '"Sora", "Avenir Next", "Segoe UI", sans-serif',
                }}
              >
                Make consistency visible.
              </h1>
              <p className="mt-6 max-w-xl text-lg leading-8 text-slate-600">
                HabitFlow turns goals into measurable daily actions. Track
                water, pages, minutes, and check-off habits in one clean
                dashboard.
              </p>

              <div className="mt-8 flex flex-wrap items-center gap-3">
                {!isReady ? null : isLoggedIn ? (
                  <Button asChild size="3" radius="full">
                    <Link href="/dashboard">Open Dashboard</Link>
                  </Button>
                ) : (
                  <Button
                    size="3"
                    radius="full"
                    onClick={() => onModalOpenChange(true)}
                  >
                    Login
                  </Button>
                )}
                <span className="text-sm text-slate-500">
                  No backend yet. Auth is cookie-based demo mode.
                </span>
              </div>

              <div className="mt-10 grid grid-cols-3 gap-3 sm:gap-4">
                <div className={`${styles.metricCard} ${styles.staggerOne}`}>
                  <p className="text-xs uppercase tracking-wider text-slate-500">
                    Streak focus
                  </p>
                  <p className="mt-2 text-2xl font-bold text-slate-900">21d</p>
                </div>
                <div className={`${styles.metricCard} ${styles.staggerTwo}`}>
                  <p className="text-xs uppercase tracking-wider text-slate-500">
                    Daily units
                  </p>
                  <p className="mt-2 text-2xl font-bold text-slate-900">
                    4 types
                  </p>
                </div>
                <div className={`${styles.metricCard} ${styles.staggerThree}`}>
                  <p className="text-xs uppercase tracking-wider text-slate-500">
                    Completion
                  </p>
                  <p className="mt-2 text-2xl font-bold text-slate-900">84%</p>
                </div>
              </div>
            </div>

            <div className={`${styles.panelWrap} ${styles.fadeInUpDelayed}`}>
              <article className={styles.panel}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-slate-500">Today</p>
                    <h2
                      className="mt-1 text-2xl font-semibold text-slate-900"
                      style={{
                        fontFamily:
                          '"Sora", "Avenir Next", "Segoe UI", sans-serif',
                      }}
                    >
                      Habit Snapshot
                    </h2>
                  </div>
                  <span className={styles.liveDot}>Live</span>
                </div>

                <div className="mt-6 space-y-3">
                  <div className={styles.habitRow}>
                    <span>Water intake</span>
                    <strong>2 / 2 L</strong>
                  </div>
                  <div className={styles.habitRow}>
                    <span>Read pages</span>
                    <strong>18 / 20</strong>
                  </div>
                  <div className={styles.habitRow}>
                    <span>Workout</span>
                    <strong>Done</strong>
                  </div>
                  <div className={styles.habitRow}>
                    <span>Focus minutes</span>
                    <strong>35 / 45</strong>
                  </div>
                </div>
              </article>
            </div>
          </section>
        </div>
      </main>

      <footer className="border-t border-slate-200/80 bg-white/70 px-4 py-5 text-center text-sm text-slate-600 backdrop-blur">
        devhouse.kz @2026
      </footer>

      <AuthModal open={modalOpen} onOpenChange={onModalOpenChange} />
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-50" />}>
      <HomePageContent />
    </Suspense>
  );
}
