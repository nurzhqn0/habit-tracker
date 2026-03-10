"use client";

import Link from "next/link";
import { getBestStreak, getCurrentStreak, isHabitDoneOnDate, todayKey } from "../../lib/habit-utils";
import type { Habit, HabitUnit } from "../../types/habit";

type HabitListItemProps = {
  habit: Habit;
};

const unitLabels: Record<HabitUnit, string> = {
  boolean: "True/False",
  liters: "Liters",
  pages: "Pages",
  minutes: "Minutes",
};

export default function HabitListItem({ habit }: HabitListItemProps) {
  const currentStreak = getCurrentStreak(habit);
  const bestStreak = getBestStreak(habit);
  const doneToday = isHabitDoneOnDate(habit, todayKey());

  return (
    <Link
      href={`/dashboard/habits/${habit.id}`}
      className="block rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-slate-900">{habit.name}</h3>
          <p className="mt-1 text-xs text-slate-500">Unit: {unitLabels[habit.unit]}</p>
        </div>
        <span
          className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${
            doneToday ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"
          }`}
        >
          {doneToday ? "Done today" : "Not done today"}
        </span>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
        <div className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-2">
          <p className="text-slate-500">Current streak</p>
          <p className="mt-0.5 text-lg font-bold text-slate-900">{currentStreak}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-2">
          <p className="text-slate-500">Best streak</p>
          <p className="mt-0.5 text-lg font-bold text-slate-900">{bestStreak}</p>
        </div>
      </div>
    </Link>
  );
}
