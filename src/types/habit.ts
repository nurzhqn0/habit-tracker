export type HabitUnit = "liters" | "pages" | "minutes" | "boolean";

export type HabitLog = {
  done: boolean;
  progress: number | null;
  updatedAt: string;
};

export type Habit = {
  id: string;
  name: string;
  createdAt: string;
  startDate: string;
  unit: HabitUnit;
  target: number | null;
  logs: Record<string, HabitLog>;
};

export type NewHabitInput = {
  name: string;
  startDate: string;
  unit: HabitUnit;
  target: number | null;
};
