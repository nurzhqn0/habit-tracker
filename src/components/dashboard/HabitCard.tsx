"use client";

import { Button, Text, TextField } from "@radix-ui/themes";
import { useMemo, useState } from "react";
import {
  formatDateReadable,
  formatTimestamp,
  getBestStreak,
  getCurrentStreak,
  getLogForDate,
  isHabitDoneOnDate,
  todayKey,
} from "../../lib/habit-utils";
import type { Habit, HabitUnit } from "../../types/habit";
import HabitCalendar from "./HabitCalendar";

type HabitCardProps = {
  habit: Habit;
  onRemove: (habitId: string) => void;
  onToggleDone: (habitId: string, dateKey: string) => void;
  onUpdateProgress: (habitId: string, dateKey: string, progress: number) => void;
};

const unitLabels: Record<HabitUnit, string> = {
  boolean: "True/False",
  liters: "L",
  pages: "Pages",
  minutes: "Minutes",
};

function getProgressPercent(habit: Habit, dateKey: string): number {
  const log = habit.logs[dateKey];
  if (habit.unit === "boolean") {
    return log?.done ? 100 : 0;
  }

  const target = habit.target ?? 0;
  const progress = log?.progress ?? 0;
  if (target <= 0) {
    return log?.done ? 100 : 0;
  }

  return Math.min(100, Math.max(0, Math.round((progress / target) * 100)));
}

export default function HabitCard({ habit, onRemove, onToggleDone, onUpdateProgress }: HabitCardProps) {
  const [selectedDate, setSelectedDate] = useState(todayKey());
  const log = getLogForDate(habit.logs, selectedDate, habit.unit === "boolean");
  const isDone = isHabitDoneOnDate(habit, selectedDate);
  const currentStreak = useMemo(() => getCurrentStreak(habit), [habit]);
  const bestStreak = useMemo(() => getBestStreak(habit), [habit]);
  const progressPercent = getProgressPercent(habit, selectedDate);

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">{habit.name}</h3>
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-1 text-slate-600">
              Unit: {unitLabels[habit.unit]}
            </span>
            <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-1 text-slate-600">
              Start: {formatDateReadable(habit.startDate)}
            </span>
            <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-1 text-slate-600">
              Created: {formatTimestamp(habit.createdAt)}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold ${
              isDone ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"
            }`}
          >
            {isDone ? "Done" : "Not done"}
          </span>
          <Button variant="soft" color="red" radius="full" onClick={() => onRemove(habit.id)}>
            Delete
          </Button>
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Current streak</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">{currentStreak}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Best streak</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">{bestStreak}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Selected day</p>
          <p className="mt-1 text-sm font-semibold text-slate-800">{formatDateReadable(selectedDate)}</p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-end gap-3">
        <label className="grid gap-1">
          <Text size="2" weight="medium">
            Active date
          </Text>
          <TextField.Root type="date" value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)} />
        </label>

        {habit.unit !== "boolean" ? (
          <label className="grid gap-1">
            <Text size="2" weight="medium">
              Progress / Target
            </Text>
            <TextField.Root
              type="number"
              min="0"
              step={habit.unit === "liters" ? "0.1" : "1"}
              value={log.progress ?? 0}
              onChange={(event) => onUpdateProgress(habit.id, selectedDate, Number(event.target.value))}
            />
            <Text size="1" color="gray">
              {(log.progress ?? 0).toString()} / {(habit.target ?? 0).toString()} {unitLabels[habit.unit]}
            </Text>
          </label>
        ) : null}

        <Button radius="full" variant="soft" onClick={() => onToggleDone(habit.id, selectedDate)}>
          {isDone ? "Mark not done" : "Mark done"}
        </Button>
      </div>

      {habit.unit !== "boolean" ? (
        <div className="mt-3">
          <div className="mb-1 flex items-center justify-between text-xs text-slate-600">
            <span>Progress</span>
            <span>{progressPercent}%</span>
          </div>
          <div className="h-2 rounded-full bg-slate-200">
            <div className="h-2 rounded-full bg-cyan-500 transition-all" style={{ width: `${progressPercent}%` }} />
          </div>
        </div>
      ) : null}

      <div className="mt-4">
        <HabitCalendar habit={habit} selectedDateKey={selectedDate} onSelectDate={setSelectedDate} />
      </div>
    </article>
  );
}
