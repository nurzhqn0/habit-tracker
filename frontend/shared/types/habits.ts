export const UNKNOWN = -1;
export const NO = 0;
export const YES_AUTO = 1;
export const YES_MANUAL = 2;
export const SKIP = 3;

export interface Habit {
  id: number;
  uuid: string;
  name: string;
  question: string;
  description: string;
  type: 0 | 1; // 0=yes/no, 1=numerical
  color: number;
  position: number;
  freq_num: number;
  freq_den: number;
  reminder_hour: number | null;
  reminder_min: number | null;
  reminder_days: number;
  target_type: 0 | 1; // 0=at least, 1=at most
  target_value: number;
  unit: string;
  created_at: string;
}

export interface HabitOverviewItem {
  habit: Habit;
  score: number;
  streak: number;
  entries: Record<string, number>;
  notes: Record<string, string>;
}

export interface EntryChange {
  value: number;
  score: number;
  streak: number;
  entries: Record<string, number>;
}

export interface HabitForm {
  name: string;
  question: string;
  description: string;
  type: 0 | 1;
  color: number;
  freq_num: number;
  freq_den: number;
  reminder_hour: number | null;
  reminder_min: number | null;
  reminder_days: number;
  target_type: 0 | 1;
  target_value: number;
  unit: string;
}
