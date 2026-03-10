"use client";

import { Button } from "@radix-ui/themes";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import HabitCard from "../../../../components/dashboard/HabitCard";
import { useHabits } from "../../../../hooks/useHabits";

export default function HabitDetailsPage() {
  const router = useRouter();
  const params = useParams<{ habitId: string }>();
  const habitId = params.habitId;

  const { habits, isReady, removeHabit, toggleDone, updateProgress } = useHabits();
  const habit = habits.find((item) => item.id === habitId);

  if (!isReady) {
    return <div className="grid min-h-[35vh] place-items-center text-slate-600">Loading habit details...</div>;
  }

  if (!habit) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6">
        <h1 className="text-xl font-semibold text-slate-900">Habit not found</h1>
        <p className="mt-2 text-sm text-slate-500">This habit may have been removed.</p>
        <Button asChild className="mt-4">
          <Link href="/dashboard/habits">Back to habits</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{habit.name}</h1>
          <p className="mt-1 text-sm text-slate-500">Habit detail dashboard with streaks, calendar, and daily progress.</p>
        </div>
        <Button asChild variant="soft" color="gray" radius="full">
          <Link href="/dashboard/habits">Back to list</Link>
        </Button>
      </div>

      <HabitCard
        habit={habit}
        onRemove={(id) => {
          removeHabit(id);
          router.replace("/dashboard/habits");
        }}
        onToggleDone={toggleDone}
        onUpdateProgress={updateProgress}
      />
    </div>
  );
}
