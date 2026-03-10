import type { Habit, HabitLog } from "../types/habit";

const DAY_MS = 24 * 60 * 60 * 1000;

export function toDateKey(date: Date): string {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return local.toISOString().split("T")[0];
}

export function todayKey(): string {
  return toDateKey(new Date());
}

export function parseDateKey(key: string): Date | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(key)) {
    return null;
  }

  const [year, month, day] = key.split("-").map(Number);
  if (!year || !month || !day) {
    return null;
  }

  return new Date(year, month - 1, day);
}

export function shiftDateKey(key: string, days: number): string {
  const baseDate = parseDateKey(key) ?? new Date();
  baseDate.setDate(baseDate.getDate() + days);
  return toDateKey(baseDate);
}

export function formatDateReadable(key: string): string {
  const date = parseDateKey(key);
  return date ? date.toLocaleDateString() : key;
}

export function formatTimestamp(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export function getLogForDate(logs: Record<string, HabitLog>, dateKey: string, isBoolean: boolean): HabitLog {
  const existing = logs[dateKey];
  if (existing) {
    return existing;
  }

  return {
    done: false,
    progress: isBoolean ? null : 0,
    updatedAt: "",
  };
}

export function isHabitDoneOnDate(habit: Habit, dateKey: string): boolean {
  const log = habit.logs[dateKey];
  if (!log) {
    return false;
  }

  if (log.done) {
    return true;
  }

  if (habit.unit === "boolean") {
    return false;
  }

  const target = habit.target ?? 0;
  return target > 0 && (log.progress ?? 0) >= target;
}

export function getCurrentStreak(habit: Habit, endDateKey: string = todayKey()): number {
  let cursor = endDateKey;
  let streak = 0;

  while (isHabitDoneOnDate(habit, cursor)) {
    streak += 1;
    cursor = shiftDateKey(cursor, -1);
  }

  return streak;
}

export function getBestStreak(habit: Habit): number {
  const doneDays = Object.entries(habit.logs)
    .filter(([dateKey]) => isHabitDoneOnDate(habit, dateKey))
    .map(([key]) => key)
    .sort();

  if (doneDays.length === 0) {
    return 0;
  }

  let best = 1;
  let current = 1;

  for (let index = 1; index < doneDays.length; index += 1) {
    const previous = parseDateKey(doneDays[index - 1]);
    const currentDate = parseDateKey(doneDays[index]);
    if (!previous || !currentDate) {
      continue;
    }

    const diff = Math.round((currentDate.getTime() - previous.getTime()) / DAY_MS);
    if (diff === 1) {
      current += 1;
      best = Math.max(best, current);
    } else {
      current = 1;
    }
  }

  return best;
}

export function getLastNDates(days: number, endDateKey: string = todayKey()): string[] {
  const keys: string[] = [];
  for (let offset = days - 1; offset >= 0; offset -= 1) {
    keys.push(shiftDateKey(endDateKey, -offset));
  }

  return keys;
}
