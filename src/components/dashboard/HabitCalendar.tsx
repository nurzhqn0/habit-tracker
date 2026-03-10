"use client";

import { useEffect, useMemo, useState } from "react";
import { isHabitDoneOnDate, parseDateKey, todayKey, toDateKey } from "../../lib/habit-utils";
import type { Habit } from "../../types/habit";

type HabitCalendarProps = {
  habit: Habit;
  selectedDateKey: string;
  onSelectDate: (dateKey: string) => void;
};

type CalendarDay = {
  dateKey: string;
  dayNumber: number;
  done: boolean;
};

const weekdayLabels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function getMonthTitle(monthDate: Date): string {
  return monthDate.toLocaleDateString(undefined, { month: "long", year: "numeric" });
}

function buildMonthDays(monthDate: Date, habit: Habit): { leadingEmpty: number; days: CalendarDay[] } {
  const year = monthDate.getFullYear();
  const monthIndex = monthDate.getMonth();
  const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
  const firstDay = new Date(year, monthIndex, 1);
  const leadingEmpty = (firstDay.getDay() + 6) % 7;

  const days: CalendarDay[] = [];
  for (let day = 1; day <= daysInMonth; day += 1) {
    const dateKey = toDateKey(new Date(year, monthIndex, day));
    days.push({
      dateKey,
      dayNumber: day,
      done: isHabitDoneOnDate(habit, dateKey),
    });
  }

  return { leadingEmpty, days };
}

export default function HabitCalendar({ habit, selectedDateKey, onSelectDate }: HabitCalendarProps) {
  const initialDate = parseDateKey(selectedDateKey) ?? new Date();
  const [cursorDate, setCursorDate] = useState(() => new Date(initialDate.getFullYear(), initialDate.getMonth(), 1));

  useEffect(() => {
    const selectedDate = parseDateKey(selectedDateKey);
    if (!selectedDate) {
      return;
    }

    setCursorDate((current) => {
      if (current.getFullYear() === selectedDate.getFullYear() && current.getMonth() === selectedDate.getMonth()) {
        return current;
      }

      return new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1);
    });
  }, [selectedDateKey]);

  const monthData = useMemo(() => buildMonthDays(cursorDate, habit), [cursorDate, habit]);

  const goPrevMonth = () => {
    setCursorDate((current) => new Date(current.getFullYear(), current.getMonth() - 1, 1));
  };

  const goNextMonth = () => {
    setCursorDate((current) => new Date(current.getFullYear(), current.getMonth() + 1, 1));
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white/80 p-3">
      <div className="mb-3 flex items-center justify-between">
        <button
          type="button"
          onClick={goPrevMonth}
          className="rounded-md border border-slate-200 px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100"
        >
          Prev
        </button>
        <p className="text-sm font-semibold text-slate-800">{getMonthTitle(cursorDate)}</p>
        <button
          type="button"
          onClick={goNextMonth}
          className="rounded-md border border-slate-200 px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100"
        >
          Next
        </button>
      </div>

      <div className="grid grid-cols-7 gap-1">
        {weekdayLabels.map((label) => (
          <span key={label} className="pb-1 text-center text-[10px] font-semibold uppercase tracking-wide text-slate-400">
            {label}
          </span>
        ))}

        {Array.from({ length: monthData.leadingEmpty }).map((_, index) => (
          <span key={`empty-${index}`} />
        ))}

        {monthData.days.map((day) => {
          const isSelected = day.dateKey === selectedDateKey;
          return (
            <button
              key={day.dateKey}
              type="button"
              onClick={() => onSelectDate(day.dateKey)}
              className={`aspect-square rounded-md text-xs font-medium transition ${
                isSelected
                  ? "ring-2 ring-cyan-500"
                  : day.done
                    ? "bg-emerald-500 text-white hover:bg-emerald-600"
                    : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
              title={day.done ? "Completed day" : "Not completed day"}
            >
              {day.dayNumber}
            </button>
          );
        })}
      </div>

      <div className="mt-3 flex items-center gap-3 text-[11px] text-slate-500">
        <span className="inline-flex items-center gap-1">
          <span className="inline-block h-2.5 w-2.5 rounded bg-emerald-500" />
          Done
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="inline-block h-2.5 w-2.5 rounded bg-slate-300" />
          Not done
        </span>
        <button
          type="button"
          onClick={() => {
            const today = todayKey();
            onSelectDate(today);
            const todayDate = parseDateKey(today);
            if (todayDate) {
              setCursorDate(new Date(todayDate.getFullYear(), todayDate.getMonth(), 1));
            }
          }}
          className="ml-auto rounded border border-slate-200 px-2 py-0.5 text-[10px] font-semibold text-slate-600 hover:bg-slate-100"
        >
          Jump to today
        </button>
      </div>
    </div>
  );
}
