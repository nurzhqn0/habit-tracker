"use client";

import { useMemo, useState } from "react";
import { isHabitDoneOnDate, parseDateKey, toDateKey, todayKey } from "../../lib/habit-utils";
import type { Habit } from "../../types/habit";

type AnalyticsSectionProps = {
  habits: Habit[];
};

type WeeklyDayStats = {
  dateKey: string;
  doneCount: number;
  anyDone: boolean;
  completionRate: number;
};

function formatValueByUnit(unit: Habit["unit"], value: number): string {
  if (unit === "liters") {
    return `${value.toFixed(1)} L`;
  }

  if (unit === "minutes") {
    return `${Math.round(value)} min`;
  }

  if (unit === "pages") {
    return `${Math.round(value)} pages`;
  }

  return `${Math.round(value)} days`;
}

function getWeekDatesMondayToSunday(referenceDateKey: string): string[] {
  const referenceDate = parseDateKey(referenceDateKey) ?? new Date();
  const weekday = (referenceDate.getDay() + 6) % 7;

  const monday = new Date(referenceDate);
  monday.setDate(referenceDate.getDate() - weekday);

  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date(monday);
    date.setDate(monday.getDate() + index);
    return toDateKey(date);
  });
}

function shiftDateKeyByDays(baseDateKey: string, shiftDays: number): string {
  const baseDate = parseDateKey(baseDateKey) ?? new Date();
  baseDate.setDate(baseDate.getDate() + shiftDays);
  return toDateKey(baseDate);
}

