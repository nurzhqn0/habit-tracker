"use client";

import { Button } from "@radix-ui/themes";
import { useState } from "react";
import CreateHabitModal from "../../../components/dashboard/CreateHabitModal";
import HabitListItem from "../../../components/dashboard/HabitListItem";
import { useHabits } from "../../../hooks/useHabits";
import type { NewHabitInput } from "../../../types/habit";

export default function HabitsPage() {
  const { habits, isReady, addHabit } = useHabits();
  const [openCreateModal, setOpenCreateModal] = useState(false);

  const onCreateHabit = (input: NewHabitInput) => {
    addHabit(input);
  };

  if (!isReady) {
    return <div className="grid min-h-[35vh] place-items-center text-slate-600">Loading habits...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Habits</h1>
          <p className="mt-1 text-sm text-slate-500">
            Manage habits here. Click any habit to open its dashboard detail and progress.
          </p>
        </div>

        <Button radius="full" onClick={() => setOpenCreateModal(true)}>
          + Create habit
        </Button>
      </div>

      {habits.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-slate-500">
          No habits yet. Use <strong>Create habit</strong> to get started.
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {habits.map((habit) => (
            <HabitListItem key={habit.id} habit={habit} />
          ))}
        </div>
      )}

      <CreateHabitModal open={openCreateModal} onOpenChange={setOpenCreateModal} onCreateHabit={onCreateHabit} />
    </div>
  );
}
