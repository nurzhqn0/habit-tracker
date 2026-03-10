"use client";

import { useCallback, useEffect, useState } from "react";
import type { Habit, HabitLog, HabitUnit, NewHabitInput } from "../types/habit";
import { todayKey } from "../lib/habit-utils";

const HABITS_STORAGE_KEY = "habitflow_habits";

function createId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function toSafeNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  return null;
}

function toSafeDateKey(value: unknown, fallback: string): string {
  if (typeof value !== "string") {
    return fallback;
  }

  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return value;
  }

  return fallback;
}

function toSafeUnit(value: unknown): HabitUnit {
  if (value === "liters" || value === "pages" || value === "minutes" || value === "boolean") {
    return value;
  }

  return "boolean";
}

function normalizeLog(unit: HabitUnit, value: unknown): HabitLog | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const source = value as Record<string, unknown>;
  const done = Boolean(source.done);
  const rawProgress = toSafeNumber(source.progress);

  return {
    done,
    progress: unit === "boolean" ? null : rawProgress ?? 0,
    updatedAt: typeof source.updatedAt === "string" ? source.updatedAt : new Date().toISOString(),
  };
}

function migrateHabit(input: unknown, fallbackDate: string): Habit | null {
  if (!input || typeof input !== "object") {
    return null;
  }

  const source = input as Record<string, unknown>;
  const unit = toSafeUnit(source.unit);
  const id = typeof source.id === "string" ? source.id : createId();
  const name = typeof source.name === "string" ? source.name.trim() : "";
  if (!name) {
    return null;
  }

  const createdAt = typeof source.createdAt === "string" ? source.createdAt : new Date().toISOString();
  const target = unit === "boolean" ? null : Math.max(0, toSafeNumber(source.target) ?? 0);

  const logs: Record<string, HabitLog> = {};
  if (source.logs && typeof source.logs === "object") {
    for (const [key, value] of Object.entries(source.logs as Record<string, unknown>)) {
      const dateKey = toSafeDateKey(key, fallbackDate);
      const normalized = normalizeLog(unit, value);
      if (normalized) {
        if (unit !== "boolean" && (normalized.progress ?? 0) >= (target ?? 0) && (target ?? 0) > 0) {
          normalized.done = true;
        }
        logs[dateKey] = normalized;
      }
    }
  }

  if (Object.keys(logs).length === 0) {
    const legacyDate = toSafeDateKey(source.date, fallbackDate);
    const legacyDone = Boolean(source.done);
    const legacyProgress = toSafeNumber(source.progress);
    const normalizedLegacyProgress = unit === "boolean" ? null : legacyProgress ?? (legacyDone ? target ?? 0 : 0);
    const normalizedLegacyDone =
      unit === "boolean"
        ? legacyDone
        : legacyDone || ((normalizedLegacyProgress ?? 0) >= (target ?? 0) && (target ?? 0) > 0);

    logs[legacyDate] = {
      done: normalizedLegacyDone,
      progress: normalizedLegacyProgress,
      updatedAt: createdAt,
    };
  }

  const startDate = toSafeDateKey(source.startDate ?? source.date, fallbackDate);

  return {
    id,
    name,
    createdAt,
    startDate,
    unit,
    target,
    logs,
  };
}

export function useHabits() {
  const [habits, setHabits] = useState<Habit[]>([]);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const fallbackDate = todayKey();

    try {
      const raw = localStorage.getItem(HABITS_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as unknown;
        if (Array.isArray(parsed)) {
          const migrated = parsed
            .map((entry) => migrateHabit(entry, fallbackDate))
            .filter((entry): entry is Habit => Boolean(entry));
          setHabits(migrated);
        }
      }
    } catch {
      setHabits([]);
    } finally {
      setIsReady(true);
    }
  }, []);

  useEffect(() => {
    if (!isReady) {
      return;
    }

    localStorage.setItem(HABITS_STORAGE_KEY, JSON.stringify(habits));
  }, [habits, isReady]);

  const addHabit = useCallback((input: NewHabitInput) => {
    const startDate = toSafeDateKey(input.startDate, todayKey());
    const newHabit: Habit = {
      id: createId(),
      name: input.name.trim(),
      createdAt: new Date().toISOString(),
      startDate,
      unit: input.unit,
      target: input.unit === "boolean" ? null : input.target ?? 0,
      logs: {
        [startDate]: {
          done: false,
          progress: input.unit === "boolean" ? null : 0,
          updatedAt: new Date().toISOString(),
        },
      },
    };

    setHabits((prev) => [newHabit, ...prev]);
  }, []);

  const removeHabit = useCallback((habitId: string) => {
    setHabits((prev) => prev.filter((habit) => habit.id !== habitId));
  }, []);

  const toggleDone = useCallback((habitId: string, dateKey: string) => {
    setHabits((prev) =>
      prev.map((habit) => {
        if (habit.id !== habitId) {
          return habit;
        }

        const safeDateKey = toSafeDateKey(dateKey, todayKey());
        const currentLog = habit.logs[safeDateKey];
        const progress = currentLog?.progress ?? 0;
        const target = habit.target ?? 0;
        const progressSaysDone = habit.unit !== "boolean" && target > 0 && progress >= target;
        const currentDone = Boolean(currentLog?.done) || progressSaysDone;
        const nextDone = !currentDone;

        const nextProgress =
          habit.unit === "boolean"
            ? null
            : nextDone
              ? Math.max(progress, target)
              : 0;

        return {
          ...habit,
          logs: {
            ...habit.logs,
            [safeDateKey]: {
              done: nextDone,
              progress: nextProgress,
              updatedAt: new Date().toISOString(),
            },
          },
        };
      }),
    );
  }, []);

  const updateProgress = useCallback((habitId: string, dateKey: string, progress: number) => {
    setHabits((prev) =>
      prev.map((habit) => {
        if (habit.id !== habitId || habit.unit === "boolean") {
          return habit;
        }

        const safeDateKey = toSafeDateKey(dateKey, todayKey());
        const currentLog = habit.logs[safeDateKey];
        const safeProgress = Number.isFinite(progress) ? Math.max(0, progress) : 0;
        const target = habit.target ?? 0;
        const done = target > 0 ? safeProgress >= target : Boolean(currentLog?.done);

        return {
          ...habit,
          logs: {
            ...habit.logs,
            [safeDateKey]: {
              done,
              progress: safeProgress,
              updatedAt: new Date().toISOString(),
            },
          },
        };
      }),
    );
  }, []);

  return {
    habits,
    isReady,
    addHabit,
    removeHabit,
    toggleDone,
    updateProgress,
  };
}