export default function AnalyticsSection({ habits }: AnalyticsSectionProps) {
  const today = todayKey();
  const [weekOffset, setWeekOffset] = useState(0);
  const referenceDateKey = useMemo(() => shiftDateKeyByDays(today, weekOffset * 7), [today, weekOffset]);
  const weekDates = useMemo(() => getWeekDatesMondayToSunday(referenceDateKey), [referenceDateKey]);
  const weekdayLabels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const totalHabits = habits.length;
  const isCurrentWeek = weekOffset === 0;
  const activeWeekDates = isCurrentWeek ? weekDates.filter((dateKey) => dateKey <= today) : weekDates;

  const statsByDate: Record<string, WeeklyDayStats> = {};
  for (const dateKey of weekDates) {
    statsByDate[dateKey] = {
      dateKey,
      doneCount: 0,
      anyDone: false,
      completionRate: 0,
    };
  }

  let totalDoneInWeek = 0;
  const habitsCompletedThisWeek = new Set<string>();

  for (const habit of habits) {
    for (const dateKey of weekDates) {
      const log = habit.logs[dateKey];
      if (!log) {
        continue;
      }

      if (isHabitDoneOnDate(habit, dateKey)) {
        totalDoneInWeek += 1;
        statsByDate[dateKey].doneCount += 1;
        statsByDate[dateKey].anyDone = true;
        habitsCompletedThisWeek.add(habit.id);
      }
    }
  }

  for (const dateKey of weekDates) {
    statsByDate[dateKey].completionRate =
      totalHabits === 0 ? 0 : Math.round((statsByDate[dateKey].doneCount / totalHabits) * 100);
  }

  let streakOfDays = 0;
  for (let index = weekDates.length - 1; index >= 0; index -= 1) {
    const dateKey = weekDates[index];
    if (isCurrentWeek && dateKey > today) {
      continue;
    }

    if (statsByDate[dateKey].anyDone) {
      streakOfDays += 1;
    } else {
      break;
    }
  }

  const fullCompletionDays = activeWeekDates.filter((dateKey) => {
    if (totalHabits === 0) {
      return false;
    }

    return statsByDate[dateKey].doneCount === totalHabits;
  }).length;

  const completedHabitsCount = habitsCompletedThisWeek.size;
  const notCompletedHabitsCount = Math.max(0, totalHabits - completedHabitsCount);
  const elapsedWeekDays = activeWeekDates.length;

  const habitTotals = habits.map((habit) => {
    const doneDays = weekDates.reduce((sum, dateKey) => sum + (isHabitDoneOnDate(habit, dateKey) ? 1 : 0), 0);
    const progressTotal = weekDates.reduce((sum, dateKey) => sum + (habit.logs[dateKey]?.progress ?? 0), 0);

    return {
      id: habit.id,
      name: habit.name,
      unit: habit.unit,
      doneDays,
      progressTotal,
    };
  });

  const sortedHabitTotals = [...habitTotals].sort((left, right) => {
    const leftValue = left.unit === "boolean" ? left.doneDays : left.progressTotal;
    const rightValue = right.unit === "boolean" ? right.doneDays : right.progressTotal;
    return rightValue - leftValue;
  });

  return (
    <section
      id="analytics"
      className="rounded-3xl border border-slate-200 bg-gradient-to-b from-white to-slate-50 p-5 shadow-[0_18px_40px_-30px_rgba(15,23,42,0.35)]"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-cyan-700">Insights</p>
          <h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">Weekly analytics</h2>
          <p className="mt-1 text-sm text-slate-500">
            Monday to Sunday: <span className="font-medium text-slate-700">{weekDates[0]}</span> to{" "}
            <span className="font-medium text-slate-700">{weekDates[6]}</span>
          </p>
        </div>

        <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-white/90 p-1 shadow-sm">
          <button
            type="button"
            onClick={() => setWeekOffset((current) => current - 1)}
            className="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-100"
          >
            &lt;-
          </button>
          <button
            type="button"
            onClick={() => setWeekOffset(0)}
            disabled={isCurrentWeek}
            className="rounded-full px-3 py-1.5 text-xs font-semibold text-slate-600 disabled:cursor-not-allowed disabled:opacity-50 hover:bg-slate-100"
          >
            This week
          </button>
          <button
            type="button"
            onClick={() => setWeekOffset((current) => Math.min(0, current + 1))}
            disabled={isCurrentWeek}
            className="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 transition disabled:cursor-not-allowed disabled:opacity-50 hover:bg-slate-100"
          >
            -&gt;
          </button>
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <article className="rounded-2xl border border-cyan-200 bg-cyan-50 p-3">
          <p className="text-[11px] uppercase tracking-wide text-cyan-700">Week total</p>
          <p className="mt-1 text-3xl font-bold text-slate-900">{totalDoneInWeek}</p>
          <p className="mt-1 text-xs text-slate-600">habit completions</p>
        </article>

        <article className="rounded-2xl border border-emerald-200 bg-emerald-50 p-3">
          <p className="text-[11px] uppercase tracking-wide text-emerald-700">Streak of days</p>
          <p className="mt-1 text-3xl font-bold text-slate-900">{streakOfDays}</p>
          <p className="mt-1 text-xs text-slate-600">consecutive active days</p>
        </article>

        <article className="rounded-2xl border border-indigo-200 bg-indigo-50 p-3">
          <p className="text-[11px] uppercase tracking-wide text-indigo-700">Habits completed</p>
          <p className="mt-1 text-3xl font-bold text-slate-900">{completedHabitsCount}</p>
          <p className="mt-1 text-xs text-slate-600">out of {totalHabits} habits</p>
        </article>

        <article className="rounded-2xl border border-amber-200 bg-amber-50 p-3">
          <p className="text-[11px] uppercase tracking-wide text-amber-700">Full completion days</p>
          <p className="mt-1 text-3xl font-bold text-slate-900">{fullCompletionDays}</p>
          <p className="mt-1 text-xs text-slate-600">all habits done</p>
        </article>
      </div>

      <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-4">
        <p className="text-sm font-semibold text-slate-800">Week breakdown (Mon-Sun)</p>
        <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-7">
          {weekDates.map((dateKey, index) => {
            const stat = statsByDate[dateKey];
            return (
              <article key={dateKey} className="rounded-xl border border-slate-200 bg-slate-50 p-2.5">
                <p className="text-xs font-semibold text-slate-700">
                  {weekdayLabels[index]} <span className="text-slate-400">{dateKey.slice(8)}</span>
                </p>
                <p className="mt-1 text-xs text-slate-600">Done: {stat.doneCount}</p>
                <p className="text-xs text-slate-600">Not done: {Math.max(0, totalHabits - stat.doneCount)}</p>
                <p className="text-xs text-slate-600">Completion: {stat.completionRate}%</p>
                <div className="mt-1.5 h-1.5 rounded-full bg-slate-200">
                  <div className="h-1.5 rounded-full bg-cyan-500" style={{ width: `${stat.completionRate}%` }} />
                </div>
              </article>
            );
          })}
        </div>
      </div>

      <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
        Habits not completed this week: <strong>{notCompletedHabitsCount}</strong>
      </div>

      <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-4">
        <p className="text-sm font-semibold text-slate-800">Totals by habit (Mon-Sun)</p>
        <p className="mt-0.5 text-xs text-slate-500">Risale -&gt; pages, KK -&gt; minutes</p>

        {sortedHabitTotals.length === 0 ? (
          <p className="mt-3 text-sm text-slate-500">No habits to analyze yet.</p>
        ) : (
          <div className="mt-3 grid gap-2">
            {sortedHabitTotals.map((item) => {
              const unitTotal = item.unit === "boolean" ? item.doneDays : item.progressTotal;
              const doneRate = elapsedWeekDays === 0 ? 0 : Math.round((item.doneDays / elapsedWeekDays) * 100);

              return (
                <article key={item.id} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-slate-800">{item.name}</p>
                    <span className="rounded-full border border-slate-300 bg-white px-2 py-0.5 text-[11px] text-slate-600">
                      {item.unit}
                    </span>
                  </div>
                  <div className="mt-1.5 grid gap-1 text-xs text-slate-600 sm:grid-cols-3">
                    <p>
                      Total: <strong>{formatValueByUnit(item.unit, unitTotal)}</strong>
                    </p>
                    <p>
                      Done days: <strong>{item.doneDays}/{elapsedWeekDays}</strong>
                    </p>
                    <p>
                      Not done days: <strong>{Math.max(0, elapsedWeekDays - item.doneDays)}</strong>
                    </p>
                  </div>
                  <div className="mt-2 h-1.5 rounded-full bg-slate-200">
                    <div className="h-1.5 rounded-full bg-emerald-500" style={{ width: `${doneRate}%` }} />
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
