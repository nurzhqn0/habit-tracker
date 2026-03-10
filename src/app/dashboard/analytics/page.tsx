"use client";

import AnalyticsSection from "../../../components/dashboard/AnalyticsSection";
import { useHabits } from "../../../hooks/useHabits";

export default function AnalyticsPage() {
  const { habits, isReady } = useHabits();

  if (!isReady) {
    return <div className="grid min-h-[35vh] place-items-center text-slate-600">Loading analytics...</div>;
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Analytics</h1>
        <p className="mt-1 text-sm text-slate-500">Separate analytics page for all existing habits.</p>
      </div>
      <AnalyticsSection habits={habits} />
    </div>
  );
}
